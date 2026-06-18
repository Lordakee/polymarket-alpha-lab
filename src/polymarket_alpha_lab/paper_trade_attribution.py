"""Paper-only attribution reducer over typed paper-trade records.

Pure arithmetic over already-typed journal and outcome-tracking report values.
This module is local/report-only and side-effect free.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport


ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperTradeAttributionConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperTradeAttributionRow:
    market_slug: str
    side: str
    status: str
    trade_count: int
    filled_count: int
    complete_fill_count: int
    partial_fill_count: int
    resolved_count: int | None
    pending_count: int | None
    realized_win_count: int | None
    realized_loss_count: int | None
    total_requested_size: Decimal
    total_filled_size: Decimal
    total_unfilled_size: Decimal
    total_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("side", self.side)
        _require_canonical_string("status", self.status)
        for field_name in (
            "trade_count",
            "filled_count",
            "complete_fill_count",
            "partial_fill_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "resolved_count",
            "pending_count",
            "realized_win_count",
            "realized_loss_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_requested_size",
            "total_filled_size",
            "total_unfilled_size",
            "total_notional",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


@dataclass(frozen=True)
class PaperTradeAttributionReport:
    generated_at: datetime
    config_version: str
    trade_count: int
    row_count: int
    market_count: int
    filled_count: int
    complete_fill_count: int
    partial_fill_count: int
    resolved_count: int | None
    pending_count: int | None
    realized_win_count: int | None
    realized_loss_count: int | None
    total_requested_size: Decimal
    total_filled_size: Decimal
    total_unfilled_size: Decimal
    total_notional: Decimal
    first_trade_decision_at: datetime | None
    latest_trade_decision_at: datetime | None
    rows: tuple[PaperTradeAttributionRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "trade_count",
            "row_count",
            "market_count",
            "filled_count",
            "complete_fill_count",
            "partial_fill_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "resolved_count",
            "pending_count",
            "realized_win_count",
            "realized_loss_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "total_requested_size",
            "total_filled_size",
            "total_unfilled_size",
            "total_notional",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_trade_decision_at",
            _as_optional_utc(self.first_trade_decision_at),
        )
        object.__setattr__(
            self,
            "latest_trade_decision_at",
            _as_optional_utc(self.latest_trade_decision_at),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_trade_attribution_report(
    trade_records: Iterable[PaperTradeRecord],
    *,
    config: PaperTradeAttributionConfig,
    generated_at: datetime,
    outcome_report: OutcomeTrackingReport | None = None,
) -> PaperTradeAttributionReport:
    if type(config) is not PaperTradeAttributionConfig:
        raise ValueError("config must be a PaperTradeAttributionConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if outcome_report is not None and type(outcome_report) is not OutcomeTrackingReport:
        raise ValueError("outcome_report must be an OutcomeTrackingReport or None")
    if outcome_report is not None:
        if outcome_report.paper_only is not True:
            raise ValueError("outcome_report must be paper_only")
        if outcome_report.report_only is not True:
            raise ValueError("outcome_report must be report_only")
        if outcome_report.readonly is not True:
            raise ValueError("outcome_report must be readonly")

    trades = _normalize_trade_records(trade_records)
    outcomes_by_packet_id = _outcomes_by_packet_id(outcome_report)
    groups: dict[tuple[str, str, str], _GroupAccumulator] = {}
    for trade in trades:
        key = (trade.market_slug, _side_for_trade(trade), trade.fill_status)
        accumulator = groups.setdefault(
            key,
            _GroupAccumulator(
                market_slug=key[0],
                side=key[1],
                status=key[2],
            ),
        )
        accumulator.add_trade(
            trade,
            outcome=_lookup_outcome(trade, outcomes_by_packet_id, outcome_report),
        )

    rows = tuple(
        sorted(
            (accumulator.to_row() for accumulator in groups.values()),
            key=lambda row: (-row.trade_count, row.market_slug, row.side, row.status),
        ),
    )
    decisions = tuple(_as_utc(trade.decision_timestamp_utc) for trade in trades)
    has_outcomes = outcome_report is not None

    return PaperTradeAttributionReport(
        generated_at=_as_utc(generated_at),
        config_version=config.config_version,
        trade_count=len(trades),
        row_count=len(rows),
        market_count=len({trade.market_slug for trade in trades}),
        filled_count=sum(1 for trade in trades if trade.fill_filled_size > ZERO),
        complete_fill_count=sum(1 for trade in trades if trade.fill_status == "complete"),
        partial_fill_count=sum(1 for trade in trades if trade.fill_status == "partial"),
        resolved_count=(
            sum(row.resolved_count for row in rows)
            if has_outcomes
            else None
        ),
        pending_count=(
            sum(row.pending_count for row in rows)
            if has_outcomes
            else None
        ),
        realized_win_count=(
            sum(row.realized_win_count for row in rows)
            if has_outcomes
            else None
        ),
        realized_loss_count=(
            sum(row.realized_loss_count for row in rows)
            if has_outcomes
            else None
        ),
        total_requested_size=sum((row.total_requested_size for row in rows), ZERO),
        total_filled_size=sum((row.total_filled_size for row in rows), ZERO),
        total_unfilled_size=sum((row.total_unfilled_size for row in rows), ZERO),
        total_notional=sum((row.total_notional for row in rows), ZERO),
        first_trade_decision_at=min(decisions) if decisions else None,
        latest_trade_decision_at=max(decisions) if decisions else None,
        rows=rows,
    )


class _GroupAccumulator:
    def __init__(self, *, market_slug: str, side: str, status: str) -> None:
        self.market_slug = market_slug
        self.side = side
        self.status = status
        self.trade_count = 0
        self.filled_count = 0
        self.complete_fill_count = 0
        self.partial_fill_count = 0
        self.resolved_count: int | None = None
        self.pending_count: int | None = None
        self.realized_win_count: int | None = None
        self.realized_loss_count: int | None = None
        self.total_requested_size = ZERO
        self.total_filled_size = ZERO
        self.total_unfilled_size = ZERO
        self.total_notional = ZERO
        self.reason_codes: set[str] | None = None

    def add_trade(
        self,
        trade: PaperTradeRecord,
        *,
        outcome: PaperForecastEvidenceObservation | None | _PendingOutcome,
    ) -> None:
        self.trade_count += 1
        if trade.fill_filled_size > ZERO:
            self.filled_count += 1
        if trade.fill_status == "complete":
            self.complete_fill_count += 1
        if trade.fill_status == "partial":
            self.partial_fill_count += 1
        self.total_requested_size += trade.order_requested_size
        self.total_filled_size += trade.fill_filled_size
        self.total_unfilled_size += trade.fill_unfilled_size
        self.total_notional += trade.fill_filled_size * trade.fill_average_price
        self._add_reason_code(_fill_reason_code(trade.fill_status))
        self._add_reason_code(f"sizing_limiter:{trade.sizing_limiter}")

        if outcome is _PENDING_OUTCOME:
            self.pending_count = _increment_optional_counter(self.pending_count)
            self.resolved_count = _zero_if_none(self.resolved_count)
            self.realized_win_count = _zero_if_none(self.realized_win_count)
            self.realized_loss_count = _zero_if_none(self.realized_loss_count)
        elif outcome is not None:
            self.resolved_count = _increment_optional_counter(self.resolved_count)
            self.pending_count = _zero_if_none(self.pending_count)
            if outcome.actual_outcome_value == ONE:
                self.realized_win_count = _increment_optional_counter(
                    self.realized_win_count,
                )
                self.realized_loss_count = _zero_if_none(self.realized_loss_count)
            else:
                self.realized_loss_count = _increment_optional_counter(
                    self.realized_loss_count,
                )
                self.realized_win_count = _zero_if_none(self.realized_win_count)

    def _add_reason_code(self, reason_code: str) -> None:
        if self.reason_codes is None:
            self.reason_codes = set()
        self.reason_codes.add(reason_code)

    def to_row(self) -> PaperTradeAttributionRow:
        return PaperTradeAttributionRow(
            market_slug=self.market_slug,
            side=self.side,
            status=self.status,
            trade_count=self.trade_count,
            filled_count=self.filled_count,
            complete_fill_count=self.complete_fill_count,
            partial_fill_count=self.partial_fill_count,
            resolved_count=self.resolved_count,
            pending_count=self.pending_count,
            realized_win_count=self.realized_win_count,
            realized_loss_count=self.realized_loss_count,
            total_requested_size=self.total_requested_size,
            total_filled_size=self.total_filled_size,
            total_unfilled_size=self.total_unfilled_size,
            total_notional=self.total_notional,
            reason_codes=tuple(sorted(self.reason_codes or ())),
        )


class _PendingOutcome:
    pass


_PENDING_OUTCOME = _PendingOutcome()


def _lookup_outcome(
    trade: PaperTradeRecord,
    outcomes_by_packet_id: dict[str, PaperForecastEvidenceObservation],
    outcome_report: OutcomeTrackingReport | None,
) -> PaperForecastEvidenceObservation | _PendingOutcome | None:
    if outcome_report is None:
        return None
    return outcomes_by_packet_id.get(trade.packet_id, _PENDING_OUTCOME)


def _outcomes_by_packet_id(
    outcome_report: OutcomeTrackingReport | None,
) -> dict[str, PaperForecastEvidenceObservation]:
    if outcome_report is None:
        return {}
    lookup: dict[str, PaperForecastEvidenceObservation] = {}
    for observation in outcome_report.observations:
        if observation.paper_only is not True:
            raise ValueError("outcome_report observations must be paper_only")
        lookup[observation.source_packet_id] = observation
    return lookup


def _normalize_trade_records(
    trade_records: Iterable[PaperTradeRecord],
) -> tuple[PaperTradeRecord, ...]:
    if isinstance(trade_records, (str, bytes)):
        raise ValueError("trade_records must be an iterable of PaperTradeRecord values")
    try:
        trades = tuple(trade_records)
    except TypeError as exc:
        raise ValueError(
            "trade_records must be an iterable of PaperTradeRecord values",
        ) from exc
    for trade in trades:
        if type(trade) is not PaperTradeRecord:
            raise ValueError("trade_records must contain only PaperTradeRecord values")
        _validate_trade_record(trade)
    return trades


def _validate_trade_record(trade: PaperTradeRecord) -> None:
    for field_name in (
        "market_slug",
        "outcome_name",
        "fill_status",
        "sizing_limiter",
    ):
        _require_canonical_string(field_name, getattr(trade, field_name))
    for field_name in (
        "order_requested_size",
        "fill_filled_size",
        "fill_unfilled_size",
        "fill_average_price",
    ):
        _require_nonnegative_decimal(field_name, getattr(trade, field_name))


def _side_for_trade(trade: PaperTradeRecord) -> str:
    normalized = trade.outcome_name.strip().lower()
    if normalized in {"yes", "true", "long"}:
        return "yes"
    if normalized in {"no", "false", "short"}:
        return "no"
    return normalized


def _fill_reason_code(status: str) -> str:
    if status == "complete":
        return "fill_complete"
    if status == "partial":
        return "fill_partial"
    return f"fill_status:{status}"


def _increment_optional_counter(value: int | None) -> int:
    return 1 if value is None else value + 1


def _zero_if_none(value: int | None) -> int:
    return 0 if value is None else value


def _normalize_rows(
    rows: tuple[PaperTradeAttributionRow, ...],
) -> tuple[PaperTradeAttributionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperTradeAttributionRow:
            raise ValueError("rows must contain PaperTradeAttributionRow values")
        if row.paper_only is not True:
            raise ValueError("rows must contain paper_only values")
        if row.report_only is not True:
            raise ValueError("rows must contain report_only values")
        if row.readonly is not True:
            raise ValueError("rows must contain readonly values")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if normalized != tuple(sorted(normalized)):
        raise ValueError("reason_codes must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return normalized


def _validate_row_consistency(row: PaperTradeAttributionRow) -> None:
    if row.trade_count == 0:
        if row.filled_count != 0:
            raise ValueError("filled_count must be zero without trades")
        if row.complete_fill_count != 0:
            raise ValueError("complete_fill_count must be zero without trades")
        if row.partial_fill_count != 0:
            raise ValueError("partial_fill_count must be zero without trades")
    if row.filled_count > row.trade_count:
        raise ValueError("filled_count must not exceed trade_count")
    if row.complete_fill_count + row.partial_fill_count > row.trade_count:
        raise ValueError("fill status counts must not exceed trade_count")
    if row.resolved_count is None:
        for field_name in (
            "pending_count",
            "realized_win_count",
            "realized_loss_count",
        ):
            if getattr(row, field_name) is not None:
                raise ValueError("outcome counts must be all present or all absent")
    else:
        for field_name in (
            "pending_count",
            "realized_win_count",
            "realized_loss_count",
        ):
            if getattr(row, field_name) is None:
                raise ValueError("outcome counts must be all present or all absent")
        if row.resolved_count + row.pending_count != row.trade_count:
            raise ValueError("resolved_count + pending_count must equal trade_count")
        if row.realized_win_count + row.realized_loss_count != row.resolved_count:
            raise ValueError("realized counts must equal resolved_count")


def _validate_report_consistency(report: PaperTradeAttributionReport) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.market_count != len({row.market_slug for row in report.rows}):
        raise ValueError("market_count must equal unique row markets")
    if report.trade_count != sum(row.trade_count for row in report.rows):
        raise ValueError("trade_count must equal row trade counts")
    for field_name in (
        "filled_count",
        "complete_fill_count",
        "partial_fill_count",
    ):
        if getattr(report, field_name) != sum(
            getattr(row, field_name) for row in report.rows
        ):
            raise ValueError(f"{field_name} must equal row totals")
    for field_name in (
        "total_requested_size",
        "total_filled_size",
        "total_unfilled_size",
        "total_notional",
    ):
        if getattr(report, field_name) != sum(
            (getattr(row, field_name) for row in report.rows),
            ZERO,
        ):
            raise ValueError(f"{field_name} must equal row totals")
    if report.trade_count == 0:
        if report.first_trade_decision_at is not None:
            raise ValueError("first_trade_decision_at must be absent without trades")
        if report.latest_trade_decision_at is not None:
            raise ValueError("latest_trade_decision_at must be absent without trades")
    else:
        if report.first_trade_decision_at is None:
            raise ValueError("first_trade_decision_at is required with trades")
        if report.latest_trade_decision_at is None:
            raise ValueError("latest_trade_decision_at is required with trades")
        if report.latest_trade_decision_at < report.first_trade_decision_at:
            raise ValueError("latest_trade_decision_at cannot precede first")
    if report.resolved_count is None:
        for field_name in (
            "pending_count",
            "realized_win_count",
            "realized_loss_count",
        ):
            if getattr(report, field_name) is not None:
                raise ValueError("outcome counts must be all present or all absent")
    else:
        for field_name in (
            "pending_count",
            "realized_win_count",
            "realized_loss_count",
        ):
            if getattr(report, field_name) is None:
                raise ValueError("outcome counts must be all present or all absent")
        if report.resolved_count + report.pending_count != report.trade_count:
            raise ValueError("resolved_count + pending_count must equal trade_count")
        if report.realized_win_count + report.realized_loss_count != report.resolved_count:
            raise ValueError("realized counts must equal resolved_count")
        for field_name in (
            "resolved_count",
            "pending_count",
            "realized_win_count",
            "realized_loss_count",
        ):
            if getattr(report, field_name) != sum(
                getattr(row, field_name) for row in report.rows
            ):
                raise ValueError(f"{field_name} must equal row totals")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: Any) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "PaperTradeAttributionConfig",
    "PaperTradeAttributionReport",
    "PaperTradeAttributionRow",
    "build_paper_trade_attribution_report",
)
