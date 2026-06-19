"""Pure paper-only decision ledger reducer for recommendation audit rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "PaperRecommendationDecisionLedgerReasonCodeCount",
    "PaperRecommendationDecisionLedgerReport",
    "PaperRecommendationDecisionLedgerRow",
    "build_paper_recommendation_decision_ledger_report",
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
DECISIONS = ("recommend", "watch", "block")
SIDES = ("yes", "no")
SAFETY_FLAGS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class PaperRecommendationDecisionLedgerRow:
    market_slug: str
    side: str
    decision: str
    primary_reason_code: str
    reason_codes: tuple[str, ...]
    expected_edge_per_share: Decimal
    max_cost_per_share: Decimal
    suggested_notional: Decimal
    flags: tuple[str, ...] = SAFETY_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side("side", self.side)
        _require_decision("decision", self.decision)
        _require_canonical_string("primary_reason_code", self.primary_reason_code)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.primary_reason_code not in self.reason_codes:
            raise ValueError("primary_reason_code must be included in reason_codes")
        object.__setattr__(
            self,
            "expected_edge_per_share",
            _finite_decimal(
                "expected_edge_per_share",
                self.expected_edge_per_share,
            ),
        )
        object.__setattr__(
            self,
            "max_cost_per_share",
            _normalize_nonnegative_decimal("max_cost_per_share", self.max_cost_per_share),
        )
        object.__setattr__(
            self,
            "suggested_notional",
            _normalize_nonnegative_decimal(
                "suggested_notional",
                self.suggested_notional,
            ),
        )
        object.__setattr__(self, "flags", _normalize_flags(self.flags))
        _require_safety_flags("ledger row", self)


@dataclass(frozen=True)
class PaperRecommendationDecisionLedgerReasonCodeCount:
    reason_code: str
    count: int

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)


@dataclass(frozen=True)
class PaperRecommendationDecisionLedgerReport:
    generated_at: datetime
    config_version: str
    row_count: int
    recommend_count: int
    watch_count: int
    block_count: int
    total_suggested_notional: Decimal
    average_expected_edge_per_share: Decimal
    reason_code_counts: tuple[PaperRecommendationDecisionLedgerReasonCodeCount, ...]
    rows: tuple[PaperRecommendationDecisionLedgerRow, ...]
    flags: tuple[str, ...] = SAFETY_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "recommend_count",
            "watch_count",
            "block_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_suggested_notional",
            _normalize_nonnegative_decimal(
                "total_suggested_notional",
                self.total_suggested_notional,
            ),
        )
        object.__setattr__(
            self,
            "average_expected_edge_per_share",
            _normalize_decimal(
                "average_expected_edge_per_share",
                self.average_expected_edge_per_share,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "flags", _normalize_flags(self.flags))
        _validate_report_consistency(self)
        _require_safety_flags("ledger report", self)


def build_paper_recommendation_decision_ledger_report(
    *,
    generated_at: datetime,
    config_version: str,
    rows: Iterable[object],
) -> PaperRecommendationDecisionLedgerReport:
    generated_at = _as_utc(generated_at)
    _require_canonical_string("config_version", config_version)
    ledger_rows = _normalize_rows(rows)

    return PaperRecommendationDecisionLedgerReport(
        generated_at=generated_at,
        config_version=config_version,
        row_count=len(ledger_rows),
        recommend_count=_decision_count(ledger_rows, "recommend"),
        watch_count=_decision_count(ledger_rows, "watch"),
        block_count=_decision_count(ledger_rows, "block"),
        total_suggested_notional=sum(
            (row.suggested_notional for row in ledger_rows),
            ZERO,
        ),
        average_expected_edge_per_share=_average_decimal(
            row.expected_edge_per_share for row in ledger_rows
        ),
        reason_code_counts=_reason_code_counts(ledger_rows),
        rows=ledger_rows,
    )


def _normalize_rows(
    rows: Iterable[object],
) -> tuple[PaperRecommendationDecisionLedgerRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    return tuple(_coerce_row(row) for row in items)


def _coerce_row(row: object) -> PaperRecommendationDecisionLedgerRow:
    if type(row) is PaperRecommendationDecisionLedgerRow:
        _require_safety_flags("ledger row", row)
        return row
    return PaperRecommendationDecisionLedgerRow(
        market_slug=_required_attr(row, "market_slug"),
        side=_required_attr(row, "side"),
        decision=_required_attr(row, "decision"),
        primary_reason_code=_required_attr(row, "primary_reason_code"),
        reason_codes=_required_attr(row, "reason_codes"),
        expected_edge_per_share=_required_attr(row, "expected_edge_per_share"),
        max_cost_per_share=_required_attr(row, "max_cost_per_share"),
        suggested_notional=_required_attr(row, "suggested_notional"),
        flags=_optional_attr(row, "flags", SAFETY_FLAGS),
        paper_only=_required_attr(row, "paper_only"),
        report_only=_required_attr(row, "report_only"),
        readonly=_required_attr(row, "readonly"),
    )


def _reason_code_counts(
    rows: tuple[PaperRecommendationDecisionLedgerRow, ...],
) -> tuple[PaperRecommendationDecisionLedgerReasonCodeCount, ...]:
    reason_counts: Counter[str] = Counter()
    for row in rows:
        reason_counts.update(row.reason_codes)
    return tuple(
        PaperRecommendationDecisionLedgerReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _decision_count(
    rows: tuple[PaperRecommendationDecisionLedgerRow, ...],
    decision: str,
) -> int:
    return sum(1 for row in rows if row.decision == decision)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _quantize(ZERO)
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _validate_report_consistency(
    report: PaperRecommendationDecisionLedgerReport,
) -> None:
    if report.row_count != (
        report.recommend_count + report.watch_count + report.block_count
    ):
        raise ValueError(
            "row_count must match recommend_count, watch_count, and block_count",
        )
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.recommend_count != _decision_count(report.rows, "recommend"):
        raise ValueError("recommend_count must match rows")
    if report.watch_count != _decision_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decision_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_suggested_notional != _quantize(
        sum((row.suggested_notional for row in report.rows), ZERO)
    ):
        raise ValueError("total_suggested_notional must match rows")
    if report.average_expected_edge_per_share != _average_decimal(
        row.expected_edge_per_share for row in report.rows
    ):
        raise ValueError("average_expected_edge_per_share must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.flags != SAFETY_FLAGS:
        raise ValueError("flags must be paper-only, report-only, and readonly")


def _normalize_reason_code_counts(
    reason_code_counts: Iterable[PaperRecommendationDecisionLedgerReasonCodeCount],
) -> tuple[PaperRecommendationDecisionLedgerReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not PaperRecommendationDecisionLedgerReasonCodeCount:
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


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
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


def _normalize_flags(flags: Iterable[str]) -> tuple[str, ...]:
    if isinstance(flags, (str, bytes)):
        raise ValueError("flags must be an iterable of strings")
    try:
        items = tuple(flags)
    except TypeError as exc:
        raise ValueError("flags must be an iterable of strings") from exc
    if items != SAFETY_FLAGS:
        raise ValueError("flags must be paper-only, report-only, and readonly")
    for item in items:
        _require_canonical_string("flags", item)
    return items


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _optional_attr(value: object, field_name: str, default: object) -> object:
    if hasattr(value, field_name):
        return getattr(value, field_name)
    return default


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_safety_flags(field_name: str, value: object) -> None:
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


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes or no")


def _require_decision(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DECISIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or block")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_finite_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _finite_decimal(field_name: str, value: object) -> Decimal:
    _require_finite_decimal(field_name, value)
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
