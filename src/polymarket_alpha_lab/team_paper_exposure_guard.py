"""Pure diagnostics for proposed team paper exposure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
SIDES = ("yes", "no")
EXPOSURE_STATUSES = ("pass", "watch", "blocked")
STATUS_PRIORITY = {"pass": 0, "watch": 1, "blocked": 2}


@dataclass(frozen=True)
class TeamPaperExposureGuardConfig:
    max_team_notional: Decimal
    max_category_notional: Decimal
    max_event_template_notional: Decimal
    max_market_notional: Decimal
    min_confidence_for_full_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "max_team_notional",
            "max_category_notional",
            "max_event_template_notional",
            "max_market_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confidence_for_full_notional",
            _normalize_probability(
                "min_confidence_for_full_notional",
                self.min_confidence_for_full_notional,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamPaperExposureInput:
    team_id: str
    category_id: str
    event_template: str
    market_slug: str
    selected_side: str
    proposed_notional: Decimal
    existing_paper_notional: Decimal
    confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "category_id",
            "event_template",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.selected_side not in SIDES:
            raise ValueError("selected_side must be yes or no")
        for field_name in ("proposed_notional", "existing_paper_notional"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _normalize_nonnegative_decimal("confidence", self.confidence),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class TeamPaperExposureGuardRow:
    team_id: str
    category_id: str
    event_template: str
    market_slug: str
    selected_side: str
    proposed_notional: Decimal
    existing_paper_notional: Decimal
    confidence: Decimal
    team_total_notional: Decimal
    category_total_notional: Decimal
    event_template_total_notional: Decimal
    market_total_notional: Decimal
    capped_notional: Decimal
    exposure_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "category_id",
            "event_template",
            "market_slug",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        if self.selected_side not in SIDES:
            raise ValueError("selected_side must be yes or no")
        for field_name in (
            "proposed_notional",
            "existing_paper_notional",
            "team_total_notional",
            "category_total_notional",
            "event_template_total_notional",
            "market_total_notional",
            "capped_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _normalize_nonnegative_decimal("confidence", self.confidence),
        )
        if self.exposure_status not in EXPOSURE_STATUSES:
            raise ValueError("exposure_status must be pass, watch, or blocked")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class TeamPaperExposureGuardReport:
    generated_at: datetime
    input_count: int
    row_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    exposure_status: str
    total_proposed_notional: Decimal
    total_existing_paper_notional: Decimal
    total_capped_notional: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[TeamPaperExposureGuardRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.exposure_status not in EXPOSURE_STATUSES:
            raise ValueError("exposure_status must be pass, watch, or blocked")
        for field_name in (
            "total_proposed_notional",
            "total_existing_paper_notional",
            "total_capped_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_team_paper_exposure_guard_report(
    inputs: list[TeamPaperExposureInput] | tuple[TeamPaperExposureInput, ...],
    *,
    config: TeamPaperExposureGuardConfig,
    generated_at: datetime,
) -> TeamPaperExposureGuardReport:
    if type(config) is not TeamPaperExposureGuardConfig:
        raise ValueError("config must be a TeamPaperExposureGuardConfig")
    generated_at = _as_utc(generated_at)
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    maps = _exposure_maps(normalized_inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config, maps=maps) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return TeamPaperExposureGuardReport(
        generated_at=generated_at,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        exposure_status=_report_status(rows),
        total_proposed_notional=_sum_decimal(row.proposed_notional for row in rows),
        total_existing_paper_notional=_sum_decimal(
            row.existing_paper_notional for row in rows
        ),
        total_capped_notional=_sum_decimal(row.capped_notional for row in rows),
        reason_codes=_dedupe(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
        ),
        rows=rows,
    )


def _row_from_input(
    value: TeamPaperExposureInput,
    *,
    config: TeamPaperExposureGuardConfig,
    maps: dict[str, dict[str, Decimal]],
) -> TeamPaperExposureGuardRow:
    reason_codes = _reason_codes_for(value, config=config, maps=maps)
    return TeamPaperExposureGuardRow(
        team_id=value.team_id,
        category_id=value.category_id,
        event_template=value.event_template,
        market_slug=value.market_slug,
        selected_side=value.selected_side,
        proposed_notional=value.proposed_notional,
        existing_paper_notional=value.existing_paper_notional,
        confidence=value.confidence,
        team_total_notional=maps["team_total"][value.team_id],
        category_total_notional=maps["category_total"][value.category_id],
        event_template_total_notional=maps["template_total"][value.event_template],
        market_total_notional=maps["market_total"][value.market_slug],
        capped_notional=_capped_notional(value, config=config, maps=maps),
        exposure_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _reason_codes_for(
    value: TeamPaperExposureInput,
    *,
    config: TeamPaperExposureGuardConfig,
    maps: dict[str, dict[str, Decimal]],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if maps["team_total"][value.team_id] > config.max_team_notional:
        reason_codes.append("team_notional_above_max")
    if maps["category_total"][value.category_id] > config.max_category_notional:
        reason_codes.append("category_notional_above_max")
    if (
        maps["template_total"][value.event_template]
        > config.max_event_template_notional
    ):
        reason_codes.append("event_template_notional_above_max")
    if maps["market_total"][value.market_slug] > config.max_market_notional:
        reason_codes.append("market_notional_above_max")
    if value.confidence < config.min_confidence_for_full_notional:
        reason_codes.append("confidence_below_full_notional")
    return tuple(reason_codes)


def _capped_notional(
    value: TeamPaperExposureInput,
    *,
    config: TeamPaperExposureGuardConfig,
    maps: dict[str, dict[str, Decimal]],
) -> Decimal:
    candidates = (
        value.proposed_notional,
        _remaining_notional(
            config.max_team_notional,
            maps["team_existing"][value.team_id],
        ),
        _remaining_notional(
            config.max_category_notional,
            maps["category_existing"][value.category_id],
        ),
        _remaining_notional(
            config.max_event_template_notional,
            maps["template_existing"][value.event_template],
        ),
        _remaining_notional(
            config.max_market_notional,
            maps["market_existing"][value.market_slug],
        ),
        _confidence_notional(value, config.min_confidence_for_full_notional),
    )
    capped = candidates[0]
    for candidate in candidates[1:]:
        if candidate < capped:
            capped = candidate
    return _quantize(capped)


def _confidence_notional(
    value: TeamPaperExposureInput,
    min_confidence_for_full_notional: Decimal,
) -> Decimal:
    if value.confidence >= min_confidence_for_full_notional:
        return value.proposed_notional
    if min_confidence_for_full_notional <= ZERO:
        return value.proposed_notional
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            value.proposed_notional
            * value.confidence
            / min_confidence_for_full_notional,
        )


def _remaining_notional(limit: Decimal, existing_notional: Decimal) -> Decimal:
    if existing_notional >= limit:
        return _quantize(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(limit - existing_notional)


def _exposure_maps(
    inputs: tuple[TeamPaperExposureInput, ...],
) -> dict[str, dict[str, Decimal]]:
    maps: dict[str, dict[str, Decimal]] = {
        "team_total": {},
        "category_total": {},
        "template_total": {},
        "market_total": {},
        "team_existing": {},
        "category_existing": {},
        "template_existing": {},
        "market_existing": {},
    }
    for value in inputs:
        row_total = _add_decimal(value.existing_paper_notional, value.proposed_notional)
        _add_to_map(maps["team_total"], value.team_id, row_total)
        _add_to_map(maps["category_total"], value.category_id, row_total)
        _add_to_map(maps["template_total"], value.event_template, row_total)
        _add_to_map(maps["market_total"], value.market_slug, row_total)
        _add_to_map(maps["team_existing"], value.team_id, value.existing_paper_notional)
        _add_to_map(
            maps["category_existing"],
            value.category_id,
            value.existing_paper_notional,
        )
        _add_to_map(
            maps["template_existing"],
            value.event_template,
            value.existing_paper_notional,
        )
        _add_to_map(
            maps["market_existing"],
            value.market_slug,
            value.existing_paper_notional,
        )
    return maps


def _add_to_map(values: dict[str, Decimal], key: str, value: Decimal) -> None:
    values[key] = _add_decimal(values.get(key, ZERO), value)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_above_max") for reason_code in reason_codes):
        return "blocked"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[TeamPaperExposureGuardRow, ...]) -> str:
    if _status_count(rows, "blocked"):
        return "blocked"
    if _status_count(rows, "watch"):
        return "watch"
    return "pass"


def _row_sort_key(row: TeamPaperExposureGuardRow) -> tuple[int, str, str, str, str, str]:
    return (
        STATUS_PRIORITY[row.exposure_status],
        row.team_id,
        row.category_id,
        row.event_template,
        row.market_slug,
        row.selected_side,
    )


def _status_count(rows: tuple[TeamPaperExposureGuardRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.exposure_status == status)


def _normalize_inputs(
    values: list[TeamPaperExposureInput] | tuple[TeamPaperExposureInput, ...],
) -> tuple[TeamPaperExposureInput, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple of TeamPaperExposureInput values")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not TeamPaperExposureInput:
            raise ValueError("inputs must contain only TeamPaperExposureInput values")
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    values: tuple[TeamPaperExposureGuardRow, ...],
) -> tuple[TeamPaperExposureGuardRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple of TeamPaperExposureGuardRow values")
    for value in values:
        if type(value) is not TeamPaperExposureGuardRow:
            raise ValueError("rows must contain only TeamPaperExposureGuardRow values")
        _require_hard_flags("row", value)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return values


def _validate_row_consistency(row: TeamPaperExposureGuardRow) -> None:
    row_total = _add_decimal(row.existing_paper_notional, row.proposed_notional)
    if row.team_total_notional < row_total:
        raise ValueError("team_total_notional must cover row notional")
    if row.category_total_notional < row_total:
        raise ValueError("category_total_notional must cover row notional")
    if row.event_template_total_notional < row_total:
        raise ValueError("event_template_total_notional must cover row notional")
    if row.market_total_notional < row_total:
        raise ValueError("market_total_notional must cover row notional")
    if row.capped_notional > row.proposed_notional:
        raise ValueError("capped_notional must not exceed proposed_notional")
    if row.exposure_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("exposure_status must match reason_codes")


def _validate_report_consistency(report: TeamPaperExposureGuardReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must equal rows length")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must equal rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must equal rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must equal rows")
    if report.row_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("row_count must equal status counts")
    if report.exposure_status != _report_status(report.rows):
        raise ValueError("exposure_status must equal rows")
    if report.total_proposed_notional != _sum_decimal(
        row.proposed_notional for row in report.rows
    ):
        raise ValueError("total_proposed_notional must equal rows")
    if report.total_existing_paper_notional != _sum_decimal(
        row.existing_paper_notional for row in report.rows
    ):
        raise ValueError("total_existing_paper_notional must equal rows")
    if report.total_capped_notional != _sum_decimal(
        row.capped_notional for row in report.rows
    ):
        raise ValueError("total_capped_notional must equal rows")
    expected_reason_codes = _dedupe(
        reason_code
        for row in report.rows
        for reason_code in row.reason_codes
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must equal rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return _quantize(total)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple of strings")
    for value in values:
        _require_canonical_string("reason_codes", value)
    return _dedupe(values)


def _dedupe(values: object) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
    return value.astimezone(UTC)


__all__ = (
    "TeamPaperExposureGuardConfig",
    "TeamPaperExposureInput",
    "TeamPaperExposureGuardRow",
    "TeamPaperExposureGuardReport",
    "build_team_paper_exposure_guard_report",
)
