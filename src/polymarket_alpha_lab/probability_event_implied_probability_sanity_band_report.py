"""Paper-only probability event implied probability sanity band report.

Pure supplied-input checks for YES/NO implied probability sums, forecast
reference bands, and spread sanity. This module performs no I/O and has no
execution surface.
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
WATCH_YES_NO_SUM_GAP = Decimal("0.020000")
BLOCK_YES_NO_SUM_GAP = Decimal("0.050000")
WATCH_BAND_GAP = Decimal("0.020000")
BLOCK_BAND_GAP = Decimal("0.100000")
WATCH_SPREAD_PROBABILITY = Decimal("0.050000")
BLOCK_SPREAD_PROBABILITY = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64)
SANITY_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("pass", "watch", "block")
MANUAL_NEXT_STEPS = (
    "no_manual_action_required",
    "manual_verify_probability_inputs",
    "manual_review_required_before_research_use",
)


@dataclass(frozen=True)
class ProbabilityEventImpliedProbabilitySanityBandInput:
    event_id: str
    market_slug: str
    yes_probability: Decimal
    no_probability: Decimal
    forecast_probability: Decimal
    reference_probability_low: Decimal
    reference_probability_high: Decimal
    spread_probability: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "yes_probability",
            "no_probability",
            "forecast_probability",
            "reference_probability_low",
            "reference_probability_high",
            "spread_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.reference_probability_low > self.reference_probability_high:
            raise ValueError(
                "reference_probability_low must be at most reference_probability_high",
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_safety_flags(self)


@dataclass(frozen=True)
class ProbabilityEventImpliedProbabilitySanityBandRow:
    event_id: str
    market_slug: str
    yes_probability: Decimal
    no_probability: Decimal
    yes_no_sum_probability: Decimal
    yes_no_sum_gap: Decimal
    forecast_probability: Decimal
    reference_probability_low: Decimal
    reference_probability_high: Decimal
    reference_mid_probability: Decimal
    forecast_reference_mid_gap: Decimal
    band_gap: Decimal
    spread_probability: Decimal
    sanity_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "yes_probability",
            "no_probability",
            "forecast_probability",
            "reference_probability_low",
            "reference_probability_high",
            "reference_mid_probability",
            "spread_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "yes_no_sum_probability",
            "yes_no_sum_gap",
            "forecast_reference_mid_gap",
            "band_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        if self.reference_probability_low > self.reference_probability_high:
            raise ValueError(
                "reference_probability_low must be at most reference_probability_high",
            )
        if self.sanity_status not in SANITY_STATUSES:
            raise ValueError("sanity_status must be pass, watch, or block")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.manual_next_step not in MANUAL_NEXT_STEPS:
            raise ValueError("manual_next_step must be a supported action")
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class ProbabilityEventImpliedProbabilitySanityBandReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    pass_count: int
    watch_count: int
    block_count: int
    pass_ratio: Decimal
    max_band_gap: Decimal
    max_yes_no_sum_gap: Decimal
    max_spread_probability: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ProbabilityEventImpliedProbabilitySanityBandRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "pass_ratio",
            "max_band_gap",
            "max_yes_no_sum_gap",
            "max_spread_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.report_status not in REPORT_STATUSES:
            raise ValueError("report_status must be pass, watch, or block")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_probability_event_implied_probability_sanity_band_report(
    inputs: Iterable[ProbabilityEventImpliedProbabilitySanityBandInput],
    *,
    config_version: str,
    generated_at: datetime,
) -> ProbabilityEventImpliedProbabilitySanityBandReport:
    _require_canonical_string("config_version", config_version)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(sorted((_row_from_input(value) for value in normalized_inputs), key=_row_sort_key))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    return ProbabilityEventImpliedProbabilitySanityBandReport(
        generated_at=_as_utc(generated_at),
        config_version=config_version,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        pass_ratio=_pass_ratio(pass_count=pass_count, row_count=len(rows)),
        max_band_gap=_max_probability(rows, "band_gap"),
        max_yes_no_sum_gap=_max_probability(rows, "yes_no_sum_gap"),
        max_spread_probability=_max_probability(rows, "spread_probability"),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def probability_event_implied_probability_sanity_band_report_payload(
    report: ProbabilityEventImpliedProbabilitySanityBandReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventImpliedProbabilitySanityBandReport:
        raise ValueError(
            "report must be a ProbabilityEventImpliedProbabilitySanityBandReport",
        )
    _validate_report_consistency(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_from_input(
    value: ProbabilityEventImpliedProbabilitySanityBandInput,
) -> ProbabilityEventImpliedProbabilitySanityBandRow:
    yes_no_sum_probability = _sum_decimals((value.yes_probability, value.no_probability))
    yes_no_sum_gap = _abs_decimal(_subtract_decimal(yes_no_sum_probability, ONE))
    reference_mid_probability = _divide_decimal(
        _sum_decimals((value.reference_probability_low, value.reference_probability_high)),
        TWO,
    )
    forecast_reference_mid_gap = _abs_decimal(
        _subtract_decimal(value.forecast_probability, reference_mid_probability),
    )
    band_gap = _band_gap(value)
    check_reason_codes = _check_reason_codes(
        yes_no_sum_gap=yes_no_sum_gap,
        forecast_probability=value.forecast_probability,
        reference_probability_low=value.reference_probability_low,
        reference_probability_high=value.reference_probability_high,
        band_gap=band_gap,
        spread_probability=value.spread_probability,
    )
    sanity_status = _sanity_status(check_reason_codes)
    return ProbabilityEventImpliedProbabilitySanityBandRow(
        event_id=value.event_id,
        market_slug=value.market_slug,
        yes_probability=value.yes_probability,
        no_probability=value.no_probability,
        yes_no_sum_probability=yes_no_sum_probability,
        yes_no_sum_gap=yes_no_sum_gap,
        forecast_probability=value.forecast_probability,
        reference_probability_low=value.reference_probability_low,
        reference_probability_high=value.reference_probability_high,
        reference_mid_probability=reference_mid_probability,
        forecast_reference_mid_gap=forecast_reference_mid_gap,
        band_gap=band_gap,
        spread_probability=value.spread_probability,
        sanity_status=sanity_status,
        reason_codes=_normalize_reason_codes(
            (
                f"implied_probability_sanity_band_{sanity_status}",
                *value.reason_codes,
                *check_reason_codes,
            ),
        ),
        manual_next_step=_manual_next_step(sanity_status),
    )


def _check_reason_codes(
    *,
    yes_no_sum_gap: Decimal,
    forecast_probability: Decimal,
    reference_probability_low: Decimal,
    reference_probability_high: Decimal,
    band_gap: Decimal,
    spread_probability: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if yes_no_sum_gap >= BLOCK_YES_NO_SUM_GAP:
        reasons.append("yes_no_sum_block")
    elif yes_no_sum_gap >= WATCH_YES_NO_SUM_GAP:
        reasons.append("yes_no_sum_watch")
    if forecast_probability > reference_probability_high:
        if band_gap >= BLOCK_BAND_GAP:
            reasons.append("forecast_above_reference_band_block")
        elif band_gap >= WATCH_BAND_GAP:
            reasons.append("forecast_above_reference_band_watch")
    elif forecast_probability < reference_probability_low:
        if band_gap >= BLOCK_BAND_GAP:
            reasons.append("forecast_below_reference_band_block")
        elif band_gap >= WATCH_BAND_GAP:
            reasons.append("forecast_below_reference_band_watch")
    if spread_probability >= BLOCK_SPREAD_PROBABILITY:
        reasons.append("spread_probability_block")
    elif spread_probability >= WATCH_SPREAD_PROBABILITY:
        reasons.append("spread_probability_watch")
    return _normalize_reason_codes(tuple(reasons))


def _sanity_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _manual_next_step(sanity_status: str) -> str:
    if sanity_status == "block":
        return "manual_review_required_before_research_use"
    if sanity_status == "watch":
        return "manual_verify_probability_inputs"
    return "no_manual_action_required"


def _band_gap(value: ProbabilityEventImpliedProbabilitySanityBandInput) -> Decimal:
    if value.forecast_probability > value.reference_probability_high:
        return _subtract_decimal(value.forecast_probability, value.reference_probability_high)
    if value.forecast_probability < value.reference_probability_low:
        return _subtract_decimal(value.reference_probability_low, value.forecast_probability)
    return _quantize(ZERO)


def _row_sort_key(
    row: ProbabilityEventImpliedProbabilitySanityBandRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        0 if row.sanity_status == "block" else 1 if row.sanity_status == "watch" else 2,
        -row.band_gap,
        -row.spread_probability,
        row.market_slug,
        row.event_id,
    )


def _status_count(
    rows: tuple[ProbabilityEventImpliedProbabilitySanityBandRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.sanity_status == status)


def _pass_ratio(*, pass_count: int, row_count: int) -> Decimal:
    if row_count == 0:
        return _quantize(ZERO)
    return _divide_decimal(Decimal(pass_count), Decimal(row_count))


def _max_probability(
    rows: tuple[ProbabilityEventImpliedProbabilitySanityBandRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _report_status(rows: tuple[ProbabilityEventImpliedProbabilitySanityBandRow, ...]) -> str:
    if any(row.sanity_status == "block" for row in rows):
        return "block"
    if any(row.sanity_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ProbabilityEventImpliedProbabilitySanityBandRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "pass":
        return ("implied_probability_sanity_band_pass",)
    return _normalize_reason_codes(
        (
            f"implied_probability_sanity_band_{status}",
            *(
                reason
                for row in rows
                for reason in row.reason_codes
                if reason.endswith(("_watch", "_block"))
                and not reason.startswith("implied_probability_sanity_band_")
            ),
        ),
    )


def _normalize_inputs(
    values: Iterable[ProbabilityEventImpliedProbabilitySanityBandInput],
) -> tuple[ProbabilityEventImpliedProbabilitySanityBandInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(
            "inputs must be an iterable of ProbabilityEventImpliedProbabilitySanityBandInput values",
        )
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of ProbabilityEventImpliedProbabilitySanityBandInput values",
        ) from exc
    for value in normalized:
        if type(value) is not ProbabilityEventImpliedProbabilitySanityBandInput:
            raise ValueError(
                "inputs must contain only ProbabilityEventImpliedProbabilitySanityBandInput values",
            )
        if value.paper_only is not True:
            raise ValueError("inputs must contain paper_only values")
        if value.report_only is not True:
            raise ValueError("inputs must contain report_only values")
        if value.readonly is not True:
            raise ValueError("inputs must contain readonly values")
    return normalized


def _normalize_rows(
    rows: Iterable[ProbabilityEventImpliedProbabilitySanityBandRow],
) -> tuple[ProbabilityEventImpliedProbabilitySanityBandRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ProbabilityEventImpliedProbabilitySanityBandRow:
            raise ValueError(
                "rows must contain ProbabilityEventImpliedProbabilitySanityBandRow values",
            )
        if row.paper_only is not True:
            raise ValueError("rows must contain paper_only values")
        if row.report_only is not True:
            raise ValueError("rows must contain report_only values")
        if row.readonly is not True:
            raise ValueError("rows must contain readonly values")
    return normalized


def _validate_row_consistency(row: ProbabilityEventImpliedProbabilitySanityBandRow) -> None:
    expected_yes_no_sum = _sum_decimals((row.yes_probability, row.no_probability))
    if row.yes_no_sum_probability != expected_yes_no_sum:
        raise ValueError("yes_no_sum_probability must match yes and no probabilities")
    if row.yes_no_sum_gap != _abs_decimal(_subtract_decimal(row.yes_no_sum_probability, ONE)):
        raise ValueError("yes_no_sum_gap must match yes_no_sum_probability")
    expected_mid = _divide_decimal(
        _sum_decimals((row.reference_probability_low, row.reference_probability_high)),
        TWO,
    )
    if row.reference_mid_probability != expected_mid:
        raise ValueError("reference_mid_probability must match reference band")
    if row.forecast_reference_mid_gap != _abs_decimal(
        _subtract_decimal(row.forecast_probability, row.reference_mid_probability),
    ):
        raise ValueError("forecast_reference_mid_gap must match forecast and reference mid")
    validation_input = ProbabilityEventImpliedProbabilitySanityBandInput(
        event_id=row.event_id,
        market_slug=row.market_slug,
        yes_probability=row.yes_probability,
        no_probability=row.no_probability,
        forecast_probability=row.forecast_probability,
        reference_probability_low=row.reference_probability_low,
        reference_probability_high=row.reference_probability_high,
        spread_probability=row.spread_probability,
        reason_codes=(),
    )
    if row.band_gap != _band_gap(validation_input):
        raise ValueError("band_gap must match forecast and reference band")
    expected_reasons = _check_reason_codes(
        yes_no_sum_gap=row.yes_no_sum_gap,
        forecast_probability=row.forecast_probability,
        reference_probability_low=row.reference_probability_low,
        reference_probability_high=row.reference_probability_high,
        band_gap=row.band_gap,
        spread_probability=row.spread_probability,
    )
    expected_status = _sanity_status(expected_reasons)
    if row.sanity_status != expected_status:
        raise ValueError("sanity_status must match reason_codes")
    if row.manual_next_step != _manual_next_step(row.sanity_status):
        raise ValueError("manual_next_step must match sanity_status")
    if not row.reason_codes:
        raise ValueError("reason_codes must include status")
    if row.reason_codes[0] != f"implied_probability_sanity_band_{row.sanity_status}":
        raise ValueError("reason_codes must begin with sanity status")
    for reason in expected_reasons:
        if reason not in row.reason_codes:
            raise ValueError("reason_codes must include derived sanity checks")


def _validate_report_consistency(
    report: ProbabilityEventImpliedProbabilitySanityBandReport,
) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must match rows")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _pass_ratio(
        pass_count=report.pass_count,
        row_count=report.row_count,
    ):
        raise ValueError("pass_ratio must match pass_count and row_count")
    if report.max_band_gap != _max_probability(report.rows, "band_gap"):
        raise ValueError("max_band_gap must match rows")
    if report.max_yes_no_sum_gap != _max_probability(report.rows, "yes_no_sum_gap"):
        raise ValueError("max_yes_no_sum_gap must match rows")
    if report.max_spread_probability != _max_probability(report.rows, "spread_probability"):
        raise ValueError("max_spread_probability must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")


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
