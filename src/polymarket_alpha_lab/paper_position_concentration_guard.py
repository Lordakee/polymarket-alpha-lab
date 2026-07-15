from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
GROUP_TYPES = ("market", "category", "team", "outcome_side")
CONCENTRATION_STATUSES = ("clear", "watch")
GROUP_TYPE_PRIORITY = {"market": 0, "category": 1, "team": 2, "outcome_side": 3}
REASON_BY_GROUP_TYPE = {
    "market": "market_share_at_or_above_limit",
    "category": "category_share_at_or_above_limit",
    "team": "team_share_at_or_above_limit",
    "outcome_side": "outcome_side_share_at_or_above_limit",
}


@dataclass(frozen=True)
class PaperPositionConcentrationGuardConfig:
    config_version: str
    market_warn_share: Decimal
    category_warn_share: Decimal
    team_warn_share: Decimal
    outcome_side_warn_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_warn_share",
            "category_warn_share",
            "team_warn_share",
            "outcome_side_warn_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_share(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperPositionConcentrationRecord:
    market_slug: str
    category_id: str
    team_id: str
    outcome_side: str
    open_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "category_id",
            "team_id",
            "outcome_side",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "open_notional",
            _normalize_nonnegative_decimal("open_notional", self.open_notional),
        )
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class PaperPositionConcentrationGuardRow:
    group_type: str
    group_value: str
    position_count: int
    open_notional: Decimal
    share_of_total_open_notional: Decimal | None
    threshold_share: Decimal
    concentration_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if self.group_type not in GROUP_TYPES:
            raise ValueError("group_type must be a known concentration group type")
        _require_canonical_string("group_value", self.group_value)
        _require_positive_int("position_count", self.position_count)
        object.__setattr__(
            self,
            "open_notional",
            _normalize_nonnegative_decimal("open_notional", self.open_notional),
        )
        object.__setattr__(
            self,
            "share_of_total_open_notional",
            _normalize_optional_share(
                "share_of_total_open_notional",
                self.share_of_total_open_notional,
            ),
        )
        object.__setattr__(
            self,
            "threshold_share",
            _normalize_share("threshold_share", self.threshold_share),
        )
        if self.concentration_status not in CONCENTRATION_STATUSES:
            raise ValueError("concentration_status must be clear or watch")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class PaperPositionConcentrationGuardReport:
    generated_at: datetime
    config_version: str
    record_count: int
    group_count: int
    clear_count: int
    watch_count: int
    total_open_notional: Decimal
    concentration_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PaperPositionConcentrationGuardRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("record_count", "group_count", "clear_count", "watch_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_open_notional",
            _normalize_nonnegative_decimal(
                "total_open_notional",
                self.total_open_notional,
            ),
        )
        if self.concentration_status not in CONCENTRATION_STATUSES:
            raise ValueError("concentration_status must be clear or watch")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_paper_position_concentration_guard_report(
    records: list[PaperPositionConcentrationRecord]
    | tuple[PaperPositionConcentrationRecord, ...],
    *,
    config: PaperPositionConcentrationGuardConfig,
    generated_at: datetime,
) -> PaperPositionConcentrationGuardReport:
    if type(config) is not PaperPositionConcentrationGuardConfig:
        raise ValueError("config must be a PaperPositionConcentrationGuardConfig")
    generated_at = _as_utc(generated_at)
    _require_hard_flags("config", config)
    normalized_records = _normalize_records(records)
    total_open_notional = _sum_decimal(
        value.open_notional for value in normalized_records
    )
    rows = _build_rows(
        normalized_records,
        config=config,
        total_open_notional=total_open_notional,
    )
    return PaperPositionConcentrationGuardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        record_count=len(normalized_records),
        group_count=len(rows),
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        total_open_notional=total_open_notional,
        concentration_status=_report_status(rows),
        reason_codes=_dedupe(
            reason_code for row in rows for reason_code in row.reason_codes
        ),
        rows=rows,
    )


def _build_rows(
    records: tuple[PaperPositionConcentrationRecord, ...],
    *,
    config: PaperPositionConcentrationGuardConfig,
    total_open_notional: Decimal,
) -> tuple[PaperPositionConcentrationGuardRow, ...]:
    rows: list[PaperPositionConcentrationGuardRow] = []
    for group_type, threshold_share, pairs in (
        (
            "market",
            config.market_warn_share,
            ((value, value.market_slug) for value in records),
        ),
        (
            "category",
            config.category_warn_share,
            ((value, value.category_id) for value in records),
        ),
        (
            "team",
            config.team_warn_share,
            ((value, value.team_id) for value in records),
        ),
        (
            "outcome_side",
            config.outcome_side_warn_share,
            ((value, value.outcome_side) for value in records),
        ),
    ):
        rows.extend(
            _rows_for_group(
                group_type,
                threshold_share=threshold_share,
                pairs=pairs,
                total_open_notional=total_open_notional,
            ),
        )
    return tuple(sorted(rows, key=_row_sort_key))


