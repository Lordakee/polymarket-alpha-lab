"""Paper-only P(YES) probability sanity report.

Pure supplied-input checks for forecast, market, bid/ask, threshold, and edge
direction consistency. This module performs no I/O and has no execution surface.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
DECIMAL_CONTEXT = Context(prec=64)
SANITY_STATUSES = ("ready", "blocked")
REPORT_STATUSES = ("ready", "blocked")


@dataclass(frozen=True)
class PredictionMarketProbabilitySanityInput:
    candidate_id: str
    market_slug: str
    forecast_probability: Decimal
    market_probability: Decimal
    bid_implied_probability: Decimal
    ask_implied_probability: Decimal
    cost_adjusted_threshold: Decimal
    edge_to_threshold: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "bid_implied_probability",
            "ask_implied_probability",
            "cost_adjusted_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_to_threshold",
            _normalize_decimal("edge_to_threshold", self.edge_to_threshold),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_safety_flags(self)


@dataclass(frozen=True)
class PredictionMarketProbabilitySanityRow:
    candidate_id: str
    market_slug: str
    forecast_probability: Decimal
    market_probability: Decimal
    bid_implied_probability: Decimal
    ask_implied_probability: Decimal
    bid_ask_mid_probability: Decimal
    cost_adjusted_threshold: Decimal
    edge_to_threshold: Decimal
    probability_gap: Decimal
    bid_ask_mid_gap: Decimal
    threshold_probability_gap: Decimal
    sanity_status: str
    inconsistency_reasons: tuple[str, ...]
    blocker_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "bid_implied_probability",
            "ask_implied_probability",
            "bid_ask_mid_probability",
            "cost_adjusted_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "edge_to_threshold",
            "probability_gap",
            "bid_ask_mid_gap",
            "threshold_probability_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        if self.sanity_status not in SANITY_STATUSES:
            raise ValueError("sanity_status must be ready or blocked")
        object.__setattr__(
            self,
            "inconsistency_reasons",
            _normalize_reason_codes(self.inconsistency_reasons),
        )
        object.__setattr__(
            self,
            "blocker_reasons",
            _normalize_reason_codes(self.blocker_reasons),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PredictionMarketProbabilitySanityReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    ready_count: int
    blocked_count: int
    ready_ratio: Decimal
    max_probability_gap: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PredictionMarketProbabilitySanityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("input_count", "row_count", "ready_count", "blocked_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_probability("ready_ratio", self.ready_ratio),
        )
        object.__setattr__(
            self,
            "max_probability_gap",
            _normalize_probability("max_probability_gap", self.max_probability_gap),
        )
        if self.report_status not in REPORT_STATUSES:
            raise ValueError("report_status must be ready or blocked")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_prediction_market_probability_sanity_report(
    inputs: Iterable[PredictionMarketProbabilitySanityInput],
    *,
    config_version: str,
    generated_at: datetime,
) -> PredictionMarketProbabilitySanityReport:
    _require_canonical_string("config_version", config_version)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(sorted((_row_from_input(value) for value in normalized_inputs), key=_row_sort_key))
    ready_count = _status_count(rows, "ready")
    blocked_count = _status_count(rows, "blocked")
    return PredictionMarketProbabilitySanityReport(
        generated_at=_as_utc(generated_at),
        config_version=config_version,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        ready_count=ready_count,
        blocked_count=blocked_count,
        ready_ratio=_ready_ratio(ready_count=ready_count, row_count=len(rows)),
        max_probability_gap=_max_probability_gap(rows),
        report_status="blocked" if blocked_count else "ready",
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def prediction_market_probability_sanity_report_payload(
    report: PredictionMarketProbabilitySanityReport,
) -> dict[str, Any]:
    if type(report) is not PredictionMarketProbabilitySanityReport:
        raise ValueError("report must be a PredictionMarketProbabilitySanityReport")
    _validate_report_consistency(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_from_input(
    value: PredictionMarketProbabilitySanityInput,
) -> PredictionMarketProbabilitySanityRow:
    bid_ask_mid_probability = _divide_decimal(
        _sum_decimals((value.bid_implied_probability, value.ask_implied_probability)),
        TWO,
    )
    probability_gap = _subtract_decimal(value.forecast_probability, value.market_probability)
    bid_ask_mid_gap = _subtract_decimal(value.market_probability, bid_ask_mid_probability)
    threshold_probability_gap = _subtract_decimal(
        value.forecast_probability,
        value.cost_adjusted_threshold,
    )
    inconsistency_reasons = _inconsistency_reasons(
        value=value,
        probability_gap=probability_gap,
        bid_ask_mid_gap=bid_ask_mid_gap,
        threshold_probability_gap=threshold_probability_gap,
    )
    blocker_reasons = _blocker_reasons(inconsistency_reasons)
    sanity_status = "blocked" if blocker_reasons else "ready"
    status_reason = (
        "probability_sanity_blocked"
        if sanity_status == "blocked"
        else "probability_sanity_ready"
    )
    return PredictionMarketProbabilitySanityRow(
        candidate_id=value.candidate_id,
        market_slug=value.market_slug,
        forecast_probability=value.forecast_probability,
        market_probability=value.market_probability,
        bid_implied_probability=value.bid_implied_probability,
        ask_implied_probability=value.ask_implied_probability,
        bid_ask_mid_probability=bid_ask_mid_probability,
        cost_adjusted_threshold=value.cost_adjusted_threshold,
        edge_to_threshold=value.edge_to_threshold,
        probability_gap=probability_gap,
        bid_ask_mid_gap=bid_ask_mid_gap,
        threshold_probability_gap=threshold_probability_gap,
        sanity_status=sanity_status,
        inconsistency_reasons=inconsistency_reasons,
        blocker_reasons=blocker_reasons,
        reason_codes=_normalize_reason_codes(
            (
                status_reason,
                *value.reason_codes,
                *inconsistency_reasons,
                *blocker_reasons,
            ),
        ),
    )


def _inconsistency_reasons(
    *,
    value: PredictionMarketProbabilitySanityInput,
    probability_gap: Decimal,
    bid_ask_mid_gap: Decimal,
    threshold_probability_gap: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if value.bid_implied_probability > value.ask_implied_probability:
        reasons.append("bid_above_ask")
    if not _same_direction(probability_gap, threshold_probability_gap):
        reasons.append("forecast_threshold_direction_mismatch")
    if not _same_direction(threshold_probability_gap, value.edge_to_threshold):
        reasons.append("edge_to_threshold_direction_mismatch")
    if threshold_probability_gap != value.edge_to_threshold:
        reasons.append("edge_to_threshold_value_mismatch")
    lower_bound = min(value.bid_implied_probability, value.ask_implied_probability)
    upper_bound = max(value.bid_implied_probability, value.ask_implied_probability)
    if not lower_bound <= value.market_probability <= upper_bound:
        reasons.append("market_probability_outside_bid_ask")
    return _normalize_reason_codes(tuple(reasons))


def _blocker_reasons(inconsistency_reasons: tuple[str, ...]) -> tuple[str, ...]:
    blockers: list[str] = []
    if "bid_above_ask" in inconsistency_reasons:
        blockers.append("bid_ask_implied_probability_inconsistent")
    if any(reason.startswith("edge_to_threshold_") for reason in inconsistency_reasons):
        blockers.append("edge_to_threshold_inconsistent")
    if "forecast_threshold_direction_mismatch" in inconsistency_reasons:
        blockers.append("forecast_threshold_direction_inconsistent")
    if "market_probability_outside_bid_ask" in inconsistency_reasons:
        blockers.append("market_probability_bid_ask_inconsistent")
    return _normalize_reason_codes(tuple(blockers))


def _same_direction(left: Decimal, right: Decimal) -> bool:
    if left == ZERO and right == ZERO:
        return True
    if left > ZERO and right > ZERO:
        return True
    if left < ZERO and right < ZERO:
        return True
    return False


def _row_sort_key(
    row: PredictionMarketProbabilitySanityRow,
) -> tuple[int, Decimal, str, str]:
    return (
        0 if row.sanity_status == "blocked" else 1,
        -_abs_decimal(row.probability_gap),
        row.market_slug,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[PredictionMarketProbabilitySanityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.sanity_status == status)


def _ready_ratio(*, ready_count: int, row_count: int) -> Decimal:
    if row_count == 0:
        return _quantize(ZERO)
    return _divide_decimal(Decimal(ready_count), Decimal(row_count))


def _max_probability_gap(rows: tuple[PredictionMarketProbabilitySanityRow, ...]) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    return max(_abs_decimal(row.probability_gap) for row in rows)


def _report_reason_codes(
    rows: tuple[PredictionMarketProbabilitySanityRow, ...],
) -> tuple[str, ...]:
    if not any(row.sanity_status == "blocked" for row in rows):
        return ("probability_sanity_ready",)
    return _normalize_reason_codes(
        (
            "probability_sanity_blocked",
            *(
                reason
                for row in rows
                for reason in (*row.inconsistency_reasons, *row.blocker_reasons)
            ),
        ),
    )


def _normalize_inputs(
    values: Iterable[PredictionMarketProbabilitySanityInput],
) -> tuple[PredictionMarketProbabilitySanityInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(
            "inputs must be an iterable of PredictionMarketProbabilitySanityInput values",
        )
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of PredictionMarketProbabilitySanityInput values",
        ) from exc
    for value in normalized:
        if type(value) is not PredictionMarketProbabilitySanityInput:
            raise ValueError(
                "inputs must contain only PredictionMarketProbabilitySanityInput values",
            )
        if value.paper_only is not True:
            raise ValueError("inputs must contain paper_only values")
        if value.report_only is not True:
            raise ValueError("inputs must contain report_only values")
        if value.readonly is not True:
            raise ValueError("inputs must contain readonly values")
    return normalized


def _normalize_rows(
    rows: Iterable[PredictionMarketProbabilitySanityRow],
) -> tuple[PredictionMarketProbabilitySanityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PredictionMarketProbabilitySanityRow:
            raise ValueError("rows must contain PredictionMarketProbabilitySanityRow values")
        if row.paper_only is not True:
            raise ValueError("rows must contain paper_only values")
        if row.report_only is not True:
            raise ValueError("rows must contain report_only values")
        if row.readonly is not True:
            raise ValueError("rows must contain readonly values")
    return normalized


def _validate_row_consistency(row: PredictionMarketProbabilitySanityRow) -> None:
    expected_mid = _divide_decimal(
        _sum_decimals((row.bid_implied_probability, row.ask_implied_probability)),
        TWO,
    )
    if row.bid_ask_mid_probability != expected_mid:
        raise ValueError("bid_ask_mid_probability must match bid and ask")
    if row.probability_gap != _subtract_decimal(
        row.forecast_probability,
        row.market_probability,
    ):
        raise ValueError("probability_gap must match forecast and market probabilities")
    if row.bid_ask_mid_gap != _subtract_decimal(
        row.market_probability,
        row.bid_ask_mid_probability,
    ):
        raise ValueError("bid_ask_mid_gap must match market and bid/ask mid")
    if row.threshold_probability_gap != _subtract_decimal(
        row.forecast_probability,
        row.cost_adjusted_threshold,
    ):
        raise ValueError("threshold_probability_gap must match forecast and threshold")
    expected_inconsistency_reasons = _inconsistency_reasons(
        value=PredictionMarketProbabilitySanityInput(
            candidate_id=row.candidate_id,
            market_slug=row.market_slug,
            forecast_probability=row.forecast_probability,
            market_probability=row.market_probability,
            bid_implied_probability=row.bid_implied_probability,
            ask_implied_probability=row.ask_implied_probability,
            cost_adjusted_threshold=row.cost_adjusted_threshold,
            edge_to_threshold=row.edge_to_threshold,
            reason_codes=(),
        ),
        probability_gap=row.probability_gap,
        bid_ask_mid_gap=row.bid_ask_mid_gap,
        threshold_probability_gap=row.threshold_probability_gap,
    )
    if row.inconsistency_reasons != expected_inconsistency_reasons:
        raise ValueError("inconsistency_reasons must match probability sanity checks")
    expected_blocker_reasons = _blocker_reasons(row.inconsistency_reasons)
    if row.blocker_reasons != expected_blocker_reasons:
        raise ValueError("blocker_reasons must match inconsistency reasons")
    expected_status = "blocked" if row.blocker_reasons else "ready"
    if row.sanity_status != expected_status:
        raise ValueError("sanity_status must match blocker_reasons")


def _validate_report_consistency(report: PredictionMarketProbabilitySanityReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must match rows")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.ready_ratio != _ready_ratio(
        ready_count=report.ready_count,
        row_count=report.row_count,
    ):
        raise ValueError("ready_ratio must match ready_count and row_count")
    if report.max_probability_gap != _max_probability_gap(report.rows):
        raise ValueError("max_probability_gap must match rows")
    expected_status = "blocked" if report.blocked_count else "ready"
    if report.report_status != expected_status:
        raise ValueError("report_status must match blocked_count")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        raw_codes = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    normalized: list[str] = []
    seen: set[str] = set()
    for code in raw_codes:
        _require_canonical_string("reason_code", code)
        if code not in seen:
            normalized.append(code)
            seen.add(code)
    return tuple(normalized)


def _require_safety_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return _quantize(total)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value
