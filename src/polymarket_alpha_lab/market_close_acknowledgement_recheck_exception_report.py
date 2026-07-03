"""Pure in-memory market close acknowledgement recheck exception report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS as _UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_EXCEPTION_CONFIG_VERSION = (
    "market-close-acknowledgement-recheck-exception-v0"
)

_EMPTY_REASON = "market_close_ack_recheck_exception_report_empty"
_CLEAR_REASON = "market_close_ack_recheck_clear"
_MISSING_CLOSE_EVIDENCE_REASON = "market_close_ack_recheck_missing_close_evidence"
_MISSING_ACKNOWLEDGEMENT_REASON = "market_close_ack_recheck_missing_acknowledgement"
_STALE_RECHECK_REASON = "market_close_ack_recheck_stale_recheck"
_STALE_CLOSE_EVIDENCE_REASON = "market_close_ack_recheck_stale_close_evidence"
_NON_ACKNOWLEDGED_OUTCOME_SOURCE_REASON = (
    "market_close_ack_recheck_outcome_source_not_acknowledgement"
)

_CRITICAL_REASONS = (
    _MISSING_CLOSE_EVIDENCE_REASON,
    _MISSING_ACKNOWLEDGEMENT_REASON,
)
_ROW_REASON_CODES = (
    _MISSING_CLOSE_EVIDENCE_REASON,
    _MISSING_ACKNOWLEDGEMENT_REASON,
    _STALE_RECHECK_REASON,
    _STALE_CLOSE_EVIDENCE_REASON,
    _NON_ACKNOWLEDGED_OUTCOME_SOURCE_REASON,
    _CLEAR_REASON,
)
_REPORT_REASON_CODES = (_EMPTY_REASON, *_ROW_REASON_CODES)
_SEVERITIES = ("critical", "watch", "clear")
_REPORT_STATUSES = ("empty", *_SEVERITIES)
_OUTCOME_SOURCES = ("acknowledgement", "resolver", "manual", "unknown")
_SEVERITY_RANK = {"critical": 0, "watch": 1, "clear": 2}
_REASON_RANK = {
    reason_code: index for index, reason_code in enumerate(_ROW_REASON_CODES)
}
_UNSAFE_PUBLIC_STRING_FRAGMENTS = frozenset(
    (
        *_UNSAFE_SURFACE_FIELD_FRAGMENTS,
        "api_key",
        "password",
        "secret",
        "token",
    ),
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckExceptionConfig:
    config_version: str = (
        DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_EXCEPTION_CONFIG_VERSION
    )
    max_recheck_age_seconds: Decimal = Decimal("3600.000000")
    max_close_evidence_age_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "max_recheck_age_seconds",
            _require_positive_decimal(
                "max_recheck_age_seconds",
                self.max_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_close_evidence_age_seconds",
            _require_positive_decimal(
                "max_close_evidence_age_seconds",
                self.max_close_evidence_age_seconds,
            ),
        )
        require_paper_only_flags(
            "MarketCloseAcknowledgementRecheckExceptionConfig "
            "paper_only/report_only/readonly",
            self,
        )


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckExceptionInputRow:
    market_id: str
    team_id: str
    category_id: str
    market_closed_at: datetime
    close_evidence_observed_at: datetime | None = None
    acknowledgement_observed_at: datetime | None = None
    rechecked_at: datetime | None = None
    outcome_source: str = "acknowledgement"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_id",
            _require_public_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "category_id",
            _require_public_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        for field_name in (
            "close_evidence_observed_at",
            "acknowledgement_observed_at",
            "rechecked_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        _require_member("outcome_source", self.outcome_source, _OUTCOME_SOURCES)
        require_paper_only_flags(
            "market close acknowledgement recheck exception input row",
            self,
        )


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckExceptionRow:
    market_id: str
    team_id: str
    category_id: str
    market_closed_at: datetime
    close_evidence_observed_at: datetime | None
    acknowledgement_observed_at: datetime | None
    rechecked_at: datetime | None
    outcome_source: str
    outcome_source_acknowledged: bool
    market_close_age_seconds: Decimal
    close_evidence_age_seconds: Decimal | None
    acknowledgement_age_seconds: Decimal | None
    recheck_age_seconds: Decimal | None
    max_recheck_age_seconds: Decimal
    max_close_evidence_age_seconds: Decimal
    severity: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "team_id", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        for field_name in (
            "close_evidence_observed_at",
            "acknowledgement_observed_at",
            "rechecked_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        _require_member("outcome_source", self.outcome_source, _OUTCOME_SOURCES)
        if type(self.outcome_source_acknowledged) is not bool:
            raise ValueError("outcome_source_acknowledged must be a bool")
        for field_name in (
            "market_close_age_seconds",
            "max_recheck_age_seconds",
            "max_close_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "close_evidence_age_seconds",
            "acknowledgement_age_seconds",
            "recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_member("severity", self.severity, _SEVERITIES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allowed=_ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags(
            "market close acknowledgement recheck exception row",
            self,
        )


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckExceptionRollupRow:
    team_id: str
    category_id: str
    severity: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    critical_count: Decimal
    exception_count: Decimal
    exception_ratio: Decimal
    missing_close_evidence_count: Decimal
    missing_acknowledgement_count: Decimal
    stale_recheck_count: Decimal
    stale_close_evidence_count: Decimal
    non_acknowledged_outcome_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "category_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        _require_member("severity", self.severity, _SEVERITIES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allowed=_REPORT_REASON_CODES),
        )
        for field_name in (
            "market_count",
            "clear_count",
            "watch_count",
            "critical_count",
            "exception_count",
            "missing_close_evidence_count",
            "missing_acknowledgement_count",
            "stale_recheck_count",
            "stale_close_evidence_count",
            "non_acknowledged_outcome_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exception_ratio",
            _require_ratio_decimal("exception_ratio", self.exception_ratio),
        )
        _validate_rollup(self)
        require_paper_only_flags(
            "market close acknowledgement recheck exception rollup row",
            self,
        )


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckExceptionReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    critical_count: Decimal
    exception_count: Decimal
    exception_ratio: Decimal
    missing_close_evidence_count: Decimal
    missing_acknowledgement_count: Decimal
    stale_recheck_count: Decimal
    stale_close_evidence_count: Decimal
    non_acknowledged_outcome_source_count: Decimal
    max_recheck_age_seconds: Decimal
    max_close_evidence_age_seconds: Decimal
    max_recheck_age_seconds_observed: Decimal
    max_close_evidence_age_seconds_observed: Decimal
    rows: tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...]
    team_category_rollups: tuple[
        MarketCloseAcknowledgementRecheckExceptionRollupRow,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allowed=_REPORT_REASON_CODES),
        )
        for field_name in (
            "market_count",
            "clear_count",
            "watch_count",
            "critical_count",
            "exception_count",
            "missing_close_evidence_count",
            "missing_acknowledgement_count",
            "stale_recheck_count",
            "stale_close_evidence_count",
            "non_acknowledged_outcome_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exception_ratio",
            _require_ratio_decimal("exception_ratio", self.exception_ratio),
        )
        for field_name in (
            "max_recheck_age_seconds",
            "max_close_evidence_age_seconds",
            "max_recheck_age_seconds_observed",
            "max_close_evidence_age_seconds_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "team_category_rollups",
            _normalize_rollups(self.team_category_rollups),
        )
        _validate_report(self)
        require_paper_only_flags(
            "market close acknowledgement recheck exception report",
            self,
        )
        reject_unsafe_surface_fields(
            "market close acknowledgement recheck exception report",
            self,
        )


def build_market_close_acknowledgement_recheck_exception_report(
    input_rows: list[MarketCloseAcknowledgementRecheckExceptionInputRow]
    | tuple[MarketCloseAcknowledgementRecheckExceptionInputRow, ...],
    *,
    config: MarketCloseAcknowledgementRecheckExceptionConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckExceptionReport:
    if type(config) is not MarketCloseAcknowledgementRecheckExceptionConfig:
        raise ValueError(
            "config must be a MarketCloseAcknowledgementRecheckExceptionConfig",
        )
    require_paper_only_flags(
        "market close acknowledgement recheck exception config",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    input_row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for input_row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    rollups = _team_category_rollups(rows)

    return MarketCloseAcknowledgementRecheckExceptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        market_count=_decimal_count(len(rows)),
        clear_count=_severity_count(rows, "clear"),
        watch_count=_severity_count(rows, "watch"),
        critical_count=_severity_count(rows, "critical"),
        exception_count=_decimal_count(sum(1 for row in rows if row.severity != "clear")),
        exception_ratio=_ratio(
            _decimal_count(sum(1 for row in rows if row.severity != "clear")),
            _decimal_count(len(rows)),
        ),
        missing_close_evidence_count=_reason_count(
            rows,
            _MISSING_CLOSE_EVIDENCE_REASON,
        ),
        missing_acknowledgement_count=_reason_count(
            rows,
            _MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        stale_recheck_count=_reason_count(rows, _STALE_RECHECK_REASON),
        stale_close_evidence_count=_reason_count(rows, _STALE_CLOSE_EVIDENCE_REASON),
        non_acknowledged_outcome_source_count=_reason_count(
            rows,
            _NON_ACKNOWLEDGED_OUTCOME_SOURCE_REASON,
        ),
        max_recheck_age_seconds=config.max_recheck_age_seconds,
        max_close_evidence_age_seconds=config.max_close_evidence_age_seconds,
        max_recheck_age_seconds_observed=_max_decimal(
            tuple(row.recheck_age_seconds for row in rows),
        ),
        max_close_evidence_age_seconds_observed=_max_decimal(
            tuple(row.close_evidence_age_seconds for row in rows),
        ),
        rows=rows,
        team_category_rollups=rollups,
    )


def market_close_acknowledgement_recheck_exception_report_payload(
    report: MarketCloseAcknowledgementRecheckExceptionReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckExceptionReport:
        raise ValueError(
            "report must be a MarketCloseAcknowledgementRecheckExceptionReport",
        )
    require_paper_only_flags(
        "market close acknowledgement recheck exception report",
        report,
    )
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields(
        "market close acknowledgement recheck exception report",
        ready,
    )
    return ready


def _normalize_input_rows(
    input_rows: object,
    *,
    generated_at: datetime,
) -> tuple[MarketCloseAcknowledgementRecheckExceptionInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    rows = tuple(input_rows)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckExceptionInputRow:
            raise ValueError(
                "input_rows must contain "
                "MarketCloseAcknowledgementRecheckExceptionInputRow",
            )
        require_paper_only_flags(
            "market close acknowledgement recheck exception input row",
            row,
        )
        _validate_input_times_against_generated_at(row, generated_at=generated_at)
        if row.market_id in seen_market_ids:
            raise ValueError("input_rows must be unique by market_id")
        seen_market_ids.add(row.market_id)
    return tuple(sorted(rows, key=lambda row: (row.market_id, row.team_id, row.category_id)))


def _row_from_input(
    input_row: MarketCloseAcknowledgementRecheckExceptionInputRow,
    *,
    config: MarketCloseAcknowledgementRecheckExceptionConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckExceptionRow:
    market_close_age_seconds = _age_seconds(
        generated_at,
        input_row.market_closed_at,
        earlier_field_name="market_closed_at",
    )
    close_evidence_age_seconds = (
        None
        if input_row.close_evidence_observed_at is None
        else _age_seconds(
            generated_at,
            input_row.close_evidence_observed_at,
            earlier_field_name="close_evidence_observed_at",
        )
    )
    acknowledgement_age_seconds = (
        None
        if input_row.acknowledgement_observed_at is None
        else _age_seconds(
            generated_at,
            input_row.acknowledgement_observed_at,
            earlier_field_name="acknowledgement_observed_at",
        )
    )
    recheck_age_seconds = (
        None
        if input_row.rechecked_at is None
        else _age_seconds(
            generated_at,
            input_row.rechecked_at,
            earlier_field_name="rechecked_at",
        )
    )
    reason_codes = _input_reason_codes(
        input_row,
        close_evidence_age_seconds=close_evidence_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        max_close_evidence_age_seconds=config.max_close_evidence_age_seconds,
        max_recheck_age_seconds=config.max_recheck_age_seconds,
    )

    return MarketCloseAcknowledgementRecheckExceptionRow(
        market_id=input_row.market_id,
        team_id=input_row.team_id,
        category_id=input_row.category_id,
        market_closed_at=input_row.market_closed_at,
        close_evidence_observed_at=input_row.close_evidence_observed_at,
        acknowledgement_observed_at=input_row.acknowledgement_observed_at,
        rechecked_at=input_row.rechecked_at,
        outcome_source=input_row.outcome_source,
        outcome_source_acknowledged=input_row.outcome_source == "acknowledgement",
        market_close_age_seconds=market_close_age_seconds,
        close_evidence_age_seconds=close_evidence_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        max_recheck_age_seconds=config.max_recheck_age_seconds,
        max_close_evidence_age_seconds=config.max_close_evidence_age_seconds,
        severity=_row_severity(reason_codes),
        reason_codes=reason_codes,
    )


def _input_reason_codes(
    input_row: MarketCloseAcknowledgementRecheckExceptionInputRow,
    *,
    close_evidence_age_seconds: Decimal | None,
    recheck_age_seconds: Decimal | None,
    max_close_evidence_age_seconds: Decimal,
    max_recheck_age_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if input_row.close_evidence_observed_at is None:
        reasons.add(_MISSING_CLOSE_EVIDENCE_REASON)
    elif close_evidence_age_seconds is not None:
        if close_evidence_age_seconds > max_close_evidence_age_seconds:
            reasons.add(_STALE_CLOSE_EVIDENCE_REASON)
    if input_row.acknowledgement_observed_at is None:
        reasons.add(_MISSING_ACKNOWLEDGEMENT_REASON)
    if input_row.rechecked_at is None:
        reasons.add(_STALE_RECHECK_REASON)
    elif recheck_age_seconds is not None:
        if recheck_age_seconds > max_recheck_age_seconds:
            reasons.add(_STALE_RECHECK_REASON)
    if input_row.outcome_source != "acknowledgement":
        reasons.add(_NON_ACKNOWLEDGED_OUTCOME_SOURCE_REASON)
    if not reasons:
        reasons.add(_CLEAR_REASON)
    return tuple(reason_code for reason_code in _ROW_REASON_CODES if reason_code in reasons)


def _team_category_rollups(
    rows: tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...],
) -> tuple[MarketCloseAcknowledgementRecheckExceptionRollupRow, ...]:
    keys = tuple(sorted({(row.team_id, row.category_id) for row in rows}))
    rollups = tuple(
        _rollup_from_rows(
            team_id=team_id,
            category_id=category_id,
            rows=tuple(
                row
                for row in rows
                if row.team_id == team_id and row.category_id == category_id
            ),
        )
        for team_id, category_id in keys
    )
    return tuple(sorted(rollups, key=_rollup_sort_key))


def _rollup_from_rows(
    *,
    team_id: str,
    category_id: str,
    rows: tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...],
) -> MarketCloseAcknowledgementRecheckExceptionRollupRow:
    exception_count = _decimal_count(sum(1 for row in rows if row.severity != "clear"))
    return MarketCloseAcknowledgementRecheckExceptionRollupRow(
        team_id=team_id,
        category_id=category_id,
        severity=_report_status(rows) if rows else "clear",
        reason_codes=_report_reason_codes(rows),
        market_count=_decimal_count(len(rows)),
        clear_count=_severity_count(rows, "clear"),
        watch_count=_severity_count(rows, "watch"),
        critical_count=_severity_count(rows, "critical"),
        exception_count=exception_count,
        exception_ratio=_ratio(exception_count, _decimal_count(len(rows))),
        missing_close_evidence_count=_reason_count(rows, _MISSING_CLOSE_EVIDENCE_REASON),
        missing_acknowledgement_count=_reason_count(
            rows,
            _MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        stale_recheck_count=_reason_count(rows, _STALE_RECHECK_REASON),
        stale_close_evidence_count=_reason_count(rows, _STALE_CLOSE_EVIDENCE_REASON),
        non_acknowledged_outcome_source_count=_reason_count(
            rows,
            _NON_ACKNOWLEDGED_OUTCOME_SOURCE_REASON,
        ),
    )


def _validate_input_times_against_generated_at(
    row: MarketCloseAcknowledgementRecheckExceptionInputRow,
    *,
    generated_at: datetime,
) -> None:
    _age_seconds(generated_at, row.market_closed_at, earlier_field_name="market_closed_at")
    if row.close_evidence_observed_at is not None:
        _age_seconds(
            generated_at,
            row.close_evidence_observed_at,
            earlier_field_name="close_evidence_observed_at",
        )
    if row.acknowledgement_observed_at is not None:
        _age_seconds(
            generated_at,
            row.acknowledgement_observed_at,
            earlier_field_name="acknowledgement_observed_at",
        )
    if row.rechecked_at is not None:
        _age_seconds(generated_at, row.rechecked_at, earlier_field_name="rechecked_at")


def _validate_row(row: MarketCloseAcknowledgementRecheckExceptionRow) -> None:
    if row.close_evidence_observed_at is None:
        if row.close_evidence_age_seconds is not None:
            raise ValueError("close_evidence_age_seconds requires close evidence")
    elif row.close_evidence_age_seconds is None:
        raise ValueError("close_evidence_age_seconds is required with close evidence")
    if row.acknowledgement_observed_at is None:
        if row.acknowledgement_age_seconds is not None:
            raise ValueError("acknowledgement_age_seconds requires acknowledgement")
    elif row.acknowledgement_age_seconds is None:
        raise ValueError("acknowledgement_age_seconds is required with acknowledgement")
    if row.rechecked_at is None:
        if row.recheck_age_seconds is not None:
            raise ValueError("recheck_age_seconds requires rechecked_at")
    elif row.recheck_age_seconds is None:
        raise ValueError("recheck_age_seconds is required with rechecked_at")
    if row.outcome_source_acknowledged != (row.outcome_source == "acknowledgement"):
        raise ValueError("outcome_source_acknowledged must match outcome_source")
    expected_reasons = _expected_reason_codes_from_row(row)
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row state")
    if row.severity != _row_severity(row.reason_codes):
        raise ValueError("severity must match reason_codes")


def _expected_reason_codes_from_row(
    row: MarketCloseAcknowledgementRecheckExceptionRow,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if row.close_evidence_observed_at is None:
        reasons.add(_MISSING_CLOSE_EVIDENCE_REASON)
    elif (
        row.close_evidence_age_seconds is not None
        and row.close_evidence_age_seconds > row.max_close_evidence_age_seconds
    ):
        reasons.add(_STALE_CLOSE_EVIDENCE_REASON)
    if row.acknowledgement_observed_at is None:
        reasons.add(_MISSING_ACKNOWLEDGEMENT_REASON)
    if row.rechecked_at is None:
        reasons.add(_STALE_RECHECK_REASON)
    elif (
        row.recheck_age_seconds is not None
        and row.recheck_age_seconds > row.max_recheck_age_seconds
    ):
        reasons.add(_STALE_RECHECK_REASON)
    if row.outcome_source != "acknowledgement":
        reasons.add(_NON_ACKNOWLEDGED_OUTCOME_SOURCE_REASON)
    if not reasons:
        reasons.add(_CLEAR_REASON)
    return tuple(reason_code for reason_code in _ROW_REASON_CODES if reason_code in reasons)


def _validate_rollup(row: MarketCloseAcknowledgementRecheckExceptionRollupRow) -> None:
    if row.clear_count + row.watch_count + row.critical_count != row.market_count:
        raise ValueError("rollup severity counts must equal market_count")
    if row.exception_count != row.watch_count + row.critical_count:
        raise ValueError("rollup exception_count must equal watch plus critical")
    if row.exception_ratio != _ratio(row.exception_count, row.market_count):
        raise ValueError("rollup exception_ratio must match counts")
    if row.severity != _rollup_status(row):
        raise ValueError("rollup severity must match counts")


def _validate_report(report: MarketCloseAcknowledgementRecheckExceptionReport) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must equal rows length")
    if report.clear_count != _severity_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.watch_count != _severity_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.critical_count != _severity_count(report.rows, "critical"):
        raise ValueError("critical_count must match rows")
    if report.exception_count != report.watch_count + report.critical_count:
        raise ValueError("exception_count must equal watch plus critical")
    if report.exception_ratio != _ratio(report.exception_count, report.market_count):
        raise ValueError("exception_ratio must match counts")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for field_name, reason_code in (
        ("missing_close_evidence_count", _MISSING_CLOSE_EVIDENCE_REASON),
        ("missing_acknowledgement_count", _MISSING_ACKNOWLEDGEMENT_REASON),
        ("stale_recheck_count", _STALE_RECHECK_REASON),
        ("stale_close_evidence_count", _STALE_CLOSE_EVIDENCE_REASON),
        (
            "non_acknowledged_outcome_source_count",
            _NON_ACKNOWLEDGED_OUTCOME_SOURCE_REASON,
        ),
    ):
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_recheck_age_seconds_observed != _max_decimal(
        tuple(row.recheck_age_seconds for row in report.rows),
    ):
        raise ValueError("max_recheck_age_seconds_observed must match rows")
    if report.max_close_evidence_age_seconds_observed != _max_decimal(
        tuple(row.close_evidence_age_seconds for row in report.rows),
    ):
        raise ValueError("max_close_evidence_age_seconds_observed must match rows")
    if report.team_category_rollups != _team_category_rollups(report.rows):
        raise ValueError("team_category_rollups must match rows")


def _row_severity(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _CRITICAL_REASONS for reason_code in reason_codes):
        return "critical"
    if reason_codes == (_CLEAR_REASON,):
        return "clear"
    return "watch"


def _report_status(
    rows: tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.severity == "critical" for row in rows):
        return "critical"
    if any(row.severity == "watch" for row in rows):
        return "watch"
    return "clear"


def _rollup_status(row: MarketCloseAcknowledgementRecheckExceptionRollupRow) -> str:
    if row.critical_count > _ZERO:
        return "critical"
    if row.watch_count > _ZERO:
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != _CLEAR_REASON
    }
    if not reasons:
        return (_CLEAR_REASON,)
    return tuple(reason_code for reason_code in _ROW_REASON_CODES if reason_code in reasons)


def _severity_count(
    rows: tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...],
    severity: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.severity == severity))


def _reason_count(
    rows: tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _row_sort_key(
    row: MarketCloseAcknowledgementRecheckExceptionRow,
) -> tuple[int, int, str, str, str]:
    return (
        _SEVERITY_RANK[row.severity],
        -len(row.reason_codes),
        row.market_id,
        row.team_id,
        row.category_id,
    )


def _rollup_sort_key(
    row: MarketCloseAcknowledgementRecheckExceptionRollupRow,
) -> tuple[int, Decimal, str, str]:
    return (
        _SEVERITY_RANK[row.severity],
        -row.exception_ratio,
        row.team_id,
        row.category_id,
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketCloseAcknowledgementRecheckExceptionRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketCloseAcknowledgementRecheckExceptionRow:
            raise ValueError(
                "rows must contain MarketCloseAcknowledgementRecheckExceptionRow",
            )
        require_paper_only_flags(
            "market close acknowledgement recheck exception row",
            row,
        )
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_rollups(
    rows: object,
) -> tuple[MarketCloseAcknowledgementRecheckExceptionRollupRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("team_category_rollups must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketCloseAcknowledgementRecheckExceptionRollupRow:
            raise ValueError(
                "team_category_rollups must contain "
                "MarketCloseAcknowledgementRecheckExceptionRollupRow",
            )
        require_paper_only_flags(
            "market close acknowledgement recheck exception rollup row",
            row,
        )
    return tuple(sorted(normalized, key=_rollup_sort_key))


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    public_value = _require_canonical_string(field_name, value)
    normalized_value = public_value.lower()
    if any(fragment in normalized_value for fragment in _UNSAFE_PUBLIC_STRING_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return public_value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    reason_codes: object,
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, allowed)
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    return tuple(reason_code for reason_code in allowed if reason_code in normalized)


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


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized_value = _quantize(decimal_value)
    if normalized_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive at 0.000001 precision")
    return normalized_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return _quantize(decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize(decimal_value)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _age_seconds(
    generated_at: datetime,
    earlier: datetime,
    *,
    earlier_field_name: str,
) -> Decimal:
    if earlier > generated_at:
        if earlier_field_name == "market_closed_at":
            raise ValueError("market_closed_at cannot be after generated_at")
        raise ValueError(f"generated_at cannot be before {earlier_field_name}")
    return _elapsed_seconds(earlier, generated_at)


def _elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(_DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
        return _quantize(seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _max_decimal(values: tuple[Decimal | None, ...]) -> Decimal:
    present_values = tuple(value for value in values if value is not None)
    if not present_values:
        return _ZERO
    return _quantize(max(present_values))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


__all__ = (
    "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_EXCEPTION_CONFIG_VERSION",
    "MarketCloseAcknowledgementRecheckExceptionConfig",
    "MarketCloseAcknowledgementRecheckExceptionInputRow",
    "MarketCloseAcknowledgementRecheckExceptionReport",
    "MarketCloseAcknowledgementRecheckExceptionRollupRow",
    "MarketCloseAcknowledgementRecheckExceptionRow",
    "build_market_close_acknowledgement_recheck_exception_report",
    "market_close_acknowledgement_recheck_exception_report_payload",
)
