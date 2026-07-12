"""Read-only probability edge sensitivity report.

Pure in-memory Decimal arithmetic for screened probability edges. The module
only produces immutable report objects, public payloads, and digests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


PROBABILITY_EDGE_SENSITIVITY_REPORT_STATUSES = ("pass", "attention", "blocker")
SENSITIVITY_BANDS = PROBABILITY_EDGE_SENSITIVITY_REPORT_STATUSES
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_ROW_REASON_CODES = (
    "adjusted_edge_not_positive_blocker",
    "buffer_load_attention",
    "probability_edge_sensitivity_pass",
    "threshold_margin_negative_blocker",
    "threshold_margin_thin_attention",
)
_REPORT_REASON_CODES = (
    "adjusted_edge_blocker_review",
    "buffer_load_attention_review",
    "probability_edge_sensitivity_report_blocker",
    "probability_edge_sensitivity_report_empty",
    "probability_edge_sensitivity_report_pass",
    "probability_edge_sensitivity_report_attention",
    "threshold_margin_attention_review",
)
_PUBLIC_ROW_FIELDS = frozenset(
    (
        "observed_at",
        "forecast_probability",
        "market_probability",
        "cost_adjusted_threshold_probability",
        "forecast_error_buffer_probability",
        "liquidity_haircut_probability",
        "source_uncertainty_buffer_probability",
        "gross_edge_probability",
        "total_buffer_probability",
        "adjusted_edge_probability",
        "break_even_forecast_probability",
        "safety_margin_probability",
        "sensitivity_band",
        "reason_codes",
        "row_number",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_REPORT_FIELDS = frozenset(
    (
        "generated_at",
        "input_count",
        "pass_count",
        "attention_count",
        "blocker_count",
        "mean_adjusted_edge_probability",
        "min_safety_margin_probability",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "candidate",
    "condition" + "_id",
    "credential",
    "data" + "base",
    "dsn",
    "edge_ref",
    "exec" + "ute",
    "exec" + "ution",
    "li" + "ve",
    "market" + "_id",
    "market" + "_slug",
    "net" + "work",
    "or" + "der",
    "persist",
    "private",
    "question",
    "reco" + "mmend",
    "secret",
    "siz" + "ing",
    "source" + "_text",
    "source" + "_url",
    "table",
    "token",
    "trad" + "e",
    "trad" + "ing",
    "url",
    "wal" + "let",
    "b" + "uy",
    "se" + "ll",
)


@dataclass(frozen=True)
class ProbabilityEdgeSensitivityInput:
    edge_ref: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    cost_adjusted_threshold_probability: Decimal
    forecast_error_buffer_probability: Decimal
    liquidity_haircut_probability: Decimal
    source_uncertainty_buffer_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEdgeSensitivityInput:
            raise ValueError("input must be exactly ProbabilityEdgeSensitivityInput")
        _require_internal_ref("edge_ref", self.edge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "cost_adjusted_threshold_probability",
            "forecast_error_buffer_probability",
            "liquidity_haircut_probability",
            "source_uncertainty_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEdgeSensitivityRow:
    edge_ref: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    cost_adjusted_threshold_probability: Decimal
    forecast_error_buffer_probability: Decimal
    liquidity_haircut_probability: Decimal
    source_uncertainty_buffer_probability: Decimal
    gross_edge_probability: Decimal
    total_buffer_probability: Decimal
    adjusted_edge_probability: Decimal
    break_even_forecast_probability: Decimal
    safety_margin_probability: Decimal
    sensitivity_band: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEdgeSensitivityRow:
            raise ValueError("row must be exactly ProbabilityEdgeSensitivityRow")
        _require_internal_ref("edge_ref", self.edge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "cost_adjusted_threshold_probability",
            "forecast_error_buffer_probability",
            "liquidity_haircut_probability",
            "source_uncertainty_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_buffer_probability",
            _normalize_probability("total_buffer_probability", self.total_buffer_probability),
        )
        for field_name in (
            "gross_edge_probability",
            "adjusted_edge_probability",
            "break_even_forecast_probability",
            "safety_margin_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_sensitivity_band("sensitivity_band", self.sensitivity_band)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ProbabilityEdgeSensitivityReport:
    generated_at: datetime
    input_count: Decimal
    pass_count: Decimal
    attention_count: Decimal
    blocker_count: Decimal
    mean_adjusted_edge_probability: Decimal
    min_safety_margin_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ProbabilityEdgeSensitivityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEdgeSensitivityReport:
            raise ValueError("report must be exactly ProbabilityEdgeSensitivityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "input_count",
            "pass_count",
            "attention_count",
            "blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_adjusted_edge_probability",
            "min_safety_margin_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_probability_edge_sensitivity_report(
    inputs: Iterable[ProbabilityEdgeSensitivityInput],
    *,
    generated_at: datetime,
) -> ProbabilityEdgeSensitivityReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, generated_at=generated_at_utc) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ProbabilityEdgeSensitivityReport(
        generated_at=generated_at_utc,
        input_count=_count(len(rows)),
        pass_count=_band_count(rows, "pass"),
        attention_count=_band_count(rows, "attention"),
        blocker_count=_band_count(rows, "blocker"),
        mean_adjusted_edge_probability=_mean(
            tuple(row.adjusted_edge_probability for row in rows),
        ),
        min_safety_margin_probability=_min_decimal(
            tuple(row.safety_margin_probability for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def probability_edge_sensitivity_report_payload(
    report: ProbabilityEdgeSensitivityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ProbabilityEdgeSensitivityReport:
        _require_hard_flags("report", report)
        _verify_digest(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ProbabilityEdgeSensitivityReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def probability_edge_sensitivity_report_digest(
    report: ProbabilityEdgeSensitivityReport,
) -> dict[str, Any]:
    payload = probability_edge_sensitivity_report_payload(report)
    diagnostic_reason_codes = [
        value
        for value in payload["reason_codes"]
        if not value.startswith("probability_edge_sensitivity_report_")
    ]
    return {
        "generated_at": payload["generated_at"],
        "status": payload["status"],
        "input_count": payload["input_count"],
        "pass_count": payload["pass_count"],
        "attention_count": payload["attention_count"],
        "blocker_count": payload["blocker_count"],
        "mean_adjusted_edge_probability": payload["mean_adjusted_edge_probability"],
        "min_safety_margin_probability": payload["min_safety_margin_probability"],
        "reason_codes": diagnostic_reason_codes or payload["reason_codes"],
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
        "derived_validation_digest": payload["derived_validation_digest"],
    }


def _row_from_input(
    value: ProbabilityEdgeSensitivityInput,
    *,
    generated_at: datetime,
) -> ProbabilityEdgeSensitivityRow:
    if value.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gross_edge_probability = _subtract_decimal(
        value.forecast_probability,
        value.market_probability,
    )
    total_buffer_probability = _sum_decimals(
        (
            value.forecast_error_buffer_probability,
            value.liquidity_haircut_probability,
            value.source_uncertainty_buffer_probability,
        ),
    )
    adjusted_edge_probability = _subtract_decimal(
        gross_edge_probability,
        total_buffer_probability,
    )
    break_even_forecast_probability = _add_decimal(
        value.cost_adjusted_threshold_probability,
        total_buffer_probability,
    )
    safety_margin_probability = _subtract_decimal(
        value.forecast_probability,
        break_even_forecast_probability,
    )
    sensitivity_band = _sensitivity_band(
        adjusted_edge_probability=adjusted_edge_probability,
        safety_margin_probability=safety_margin_probability,
    )
    return ProbabilityEdgeSensitivityRow(
        edge_ref=value.edge_ref,
        observed_at=value.observed_at,
        forecast_probability=value.forecast_probability,
        market_probability=value.market_probability,
        cost_adjusted_threshold_probability=value.cost_adjusted_threshold_probability,
        forecast_error_buffer_probability=value.forecast_error_buffer_probability,
        liquidity_haircut_probability=value.liquidity_haircut_probability,
        source_uncertainty_buffer_probability=value.source_uncertainty_buffer_probability,
        gross_edge_probability=gross_edge_probability,
        total_buffer_probability=total_buffer_probability,
        adjusted_edge_probability=adjusted_edge_probability,
        break_even_forecast_probability=break_even_forecast_probability,
        safety_margin_probability=safety_margin_probability,
        sensitivity_band=sensitivity_band,
        reason_codes=_row_reason_codes(
            sensitivity_band=sensitivity_band,
            adjusted_edge_probability=adjusted_edge_probability,
            safety_margin_probability=safety_margin_probability,
            total_buffer_probability=total_buffer_probability,
        ),
    )


def _sensitivity_band(
    *,
    adjusted_edge_probability: Decimal,
    safety_margin_probability: Decimal,
) -> str:
    if adjusted_edge_probability <= ZERO or safety_margin_probability < ZERO:
        return "blocker"
    if safety_margin_probability <= Decimal("0.010000"):
        return "attention"
    return "pass"


def _row_reason_codes(
    *,
    sensitivity_band: str,
    adjusted_edge_probability: Decimal,
    safety_margin_probability: Decimal,
    total_buffer_probability: Decimal,
) -> tuple[str, ...]:
    if sensitivity_band == "pass":
        return ("probability_edge_sensitivity_pass",)
    reasons: list[str] = []
    if adjusted_edge_probability <= ZERO:
        reasons.append("adjusted_edge_not_positive_blocker")
    if safety_margin_probability < ZERO:
        reasons.append("threshold_margin_negative_blocker")
    elif safety_margin_probability <= Decimal("0.010000"):
        reasons.append("threshold_margin_thin_attention")
    if total_buffer_probability >= Decimal("0.030000"):
        reasons.append("buffer_load_attention")
    return tuple(sorted(dict.fromkeys(reasons)))


def _report_reason_codes(rows: tuple[ProbabilityEdgeSensitivityRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("probability_edge_sensitivity_report_empty",)
    reasons: list[str] = []
    if any(row.sensitivity_band == "blocker" for row in rows):
        reasons.append("probability_edge_sensitivity_report_blocker")
    elif any(row.sensitivity_band == "attention" for row in rows):
        reasons.append("probability_edge_sensitivity_report_attention")
    else:
        reasons.append("probability_edge_sensitivity_report_pass")
    if any("adjusted_edge_not_positive_blocker" in row.reason_codes for row in rows):
        reasons.append("adjusted_edge_blocker_review")
    if any(
        reason_code in row.reason_codes
        for row in rows
        for reason_code in (
            "threshold_margin_negative_blocker",
            "threshold_margin_thin_attention",
        )
    ):
        reasons.append("threshold_margin_attention_review")
    if any("buffer_load_attention" in row.reason_codes for row in rows):
        reasons.append("buffer_load_attention_review")
    return tuple(sorted(dict.fromkeys(reasons)))


def _report_status(rows: tuple[ProbabilityEdgeSensitivityRow, ...]) -> str:
    if not rows or any(row.sensitivity_band == "blocker" for row in rows):
        return "blocker"
    if any(row.sensitivity_band == "attention" for row in rows):
        return "attention"
    return "pass"


def _reason_code_counts(
    rows: tuple[ProbabilityEdgeSensitivityRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        return (("probability_edge_sensitivity_report_empty", _count(1)),)
    counts = []
    all_codes = sorted(
        set(report_reason_codes).union(
            reason_code for row in rows for reason_code in row.reason_codes
        ),
    )
    for reason_code in all_codes:
        if reason_code in _REPORT_REASON_CODES:
            count = _count(1)
        else:
            count = _count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            )
        counts.append((reason_code, count))
    return tuple(counts)


def _public_report_payload(report: ProbabilityEdgeSensitivityReport) -> dict[str, Any]:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row) for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    _verify_public_payload_integrity(public_payload)
    return public_payload


def _public_row_payload(row_number: int, row: ProbabilityEdgeSensitivityRow) -> dict[str, Any]:
    payload = asdict(row)
    payload.pop("edge_ref", None)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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


def _normalize_inputs(
    inputs: Iterable[ProbabilityEdgeSensitivityInput],
) -> tuple[ProbabilityEdgeSensitivityInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable of ProbabilityEdgeSensitivityInput")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ProbabilityEdgeSensitivityInput:
            raise ValueError("inputs must contain ProbabilityEdgeSensitivityInput")
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: tuple[ProbabilityEdgeSensitivityRow, ...],
) -> tuple[ProbabilityEdgeSensitivityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ProbabilityEdgeSensitivityRow:
            raise ValueError("rows must contain ProbabilityEdgeSensitivityRow")
        _require_hard_flags("row", row)
        _verify_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by sensitivity severity")
    return rows


def _normalize_reason_code_counts(
    value: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = []
    previous = ""
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count tuples")
        reason_code, count = item
        _require_reason_code("reason_code", reason_code, (*_ROW_REASON_CODES, *_REPORT_REASON_CODES))
        if previous and reason_code <= previous:
            raise ValueError("reason_code_counts must be sorted")
        previous = reason_code
        normalized.append((reason_code, _normalize_count("count", count)))
    return tuple(normalized)


def _row_sort_key(row: ProbabilityEdgeSensitivityRow) -> tuple[int, Decimal, str]:
    return (
        {"blocker": 0, "attention": 1, "pass": 2}[row.sensitivity_band],
        -row.safety_margin_probability,
        row.edge_ref,
    )


def _band_count(rows: tuple[ProbabilityEdgeSensitivityRow, ...], band: str) -> Decimal:
    return _count(sum(1 for row in rows if row.sensitivity_band == band))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize(ZERO)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize(ZERO)
    return _quantize(min(values))


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return _quantize(total)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("division denominator must be nonzero")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer-valued Decimal")
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_internal_ref(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if len(value) > 128:
        raise ValueError(f"{name} must be concise")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "-"):
            raise ValueError(f"{name} must be lowercase slug text")


def _require_reason_code(name: str, value: object, supported: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in supported:
        raise ValueError(f"{name} must be a supported reason code")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized = tuple(sorted(dict.fromkeys(value)))
    for reason_code in normalized:
        _require_reason_code(f"{name} item", reason_code, supported)
    return normalized


def _require_status(name: str, value: object) -> None:
    if value not in PROBABILITY_EDGE_SENSITIVITY_REPORT_STATUSES:
        raise ValueError(f"{name} must be a known report status")


def _require_sensitivity_band(name: str, value: object) -> None:
    if value not in SENSITIVITY_BANDS:
        raise ValueError(f"{name} must be a known sensitivity band")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _validate_row_consistency(row: ProbabilityEdgeSensitivityRow) -> None:
    expected_total_buffer = _sum_decimals(
        (
            row.forecast_error_buffer_probability,
            row.liquidity_haircut_probability,
            row.source_uncertainty_buffer_probability,
        ),
    )
    if row.total_buffer_probability != expected_total_buffer:
        raise ValueError("total_buffer_probability does not match inputs")
    if row.gross_edge_probability != _subtract_decimal(
        row.forecast_probability,
        row.market_probability,
    ):
        raise ValueError("gross_edge_probability does not match inputs")
    if row.adjusted_edge_probability != _subtract_decimal(
        row.gross_edge_probability,
        row.total_buffer_probability,
    ):
        raise ValueError("adjusted_edge_probability does not match inputs")
    if row.break_even_forecast_probability != _add_decimal(
        row.cost_adjusted_threshold_probability,
        row.total_buffer_probability,
    ):
        raise ValueError("break_even_forecast_probability does not match inputs")
    if row.safety_margin_probability != _subtract_decimal(
        row.forecast_probability,
        row.break_even_forecast_probability,
    ):
        raise ValueError("safety_margin_probability does not match inputs")
    expected_band = _sensitivity_band(
        adjusted_edge_probability=row.adjusted_edge_probability,
        safety_margin_probability=row.safety_margin_probability,
    )
    if row.sensitivity_band != expected_band:
        raise ValueError("sensitivity_band does not match derived fields")
    expected_reasons = _row_reason_codes(
        sensitivity_band=row.sensitivity_band,
        adjusted_edge_probability=row.adjusted_edge_probability,
        safety_margin_probability=row.safety_margin_probability,
        total_buffer_probability=row.total_buffer_probability,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match derived fields")


def _validate_report_consistency(report: ProbabilityEdgeSensitivityReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count does not match rows")
    if report.pass_count != _band_count(rows, "pass"):
        raise ValueError("pass_count does not match rows")
    if report.attention_count != _band_count(rows, "attention"):
        raise ValueError("attention_count does not match rows")
    if report.blocker_count != _band_count(rows, "blocker"):
        raise ValueError("blocker_count does not match rows")
    if report.mean_adjusted_edge_probability != _mean(
        tuple(row.adjusted_edge_probability for row in rows),
    ):
        raise ValueError("mean_adjusted_edge_probability does not match rows")
    if report.min_safety_margin_probability != _min_decimal(
        tuple(row.safety_margin_probability for row in rows),
    ):
        raise ValueError("min_safety_margin_probability does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    reason_codes = _report_reason_codes(rows)
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(rows, reason_codes):
        raise ValueError("reason_code_counts do not match rows")


def _apply_or_verify_digest(value: ProbabilityEdgeSensitivityRow | ProbabilityEdgeSensitivityReport) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(value: ProbabilityEdgeSensitivityRow | ProbabilityEdgeSensitivityReport) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(value: ProbabilityEdgeSensitivityRow | ProbabilityEdgeSensitivityReport) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8",
    )
    return sha256(encoded).hexdigest()


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{name} must be a sha256 hex digest")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_public_keys("payload", payload, _PUBLIC_REPORT_FIELDS)
    _require_public_datetime("payload.generated_at", payload.get("generated_at"))
    for field_name in (
        "input_count",
        "pass_count",
        "attention_count",
        "blocker_count",
    ):
        _normalize_nonnegative_decimal_string(f"payload.{field_name}", payload.get(field_name))
    for field_name in (
        "mean_adjusted_edge_probability",
        "min_safety_margin_probability",
    ):
        _normalize_decimal_string(f"payload.{field_name}", payload.get(field_name))
    _require_status("payload.status", payload.get("status"))
    _normalize_public_reason_codes(
        "payload.reason_codes",
        payload.get("reason_codes"),
        _REPORT_REASON_CODES,
    )
    _validate_public_reason_code_counts(payload.get("reason_code_counts"))
    _validate_public_rows(payload.get("rows"))
    _require_digest("payload.derived_validation_digest", payload.get("derived_validation_digest"))
    _require_hard_flags("payload", _DictFlags(payload))


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.reason_code_counts must be a public list")
    previous = ""
    for index, item in enumerate(value):
        if type(item) is not list or len(item) != 2:
            raise ValueError("payload.reason_code_counts must contain public tuples")
        reason_code = item[0]
        _require_reason_code(
            f"payload.reason_code_counts[{index}].reason_code",
            reason_code,
            (*_ROW_REASON_CODES, *_REPORT_REASON_CODES),
        )
        if previous and reason_code <= previous:
            raise ValueError("payload.reason_code_counts must be sorted")
        previous = reason_code
        _normalize_nonnegative_decimal_string(
            f"payload.reason_code_counts[{index}].count",
            item[1],
        )


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.rows must be a public list")
    for index, item in enumerate(value):
        if type(item) is not dict:
            raise ValueError("payload.rows must contain public objects")
        label = f"payload.rows[{index}]"
        _require_public_keys(label, item, _PUBLIC_ROW_FIELDS)
        _require_public_datetime(f"{label}.observed_at", item.get("observed_at"))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "cost_adjusted_threshold_probability",
            "forecast_error_buffer_probability",
            "liquidity_haircut_probability",
            "source_uncertainty_buffer_probability",
            "total_buffer_probability",
        ):
            _normalize_probability_decimal_string(f"{label}.{field_name}", item.get(field_name))
        for field_name in (
            "gross_edge_probability",
            "adjusted_edge_probability",
            "break_even_forecast_probability",
            "safety_margin_probability",
            "row_number",
        ):
            _normalize_decimal_string(f"{label}.{field_name}", item.get(field_name))
        _require_sensitivity_band(f"{label}.sensitivity_band", item.get("sensitivity_band"))
        _normalize_public_reason_codes(
            f"{label}.reason_codes",
            item.get("reason_codes"),
            _ROW_REASON_CODES,
        )
        _require_digest(
            f"{label}.derived_validation_digest",
            item.get("derived_validation_digest"),
        )
        _require_hard_flags(label, _DictFlags(item))


def _require_public_keys(name: str, value: dict[str, Any], supported: frozenset[str]) -> None:
    keys = frozenset(value)
    if keys != supported:
        raise ValueError(f"{name} must contain only public diagnostic fields")


def _normalize_public_reason_codes(
    name: str,
    value: object,
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a public list")
    return _normalize_reason_codes(name, tuple(value), supported)


def _normalize_probability_decimal_string(name: str, value: object) -> Decimal:
    return _normalize_probability(name, _decimal_from_public_string(name, value))


def _normalize_nonnegative_decimal_string(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_string(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal_string(name: str, value: object) -> Decimal:
    return _normalize_decimal(name, _decimal_from_public_string(name, value))


def _decimal_from_public_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:  # pragma: no cover - defensive normalizer
        raise ValueError(f"{name} must be a Decimal string") from exc
    if format(parsed, "f") != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return parsed


def _require_public_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    return _as_utc(name, parsed)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _validate_public_payload_schema(payload)
    for index, row in enumerate(payload.get("rows", ())):
        expected = _public_payload_digest(row)
        if row.get("derived_validation_digest") != expected:
            raise ValueError(
                f"payload.rows[{index}].derived_validation_digest does not match",
            )
    expected = _public_payload_digest(payload)
    if payload.get("derived_validation_digest") != expected:
        raise ValueError("payload.derived_validation_digest does not match")


def _reject_unsafe_public_payload(name: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{name} contains unsafe public field")
            _reject_unsafe_public_payload(f"{name}.{key}", item)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{name}[{index}]", item)
    elif isinstance(value, str) and _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} contains unsafe public content")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "PROBABILITY_EDGE_SENSITIVITY_REPORT_STATUSES",
    "ProbabilityEdgeSensitivityInput",
    "ProbabilityEdgeSensitivityReport",
    "ProbabilityEdgeSensitivityRow",
    "build_probability_edge_sensitivity_report",
    "probability_edge_sensitivity_report_digest",
    "probability_edge_sensitivity_report_payload",
)
