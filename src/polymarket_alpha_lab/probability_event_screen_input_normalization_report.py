"""Read-only probability event screen input normalization report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from polymarket_alpha_lab.probability_event_screen_contract import (
    ProbabilityEventScreen,
)


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUSES = frozenset(("complete_consistent", "incomplete", "inconsistent"))
_MANUAL_NEXT_STEP_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_REASON_CODE_SEQUENCE = (
    "yes_no_executable_probability_mismatch",
    "market_probability_mismatch",
    "gross_edge_probability_mismatch",
    "cost_threshold_probability_mismatch",
    "manual_next_step_missing",
    "phase_flags_not_readonly",
)


@dataclass(frozen=True)
class ProbabilityEventScreenInputNormalizationRow:
    event_ref: str
    market_ref: str
    direction: str
    normalization_status: str
    reason_codes: tuple[str, ...]
    yes_executable_probability: Decimal
    no_executable_probability: Decimal
    forecast_probability: Decimal
    market_probability: Decimal
    gross_edge_probability: Decimal
    total_cost_probability: Decimal
    cost_adjusted_threshold_probability: Decimal
    edge_to_threshold_probability: Decimal
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "event_ref",
            "market_ref",
            "direction",
            "normalization_status",
            "manual_next_step",
        ):
            if type(getattr(self, field_name)) is not str:
                raise ValueError(f"{field_name} must be a string")
        if self.direction not in ("yes", "no"):
            raise ValueError("direction must be yes or no")
        if self.normalization_status not in _STATUSES:
            raise ValueError("normalization_status must be supported")
        if not _MANUAL_NEXT_STEP_RE.fullmatch(self.manual_next_step):
            raise ValueError("manual_next_step must be a canonical snake_case label")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "yes_executable_probability",
            "no_executable_probability",
            "forecast_probability",
            "market_probability",
            "gross_edge_probability",
            "total_cost_probability",
            "cost_adjusted_threshold_probability",
            "edge_to_threshold_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ProbabilityEventScreenInputNormalizationReport:
    rows: tuple[ProbabilityEventScreenInputNormalizationRow, ...]
    normalization_ready: bool
    screen_count: Decimal
    complete_consistent_count: Decimal
    incomplete_count: Decimal
    inconsistent_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ProbabilityEventScreenInputNormalizationRow:
                raise ValueError(
                    "rows must contain ProbabilityEventScreenInputNormalizationRow",
                )
        if type(self.normalization_ready) is not bool:
            raise ValueError("normalization_ready must be a bool")
        for field_name in (
            "screen_count",
            "complete_consistent_count",
            "incomplete_count",
            "inconsistent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _payload_without_digest(self)
        payload["digest"] = self.digest
        return payload

    @property
    def digest(self) -> str:
        canonical = json.dumps(
            _payload_without_digest(self),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_probability_event_screen_input_normalization_report(
    screens: Sequence[ProbabilityEventScreen],
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenInputNormalizationReport:
    if isinstance(screens, (str, bytes)) or not isinstance(screens, Sequence):
        raise ValueError("screens must be a sequence")
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    rows: list[ProbabilityEventScreenInputNormalizationRow] = []
    for screen in screens:
        if type(screen) is not ProbabilityEventScreen:
            raise ValueError("screen must be a ProbabilityEventScreen")
        _require_hard_flags("screen", screen)
        rows.append(_row_from_screen(screen))
    row_tuple = tuple(rows)
    complete_count = _count(
        row for row in row_tuple if row.normalization_status == "complete_consistent"
    )
    incomplete_count = _count(
        row for row in row_tuple if row.normalization_status == "incomplete"
    )
    inconsistent_count = _count(
        row for row in row_tuple if row.normalization_status == "inconsistent"
    )
    return ProbabilityEventScreenInputNormalizationReport(
        rows=row_tuple,
        normalization_ready=bool(row_tuple) and incomplete_count == _ZERO and inconsistent_count == _ZERO,
        screen_count=_quantize(Decimal(len(row_tuple))),
        complete_consistent_count=complete_count,
        incomplete_count=incomplete_count,
        inconsistent_count=inconsistent_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_screen_input_normalization_report_payload(
    report: ProbabilityEventScreenInputNormalizationReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventScreenInputNormalizationReport:
        raise ValueError(
            "report must be a ProbabilityEventScreenInputNormalizationReport",
        )
    return report.public_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _row_from_screen(
    screen: ProbabilityEventScreen,
) -> ProbabilityEventScreenInputNormalizationRow:
    reason_codes = _row_reason_codes(
        direction=screen.direction,
        yes_executable_probability=screen.yes_executable_probability,
        no_executable_probability=screen.no_executable_probability,
        forecast_probability=screen.forecast_probability,
        market_probability=screen.market_probability,
        gross_edge_probability=screen.gross_edge_probability,
        cost_adjusted_threshold_probability=screen.cost_adjusted_threshold_probability,
        edge_to_threshold_probability=screen.edge_to_threshold_probability,
        manual_next_step=screen.manual_next_step,
        paper_only=screen.paper_only,
        report_only=screen.report_only,
        readonly=screen.readonly,
    )
    return ProbabilityEventScreenInputNormalizationRow(
        event_ref=screen.event_ref,
        market_ref=screen.market_ref,
        direction=screen.direction,
        normalization_status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
        yes_executable_probability=screen.yes_executable_probability,
        no_executable_probability=screen.no_executable_probability,
        forecast_probability=screen.forecast_probability,
        market_probability=screen.market_probability,
        gross_edge_probability=screen.gross_edge_probability,
        total_cost_probability=screen.total_cost_probability,
        cost_adjusted_threshold_probability=screen.cost_adjusted_threshold_probability,
        edge_to_threshold_probability=screen.edge_to_threshold_probability,
        manual_next_step=screen.manual_next_step,
        paper_only=screen.paper_only,
        report_only=screen.report_only,
        readonly=screen.readonly,
    )


def _row_reason_codes(
    *,
    direction: str,
    yes_executable_probability: Decimal,
    no_executable_probability: Decimal,
    forecast_probability: Decimal,
    market_probability: Decimal,
    gross_edge_probability: Decimal,
    cost_adjusted_threshold_probability: Decimal,
    edge_to_threshold_probability: Decimal,
    manual_next_step: str,
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if no_executable_probability != _ONE - yes_executable_probability:
        reasons.append("yes_no_executable_probability_mismatch")
    if market_probability != yes_executable_probability:
        reasons.append("market_probability_mismatch")
    expected_gross_edge = (
        forecast_probability - market_probability
        if direction == "yes"
        else market_probability - forecast_probability
    )
    if gross_edge_probability != expected_gross_edge:
        reasons.append("gross_edge_probability_mismatch")
    expected_edge_to_threshold = (
        forecast_probability - cost_adjusted_threshold_probability
        if direction == "yes"
        else cost_adjusted_threshold_probability - forecast_probability
    )
    if edge_to_threshold_probability != expected_edge_to_threshold:
        reasons.append("cost_threshold_probability_mismatch")
    if not _MANUAL_NEXT_STEP_RE.fullmatch(manual_next_step):
        reasons.append("manual_next_step_missing")
    if paper_only is not True or report_only is not True or readonly is not True:
        reasons.append("phase_flags_not_readonly")
    return _normalize_reason_codes(reasons)


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        return "complete_consistent"
    if reason_codes == ("manual_next_step_missing",):
        return "incomplete"
    return "inconsistent"


def _validate_row_consistency(row: ProbabilityEventScreenInputNormalizationRow) -> None:
    if row.no_executable_probability != _ONE - row.yes_executable_probability:
        raise ValueError(
            "no_executable_probability must equal 1 - yes_executable_probability",
        )
    if row.market_probability != row.yes_executable_probability:
        raise ValueError("market_probability must equal yes_executable_probability")
    expected_gross_edge = (
        row.forecast_probability - row.market_probability
        if row.direction == "yes"
        else row.market_probability - row.forecast_probability
    )
    if row.gross_edge_probability != expected_gross_edge:
        raise ValueError("gross_edge_probability must match direction")
    expected_edge_to_threshold = (
        row.forecast_probability - row.cost_adjusted_threshold_probability
        if row.direction == "yes"
        else row.cost_adjusted_threshold_probability - row.forecast_probability
    )
    if row.edge_to_threshold_probability != expected_edge_to_threshold:
        raise ValueError(
            "cost_adjusted_threshold_probability must match edge_to_threshold_probability",
        )
    expected_reasons = _row_reason_codes(
        direction=row.direction,
        yes_executable_probability=row.yes_executable_probability,
        no_executable_probability=row.no_executable_probability,
        forecast_probability=row.forecast_probability,
        market_probability=row.market_probability,
        gross_edge_probability=row.gross_edge_probability,
        cost_adjusted_threshold_probability=row.cost_adjusted_threshold_probability,
        edge_to_threshold_probability=row.edge_to_threshold_probability,
        manual_next_step=row.manual_next_step,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row inputs")
    expected_status = _status_from_reasons(expected_reasons)
    if row.normalization_status != expected_status:
        raise ValueError("normalization_status must match row inputs")


def _validate_report_consistency(
    report: ProbabilityEventScreenInputNormalizationReport,
) -> None:
    expected_screen_count = _quantize(Decimal(len(report.rows)))
    expected_complete_count = _count(
        row for row in report.rows if row.normalization_status == "complete_consistent"
    )
    expected_incomplete_count = _count(
        row for row in report.rows if row.normalization_status == "incomplete"
    )
    expected_inconsistent_count = _count(
        row for row in report.rows if row.normalization_status == "inconsistent"
    )
    if report.screen_count != expected_screen_count:
        raise ValueError("screen_count must match rows")
    if report.complete_consistent_count != expected_complete_count:
        raise ValueError("complete_consistent_count must match rows")
    if report.incomplete_count != expected_incomplete_count:
        raise ValueError("incomplete_count must match rows")
    if report.inconsistent_count != expected_inconsistent_count:
        raise ValueError("inconsistent_count must match rows")
    expected_ready = (
        bool(report.rows)
        and expected_incomplete_count == _ZERO
        and expected_inconsistent_count == _ZERO
    )
    if report.normalization_ready is not expected_ready:
        raise ValueError("normalization_ready must match rows")


def _count(values: Any) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in values)))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _payload_without_digest(
    report: ProbabilityEventScreenInputNormalizationReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "ProbabilityEventScreenInputNormalizationReport",
    "ProbabilityEventScreenInputNormalizationRow",
    "build_probability_event_screen_input_normalization_report",
    "probability_event_screen_input_normalization_report_payload",
)
