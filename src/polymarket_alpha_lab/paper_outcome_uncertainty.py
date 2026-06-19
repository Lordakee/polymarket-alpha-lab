"""Paper-only outcome-definition uncertainty reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)

ACTIONS = ("recommend", "watch", "reject")
SIDES = ("yes", "no")
UNCERTAINTY_STATUSES = ("clear", "watch", "blocked")
STATUS_PRIORITY = {"clear": 0, "watch": 1, "blocked": 2}


@dataclass(frozen=True)
class PaperOutcomeUncertaintyInput:
    market_slug: str
    question: str
    side: str
    action: str
    net_probability_edge: Decimal
    ambiguity_score: Decimal
    has_clear_resolution_source: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("side", self.side)
        _require_action("action", self.action)
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_probability("ambiguity_score", self.ambiguity_score),
        )
        _require_bool(
            "has_clear_resolution_source",
            self.has_clear_resolution_source,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperOutcomeUncertaintyConfig:
    config_version: str
    max_ambiguity_score: Decimal
    ambiguity_penalty_multiplier: Decimal
    missing_source_penalty_per_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_ambiguity_score",
            _normalize_probability("max_ambiguity_score", self.max_ambiguity_score),
        )
        object.__setattr__(
            self,
            "ambiguity_penalty_multiplier",
            _normalize_nonnegative_decimal(
                "ambiguity_penalty_multiplier",
                self.ambiguity_penalty_multiplier,
            ),
        )
        object.__setattr__(
            self,
            "missing_source_penalty_per_share",
            _normalize_nonnegative_decimal(
                "missing_source_penalty_per_share",
                self.missing_source_penalty_per_share,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperOutcomeUncertaintyRow:
    market_slug: str
    question: str
    side: str
    action: str
    net_probability_edge: Decimal
    ambiguity_score: Decimal
    has_clear_resolution_source: bool
    uncertainty_status: str
    uncertainty_cost_per_share: Decimal
    adjusted_net_probability_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("side", self.side)
        _require_action("action", self.action)
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_probability("ambiguity_score", self.ambiguity_score),
        )
        _require_bool(
            "has_clear_resolution_source",
            self.has_clear_resolution_source,
        )
        _require_uncertainty_status("uncertainty_status", self.uncertainty_status)
        object.__setattr__(
            self,
            "uncertainty_cost_per_share",
            _normalize_nonnegative_decimal(
                "uncertainty_cost_per_share",
                self.uncertainty_cost_per_share,
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
class PaperOutcomeUncertaintyReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    clear_count: int
    watch_count: int
    blocked_count: int
    rows: tuple[PaperOutcomeUncertaintyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "clear_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_outcome_uncertainty_report(
    inputs: Iterable[PaperOutcomeUncertaintyInput],
    *,
    config: PaperOutcomeUncertaintyConfig,
    generated_at: datetime,
) -> PaperOutcomeUncertaintyReport:
    if type(config) is not PaperOutcomeUncertaintyConfig:
        raise ValueError("config must be a PaperOutcomeUncertaintyConfig")
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
    return PaperOutcomeUncertaintyReport(
        generated_at=_as_utc(generated_at),
        config_version=config.config_version,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        rows=rows,
    )


def _row_from_input(
    value: PaperOutcomeUncertaintyInput,
    *,
    config: PaperOutcomeUncertaintyConfig,
) -> PaperOutcomeUncertaintyRow:
    uncertainty_cost_per_share = _uncertainty_cost_per_share(value, config)
    adjusted_net_probability_edge = _subtract_decimal(
        value.net_probability_edge,
        uncertainty_cost_per_share,
    )
    uncertainty_status = _uncertainty_status(value, config)
    reason_codes = _reason_codes_for(
        value,
        uncertainty_status=uncertainty_status,
    )

    return PaperOutcomeUncertaintyRow(
        market_slug=value.market_slug,
        question=value.question,
        side=value.side,
        action=value.action,
        net_probability_edge=value.net_probability_edge,
        ambiguity_score=value.ambiguity_score,
        has_clear_resolution_source=value.has_clear_resolution_source,
        uncertainty_status=uncertainty_status,
        uncertainty_cost_per_share=uncertainty_cost_per_share,
        adjusted_net_probability_edge=adjusted_net_probability_edge,
        reason_codes=reason_codes,
    )


def _uncertainty_cost_per_share(
    value: PaperOutcomeUncertaintyInput,
    config: PaperOutcomeUncertaintyConfig,
) -> Decimal:
    ambiguity_cost = _multiply_decimal(
        value.ambiguity_score,
        config.ambiguity_penalty_multiplier,
    )
    if value.has_clear_resolution_source is True:
        return ambiguity_cost
    return _add_decimal(ambiguity_cost, config.missing_source_penalty_per_share)


def _uncertainty_status(
    value: PaperOutcomeUncertaintyInput,
    config: PaperOutcomeUncertaintyConfig,
) -> str:
    if value.ambiguity_score > config.max_ambiguity_score:
        return "blocked"
    if value.ambiguity_score > ZERO:
        return "watch"
    if value.has_clear_resolution_source is not True:
        return "watch"
    return "clear"


def _reason_codes_for(
    value: PaperOutcomeUncertaintyInput,
    *,
    uncertainty_status: str,
) -> tuple[str, ...]:
    clear_codes = (
        ("outcome_definition_clear",)
        if uncertainty_status == "clear"
        else ()
    )
    ambiguity_codes = (
        ("ambiguous_outcome_definition",)
        if value.ambiguity_score > ZERO
        else ()
    )
    missing_source_codes = (
        ("missing_clear_resolution_source",)
        if value.has_clear_resolution_source is not True
        else ()
    )
    blocking_codes = (
        ("ambiguity_score_above_max",)
        if uncertainty_status == "blocked"
        else ()
    )
    return _normalize_reason_codes(
        (
            *value.reason_codes,
            *clear_codes,
            *ambiguity_codes,
            *missing_source_codes,
            *blocking_codes,
        ),
    )


def _normalize_inputs(
    values: Iterable[PaperOutcomeUncertaintyInput],
) -> tuple[PaperOutcomeUncertaintyInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of PaperOutcomeUncertaintyInput values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of PaperOutcomeUncertaintyInput values",
        ) from exc
    for value in normalized:
        if type(value) is not PaperOutcomeUncertaintyInput:
            raise ValueError(
                "inputs must contain only PaperOutcomeUncertaintyInput values",
            )
        _require_safety_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[PaperOutcomeUncertaintyRow],
) -> tuple[PaperOutcomeUncertaintyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperOutcomeUncertaintyRow:
            raise ValueError("rows must contain PaperOutcomeUncertaintyRow values")
        _require_safety_flags(row)
    return normalized


def _validate_row_consistency(row: PaperOutcomeUncertaintyRow) -> None:
    if row.uncertainty_status == "clear":
        if row.ambiguity_score != _quantize(ZERO):
            raise ValueError("clear rows must have zero ambiguity_score")
        if row.has_clear_resolution_source is not True:
            raise ValueError("clear rows require has_clear_resolution_source")
        if row.uncertainty_cost_per_share != _quantize(ZERO):
            raise ValueError("uncertainty_cost_per_share must be zero for clear rows")
    if row.uncertainty_status == "blocked" and row.ambiguity_score <= ZERO:
        raise ValueError("blocked rows require positive ambiguity_score")
    expected_adjusted_net_probability_edge = _subtract_decimal(
        row.net_probability_edge,
        row.uncertainty_cost_per_share,
    )
    if row.adjusted_net_probability_edge != expected_adjusted_net_probability_edge:
        raise ValueError("adjusted_net_probability_edge must match uncertainty cost")


def _validate_report_consistency(report: PaperOutcomeUncertaintyReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must equal rows length")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must equal rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must equal rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must equal rows")
    if report.row_count != (
        report.clear_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("row_count must equal uncertainty status counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _row_sort_key(
    row: PaperOutcomeUncertaintyRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_PRIORITY[row.uncertainty_status],
        -row.adjusted_net_probability_edge,
        row.uncertainty_cost_per_share,
        row.market_slug,
        row.side,
    )


def _status_count(
    rows: Iterable[PaperOutcomeUncertaintyRow],
    uncertainty_status: str,
) -> int:
    return sum(1 for row in rows if row.uncertainty_status == uncertainty_status)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


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


def _require_side(field_name: str, value: str) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_action(field_name: str, value: str) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_uncertainty_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in UNCERTAINTY_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


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


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "PaperOutcomeUncertaintyInput",
    "PaperOutcomeUncertaintyConfig",
    "PaperOutcomeUncertaintyRow",
    "PaperOutcomeUncertaintyReport",
    "build_paper_outcome_uncertainty_report",
)