def _rows_for_group(
    group_type: str,
    *,
    threshold_share: Decimal,
    pairs: Iterable[tuple[PaperPositionConcentrationRecord, str]],
    total_open_notional: Decimal,
) -> tuple[PaperPositionConcentrationGuardRow, ...]:
    grouped: dict[str, list[PaperPositionConcentrationRecord]] = {}
    for record, group_value in pairs:
        grouped.setdefault(group_value, []).append(record)

    rows: list[PaperPositionConcentrationGuardRow] = []
    for group_value, values in grouped.items():
        open_notional = _sum_decimal(value.open_notional for value in values)
        share = _share(open_notional, total_open_notional)
        reason_codes = _reason_codes_for(
            group_type,
            share=share,
            threshold_share=threshold_share,
        )
        rows.append(
            PaperPositionConcentrationGuardRow(
                group_type=group_type,
                group_value=group_value,
                position_count=len(values),
                open_notional=open_notional,
                share_of_total_open_notional=share,
                threshold_share=threshold_share,
                concentration_status=_status_from_reason_codes(reason_codes),
                reason_codes=reason_codes,
            ),
        )
    return tuple(rows)


def _reason_codes_for(
    group_type: str,
    *,
    share: Decimal | None,
    threshold_share: Decimal,
) -> tuple[str, ...]:
    if share is not None and share >= threshold_share:
        return (REASON_BY_GROUP_TYPE[group_type],)
    return ()


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes:
        return "watch"
    return "clear"


def _report_status(rows: tuple[PaperPositionConcentrationGuardRow, ...]) -> str:
    if _status_count(rows, "watch"):
        return "watch"
    return "clear"


def _status_count(rows: tuple[PaperPositionConcentrationGuardRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.concentration_status == status)


def _row_sort_key(
    row: PaperPositionConcentrationGuardRow,
) -> tuple[int, int, Decimal, str]:
    return (
        0 if row.concentration_status == "watch" else 1,
        GROUP_TYPE_PRIORITY[row.group_type],
        -row.open_notional,
        row.group_value,
    )


def _normalize_records(
    values: list[PaperPositionConcentrationRecord]
    | tuple[PaperPositionConcentrationRecord, ...],
) -> tuple[PaperPositionConcentrationRecord, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(
            "records must be a list or tuple of PaperPositionConcentrationRecord values",
        )
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not PaperPositionConcentrationRecord:
            raise ValueError(
                "records must contain only PaperPositionConcentrationRecord values",
            )
        _require_hard_flags("record", value)
    return normalized


def _normalize_rows(
    values: tuple[PaperPositionConcentrationGuardRow, ...],
) -> tuple[PaperPositionConcentrationGuardRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple of PaperPositionConcentrationGuardRow values")
    for value in values:
        if type(value) is not PaperPositionConcentrationGuardRow:
            raise ValueError(
                "rows must contain only PaperPositionConcentrationGuardRow values",
            )
        _require_hard_flags("row", value)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return values


def _validate_row_consistency(row: PaperPositionConcentrationGuardRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.concentration_status != expected_status:
        raise ValueError("concentration_status must match reason_codes")
    if row.share_of_total_open_notional is None:
        if row.open_notional != ZERO:
            raise ValueError("share_of_total_open_notional needs total notional")
    elif row.share_of_total_open_notional >= row.threshold_share:
        expected_reason = REASON_BY_GROUP_TYPE[row.group_type]
        if row.reason_codes != (expected_reason,):
            raise ValueError("reason_codes must match share threshold")
    elif row.reason_codes:
        raise ValueError("reason_codes must be empty below share threshold")


def _validate_report_consistency(report: PaperPositionConcentrationGuardReport) -> None:
    if report.group_count != len(report.rows):
        raise ValueError("group_count must equal rows length")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must equal rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must equal rows")
    if report.group_count != report.clear_count + report.watch_count:
        raise ValueError("group_count must equal status counts")
    if report.concentration_status != _report_status(report.rows):
        raise ValueError("concentration_status must equal rows")
    expected_reason_codes = _dedupe(
        reason_code for row in report.rows for reason_code in row.reason_codes
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must equal rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return _quantize(total)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _share(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_share(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_optional_share(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_share(field_name, value)


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
    normalized = _quantize(value)
    return normalized.copy_abs() if normalized.is_zero() else normalized


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple of strings")
    for value in values:
        _require_canonical_string("reason_codes", value)
    return _dedupe(values)


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
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


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


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
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "PaperPositionConcentrationGuardConfig",
    "PaperPositionConcentrationRecord",
    "PaperPositionConcentrationGuardRow",
    "PaperPositionConcentrationGuardReport",
    "build_paper_position_concentration_guard_report",
)
