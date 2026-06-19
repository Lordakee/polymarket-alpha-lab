"""Paper-only settlement timing reducer.

Pure supplied-input scoring for event-contract recommendation timing.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64)
ACTIONS = ("recommend", "watch", "reject")
TIMING_STATUSES = ("acceptable", "watch", "blocked")
STATUS_PRIORITY = {
    "acceptable": 0,
    "watch": 1,
    "blocked": 2,
}
WATCH_REASONS = {
    "settlement_context_stale",
    "source_action_watch",
}
BLOCK_REASONS = {
    "nonpositive_adjusted_net_probability_edge",
    "resolution_already_due",
    "resolution_horizon_exceeded",
    "source_action_reject",
    "unknown_resolution",
}


@dataclass(frozen=True)
class PaperSettlementTimingInput:
    market_slug: str
    side: str
    action: str
    net_probability_edge: Decimal
    expected_resolution_at: datetime | None
    settlement_context_fresh: bool
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        if self.action not in ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "expected_resolution_at",
            _as_optional_utc("expected_resolution_at", self.expected_resolution_at),
        )
        _require_bool("settlement_context_fresh", self.settlement_context_fresh)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperSettlementTimingConfig:
    config_version: str
    max_resolution_horizon_days: Decimal
    stale_context_penalty_per_share: Decimal
    unknown_resolution_penalty_per_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_resolution_horizon_days",
            _normalize_nonnegative_decimal(
                "max_resolution_horizon_days",
                self.max_resolution_horizon_days,
            ),
        )
        object.__setattr__(
            self,
            "stale_context_penalty_per_share",
            _normalize_nonnegative_decimal(
                "stale_context_penalty_per_share",
                self.stale_context_penalty_per_share,
            ),
        )
        object.__setattr__(
            self,
            "unknown_resolution_penalty_per_share",
            _normalize_nonnegative_decimal(
                "unknown_resolution_penalty_per_share",
                self.unknown_resolution_penalty_per_share,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperSettlementTimingRow:
    market_slug: str
    side: str
    action: str
    net_probability_edge: Decimal
    expected_resolution_at: datetime | None
    settlement_context_fresh: bool
    observed_at: datetime
    days_to_resolution: Decimal | None
    timing_status: str
    timing_cost_per_share: Decimal
    adjusted_net_probability_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        if self.action not in ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "expected_resolution_at",
            _as_optional_utc("expected_resolution_at", self.expected_resolution_at),
        )
        _require_bool("settlement_context_fresh", self.settlement_context_fresh)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "days_to_resolution",
            _normalize_optional_nonnegative_decimal(
                "days_to_resolution",
                self.days_to_resolution,
            ),
        )
        if self.timing_status not in TIMING_STATUSES:
            raise ValueError("timing_status must be acceptable, watch, or blocked")
        object.__setattr__(
            self,
            "timing_cost_per_share",
            _normalize_nonnegative_decimal(
                "timing_cost_per_share",
                self.timing_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "adjusted_net_probability_edge",
            _normalize_decimal(
                "adjusted_net_probability_edge",
                self.adjusted_net_probability_edge,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperSettlementTimingReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    acceptable_count: int
    watch_count: int
    blocked_count: int
    rows: tuple[PaperSettlementTimingRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "acceptable_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_settlement_timing_report(
    inputs: Iterable[PaperSettlementTimingInput],
    *,
    config: PaperSettlementTimingConfig,
    generated_at: datetime,
) -> PaperSettlementTimingReport:
    if type(config) is not PaperSettlementTimingConfig:
        raise ValueError("config must be a PaperSettlementTimingConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_safety_flags(config)

    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return PaperSettlementTimingReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        acceptable_count=_status_count(rows, "acceptable"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        rows=rows,
    )


def _row_from_input(
    value: PaperSettlementTimingInput,
    *,
    config: PaperSettlementTimingConfig,
) -> PaperSettlementTimingRow:
    days_to_resolution = _days_to_resolution(
        observed_at=value.observed_at,
        expected_resolution_at=value.expected_resolution_at,
    )
    timing_cost_per_share = _timing_cost_per_share(value, config=config)
    adjusted_net_probability_edge = _subtract_decimal(
        value.net_probability_edge,
        timing_cost_per_share,
    )
    timing_status = _timing_status_for(
        action=value.action,
        adjusted_net_probability_edge=adjusted_net_probability_edge,
        days_to_resolution=days_to_resolution,
        max_resolution_horizon_days=config.max_resolution_horizon_days,
        settlement_context_fresh=value.settlement_context_fresh,
        expected_resolution_at=value.expected_resolution_at,
        observed_at=value.observed_at,
    )
    reason_codes = _reason_codes_for(
        source_reason_codes=value.reason_codes,
        action=value.action,
        adjusted_net_probability_edge=adjusted_net_probability_edge,
        days_to_resolution=days_to_resolution,
        max_resolution_horizon_days=config.max_resolution_horizon_days,
        settlement_context_fresh=value.settlement_context_fresh,
        expected_resolution_at=value.expected_resolution_at,
        observed_at=value.observed_at,
    )

    return PaperSettlementTimingRow(
        market_slug=value.market_slug,
        side=value.side,
        action=value.action,
        net_probability_edge=value.net_probability_edge,
        expected_resolution_at=value.expected_resolution_at,
        settlement_context_fresh=value.settlement_context_fresh,
        observed_at=value.observed_at,
        days_to_resolution=days_to_resolution,
        timing_status=timing_status,
        timing_cost_per_share=timing_cost_per_share,
        adjusted_net_probability_edge=adjusted_net_probability_edge,
        reason_codes=reason_codes,
    )


def _timing_cost_per_share(
    value: PaperSettlementTimingInput,
    *,
    config: PaperSettlementTimingConfig,
) -> Decimal:
    stale_penalty = (
        config.stale_context_penalty_per_share
        if value.settlement_context_fresh is not True
        else ZERO
    )
    unknown_penalty = (
        config.unknown_resolution_penalty_per_share
        if value.expected_resolution_at is None
        else ZERO
    )
    return _add_decimal(stale_penalty, unknown_penalty)


def _timing_status_for(
    *,
    action: str,
    adjusted_net_probability_edge: Decimal,
    days_to_resolution: Decimal | None,
    max_resolution_horizon_days: Decimal,
    settlement_context_fresh: bool,
    expected_resolution_at: datetime | None,
    observed_at: datetime,
) -> str:
    if action == "reject":
        return "blocked"
    if expected_resolution_at is None:
        return "blocked"
    if expected_resolution_at <= observed_at:
        return "blocked"
    if (
        days_to_resolution is not None
        and days_to_resolution > max_resolution_horizon_days
    ):
        return "blocked"
    if adjusted_net_probability_edge <= ZERO:
        return "blocked"
    if action == "watch":
        return "watch"
    if settlement_context_fresh is not True:
        return "watch"
    return "acceptable"


def _reason_codes_for(
    *,
    source_reason_codes: tuple[str, ...],
    action: str,
    adjusted_net_probability_edge: Decimal,
    days_to_resolution: Decimal | None,
    max_resolution_horizon_days: Decimal,
    settlement_context_fresh: bool,
    expected_resolution_at: datetime | None,
    observed_at: datetime,
) -> tuple[str, ...]:
    action_codes = (
        ("source_action_watch",)
        if action == "watch"
        else ("source_action_reject",)
        if action == "reject"
        else ()
    )
    settlement_codes = (
        ("settlement_context_stale",)
        if settlement_context_fresh is not True
        else ()
    )
    unknown_codes = (
        ("unknown_resolution",)
        if expected_resolution_at is None
        else ()
    )
    already_due_codes = (
        ("resolution_already_due",)
        if expected_resolution_at is not None and expected_resolution_at <= observed_at
        else ()
    )
    horizon_codes = (
        ("resolution_horizon_exceeded",)
        if days_to_resolution is not None
        and days_to_resolution > max_resolution_horizon_days
        else ()
    )
    edge_codes = (
        ("nonpositive_adjusted_net_probability_edge",)
        if adjusted_net_probability_edge <= ZERO
        else ()
    )
    return _normalize_reason_codes(
        (
            *source_reason_codes,
            *action_codes,
            *settlement_codes,
            *unknown_codes,
            *already_due_codes,
            *horizon_codes,
            *edge_codes,
        ),
    )


def _days_to_resolution(
    *,
    observed_at: datetime,
    expected_resolution_at: datetime | None,
) -> Decimal | None:
    if expected_resolution_at is None:
        return None
    if expected_resolution_at <= observed_at:
        return _quantize(ZERO)
    difference = expected_resolution_at - observed_at
    seconds = Decimal(difference.days * 86400 + difference.seconds)
    microseconds = Decimal(difference.microseconds) / Decimal("1000000")
    return _divide_decimal(_add_decimal(seconds, microseconds), SECONDS_PER_DAY)


def _row_sort_key(
    row: PaperSettlementTimingRow,
) -> tuple[Decimal, int, str, str]:
    return (
        -row.adjusted_net_probability_edge,
        STATUS_PRIORITY[row.timing_status],
        row.market_slug,
        row.side,
    )


def _status_count(rows: tuple[PaperSettlementTimingRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.timing_status == status)


def _normalize_inputs(
    values: Iterable[PaperSettlementTimingInput],
) -> tuple[PaperSettlementTimingInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of PaperSettlementTimingInput values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of PaperSettlementTimingInput values",
        ) from exc
    for value in normalized:
        if type(value) is not PaperSettlementTimingInput:
            raise ValueError(
                "inputs must contain only PaperSettlementTimingInput values",
            )
        _require_safety_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[PaperSettlementTimingRow],
) -> tuple[PaperSettlementTimingRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperSettlementTimingRow:
            raise ValueError("rows must contain PaperSettlementTimingRow values")
        _require_safety_flags(row)
    return normalized


def _validate_row_consistency(row: PaperSettlementTimingRow) -> None:
    expected_days_to_resolution = _days_to_resolution(
        observed_at=row.observed_at,
        expected_resolution_at=row.expected_resolution_at,
    )
    if row.days_to_resolution != expected_days_to_resolution:
        raise ValueError("days_to_resolution must match resolution timestamps")
    if (
        row.expected_resolution_at is not None
        and row.settlement_context_fresh is True
        and row.timing_cost_per_share != _quantize(ZERO)
    ):
        raise ValueError("timing_cost_per_share must be zero for fresh known timing")
    expected_adjusted_edge = _subtract_decimal(
        row.net_probability_edge,
        row.timing_cost_per_share,
    )
    if row.adjusted_net_probability_edge != expected_adjusted_edge:
        raise ValueError(
            "adjusted_net_probability_edge must match edge and timing cost",
        )
    if row.expected_resolution_at is None:
        _require_row_status_and_reason(
            row,
            status="blocked",
            reason_code="unknown_resolution",
        )
    if (
        row.expected_resolution_at is not None
        and row.expected_resolution_at <= row.observed_at
    ):
        _require_row_status_and_reason(
            row,
            status="blocked",
            reason_code="resolution_already_due",
        )
    if row.action == "reject":
        _require_row_status_and_reason(
            row,
            status="blocked",
            reason_code="source_action_reject",
        )
    if row.adjusted_net_probability_edge <= ZERO:
        _require_row_status_and_reason(
            row,
            status="blocked",
            reason_code="nonpositive_adjusted_net_probability_edge",
        )
    if row.timing_status == "acceptable":
        if row.action != "recommend":
            raise ValueError("timing_status acceptable requires recommend action")
        if row.expected_resolution_at is None:
            raise ValueError("timing_status acceptable requires known resolution")
        if row.expected_resolution_at <= row.observed_at:
            raise ValueError("timing_status acceptable requires future resolution")
        if row.settlement_context_fresh is not True:
            raise ValueError("timing_status acceptable requires fresh settlement context")
        if row.timing_cost_per_share != _quantize(ZERO):
            raise ValueError("timing_status acceptable requires zero timing cost")
        if row.adjusted_net_probability_edge <= ZERO:
            raise ValueError("timing_status acceptable requires positive adjusted edge")
    if row.timing_status == "watch":
        if row.adjusted_net_probability_edge <= ZERO:
            raise ValueError("timing_status watch requires positive adjusted edge")
        if row.expected_resolution_at is None:
            raise ValueError("timing_status watch requires known resolution")
        if not any(reason_code in row.reason_codes for reason_code in WATCH_REASONS):
            raise ValueError("timing_status watch requires a watch reason")
    if row.timing_status == "blocked":
        if not any(reason_code in row.reason_codes for reason_code in BLOCK_REASONS):
            raise ValueError("timing_status blocked requires a blocked reason")


def _require_row_status_and_reason(
    row: PaperSettlementTimingRow,
    *,
    status: str,
    reason_code: str,
) -> None:
    if row.timing_status != status:
        raise ValueError(f"timing_status must be {status} for {reason_code}")
    if reason_code not in row.reason_codes:
        raise ValueError(f"reason_codes must include {reason_code}")


def _validate_report_consistency(report: PaperSettlementTimingReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must equal rows length")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.acceptable_count != _status_count(report.rows, "acceptable"):
        raise ValueError("acceptable_count must equal rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must equal rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must equal rows")
    if report.row_count != (
        report.acceptable_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("row_count must equal status counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


__all__ = (
    "PaperSettlementTimingInput",
    "PaperSettlementTimingConfig",
    "PaperSettlementTimingRow",
    "PaperSettlementTimingReport",
    "build_paper_settlement_timing_report",
)
