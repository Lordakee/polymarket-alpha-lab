"""Pure paper-only summary reducer for supplied recommendation gate rows."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "GateReasonCodeCount",
    "PaperRecommendationGateInputRow",
    "PaperRecommendationGateSummaryReport",
    "PaperRecommendationGateSummaryRow",
    "build_paper_recommendation_gate_summary_report",
)


ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")
GATE_STATUSES = ("pass", "watch", "blocked")
STATUS_SEVERITY = {
    "pass": 0,
    "watch": 1,
    "blocked": 2,
}


@dataclass(frozen=True)
class GateReasonCodeCount:
    reason_code: str
    count: int

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)


@dataclass(frozen=True)
class PaperRecommendationGateInputRow:
    market_slug: str
    side: str
    gate_name: str
    gate_status: str
    gate_cost_per_share: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("side", self.side)
        _require_canonical_string("gate_name", self.gate_name)
        _require_gate_status("gate_status", self.gate_status)
        _require_cost("gate_cost_per_share", self.gate_cost_per_share)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("gate row", self)


@dataclass(frozen=True)
class PaperRecommendationGateSummaryRow:
    gate_name: str
    gate_input_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    total_gate_cost_per_share: Decimal
    primary_status: str
    reason_code_counts: tuple[GateReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("gate_name", self.gate_name)
        _require_nonnegative_int("gate_input_count", self.gate_input_count)
        _require_nonnegative_int("pass_count", self.pass_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        _require_cost("total_gate_cost_per_share", self.total_gate_cost_per_share)
        _require_gate_status("primary_status", self.primary_status)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_summary_row_consistency(self)
        _require_hard_flags("summary row", self)


@dataclass(frozen=True)
class PaperRecommendationGateSummaryReport:
    generated_at: datetime
    gate_input_count: int
    gate_name_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    total_gate_cost_per_share: Decimal
    primary_status: str
    rows: tuple[PaperRecommendationGateSummaryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_nonnegative_int("gate_input_count", self.gate_input_count)
        _require_nonnegative_int("gate_name_count", self.gate_name_count)
        _require_nonnegative_int("pass_count", self.pass_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        _require_cost("total_gate_cost_per_share", self.total_gate_cost_per_share)
        _require_gate_status("primary_status", self.primary_status)
        object.__setattr__(self, "rows", _normalize_summary_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("summary report", self)


def build_paper_recommendation_gate_summary_report(
    gate_rows: tuple[object, ...] | list[object],
    *,
    generated_at: datetime,
) -> PaperRecommendationGateSummaryReport:
    generated_at = _as_utc(generated_at)
    rows = _normalize_gate_rows(gate_rows)
    summary_rows = _build_summary_rows(rows)

    return PaperRecommendationGateSummaryReport(
        generated_at=generated_at,
        gate_input_count=len(rows),
        gate_name_count=len(summary_rows),
        pass_count=sum(row.pass_count for row in summary_rows),
        watch_count=sum(row.watch_count for row in summary_rows),
        blocked_count=sum(row.blocked_count for row in summary_rows),
        total_gate_cost_per_share=_quantize_cost(
            sum((row.total_gate_cost_per_share for row in summary_rows), ZERO),
        ),
        primary_status=_primary_status(
            pass_count=sum(row.pass_count for row in summary_rows),
            watch_count=sum(row.watch_count for row in summary_rows),
            blocked_count=sum(row.blocked_count for row in summary_rows),
        ),
        rows=summary_rows,
    )


def _build_summary_rows(
    rows: tuple[PaperRecommendationGateInputRow, ...],
) -> tuple[PaperRecommendationGateSummaryRow, ...]:
    groups: dict[str, list[PaperRecommendationGateInputRow]] = {}
    for row in rows:
        groups.setdefault(row.gate_name, []).append(row)

    summary_rows = tuple(
        _summary_row_for_group(gate_name, tuple(group_rows))
        for gate_name, group_rows in groups.items()
    )
    return tuple(sorted(summary_rows, key=_summary_row_sort_key))


def _summary_row_for_group(
    gate_name: str,
    rows: tuple[PaperRecommendationGateInputRow, ...],
) -> PaperRecommendationGateSummaryRow:
    pass_count = sum(1 for row in rows if row.gate_status == "pass")
    watch_count = sum(1 for row in rows if row.gate_status == "watch")
    blocked_count = sum(1 for row in rows if row.gate_status == "blocked")
    reason_counts: Counter[str] = Counter()
    for row in rows:
        reason_counts.update(row.reason_codes)

    return PaperRecommendationGateSummaryRow(
        gate_name=gate_name,
        gate_input_count=len(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        total_gate_cost_per_share=_quantize_cost(
            sum((row.gate_cost_per_share for row in rows), ZERO),
        ),
        primary_status=_primary_status(
            pass_count=pass_count,
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
        reason_code_counts=_reason_code_count_rows(reason_counts),
    )


def _reason_code_count_rows(reason_counts: Counter[str]) -> tuple[GateReasonCodeCount, ...]:
    return tuple(
        GateReasonCodeCount(reason_code=reason_code, count=count)
        for reason_code, count in sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _summary_row_sort_key(
    row: PaperRecommendationGateSummaryRow,
) -> tuple[int, int, int, int, Decimal, str]:
    return (
        -STATUS_SEVERITY[row.primary_status],
        -row.blocked_count,
        -row.watch_count,
        -row.pass_count,
        -row.total_gate_cost_per_share,
        row.gate_name,
    )


def _primary_status(*, pass_count: int, watch_count: int, blocked_count: int) -> str:
    if blocked_count > 0:
        return "blocked"
    if watch_count > 0:
        return "watch"
    return "pass"


def _normalize_gate_rows(
    rows: tuple[object, ...] | list[object],
) -> tuple[PaperRecommendationGateInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("gate_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("gate_rows must be an iterable") from exc
    return tuple(_coerce_gate_row(row) for row in items)


def _coerce_gate_row(row: object) -> PaperRecommendationGateInputRow:
    if type(row) is PaperRecommendationGateInputRow:
        return row
    return PaperRecommendationGateInputRow(
        market_slug=_required_attr(row, "market_slug"),
        side=_required_attr(row, "side"),
        gate_name=_required_attr(row, "gate_name"),
        gate_status=_required_attr(row, "gate_status"),
        gate_cost_per_share=_required_attr(row, "gate_cost_per_share"),
        reason_codes=_required_attr(row, "reason_codes"),
        paper_only=_required_attr(row, "paper_only"),
        report_only=_required_attr(row, "report_only"),
        readonly=_required_attr(row, "readonly"),
    )


def _normalize_summary_rows(
    rows: tuple[PaperRecommendationGateSummaryRow, ...],
) -> tuple[PaperRecommendationGateSummaryRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not PaperRecommendationGateSummaryRow:
            raise ValueError("rows must contain only summary rows")
        _require_hard_flags("summary row", row)
    sorted_items = tuple(sorted(items, key=_summary_row_sort_key))
    if items != sorted_items:
        raise ValueError("rows must be deterministically sorted")
    return items


def _normalize_reason_code_counts(
    reason_code_counts: tuple[GateReasonCodeCount, ...],
) -> tuple[GateReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not GateReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
    sorted_items = tuple(
        sorted(
            items,
            key=lambda item: (-item.count, item.reason_code),
        ),
    )
    if items != sorted_items:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return items


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    for item in items:
        _require_canonical_string("reason_codes", item)
    return items


def _validate_summary_row_consistency(
    row: PaperRecommendationGateSummaryRow,
) -> None:
    count_total = row.pass_count + row.watch_count + row.blocked_count
    if row.gate_input_count != count_total:
        raise ValueError("gate_input_count must match status counts")
    if row.primary_status != _primary_status(
        pass_count=row.pass_count,
        watch_count=row.watch_count,
        blocked_count=row.blocked_count,
    ):
        raise ValueError("primary_status must match status counts")
    if row.reason_code_counts and row.gate_input_count == 0:
        raise ValueError("reason_code_counts require gate rows")
    if row.gate_input_count > 0 and not row.reason_code_counts:
        raise ValueError("reason_code_counts must summarize gate rows")
    if row.gate_input_count == 0 and row.total_gate_cost_per_share != ZERO:
        raise ValueError("total_gate_cost_per_share must be zero with no rows")


def _validate_report_consistency(
    report: PaperRecommendationGateSummaryReport,
) -> None:
    if report.gate_input_count != sum(row.gate_input_count for row in report.rows):
        raise ValueError("gate_input_count must match summary rows")
    if report.gate_name_count != len(report.rows):
        raise ValueError("gate_name_count must match summary rows")
    if report.pass_count != sum(row.pass_count for row in report.rows):
        raise ValueError("pass_count must match summary rows")
    if report.watch_count != sum(row.watch_count for row in report.rows):
        raise ValueError("watch_count must match summary rows")
    if report.blocked_count != sum(row.blocked_count for row in report.rows):
        raise ValueError("blocked_count must match summary rows")
    expected_cost = _quantize_cost(
        sum((row.total_gate_cost_per_share for row in report.rows), ZERO),
    )
    if report.total_gate_cost_per_share != expected_cost:
        raise ValueError("total_gate_cost_per_share must match summary rows")
    if report.primary_status != _primary_status(
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    ):
        raise ValueError("primary_status must match summary rows")


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} must be report_only")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_cost(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_cost(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _quantize_cost(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("cost", value)
    return value.quantize(QUANTUM)
