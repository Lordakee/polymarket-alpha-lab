from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


AMT_UNIT = Decimal("0.000001")
ZERO = Decimal("0")
DAYS_PER_YEAR = Decimal("365")
SIDES = frozenset(("yes", "no"))
ROW_FIELDS = (
    "market_slug",
    "question",
    "side",
    "paper_notional",
    "paper_share_quantity",
    "days_locked",
)


@dataclass(frozen=True)
class PaperCapitalCostConfig:
    config_version: str
    annual_capital_cost_rate: Decimal

    def __post_init__(self) -> None:
        _must_text("config_version", self.config_version)
        _must_decimal_min_zero(
            "annual_capital_cost_rate",
            self.annual_capital_cost_rate,
        )


@dataclass(frozen=True)
class PaperCapitalCostRow:
    market_slug: str
    question: str
    side: str
    paper_notional: Decimal
    paper_share_quantity: Decimal
    days_locked: int
    annual_capital_cost_rate: Decimal
    total_capital_cost: Decimal
    capital_cost_per_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _must_text("market_slug", self.market_slug)
        _must_text("question", self.question)
        _must_side(self.side)
        _must_q_decimal_min_zero("paper_notional", self.paper_notional)
        _must_q_decimal_above_zero(
            "paper_share_quantity",
            self.paper_share_quantity,
        )
        _must_int_min_zero("days_locked", self.days_locked)
        _must_decimal_min_zero(
            "annual_capital_cost_rate",
            self.annual_capital_cost_rate,
        )
        _must_q_decimal_min_zero("total_capital_cost", self.total_capital_cost)
        _must_q_decimal_min_zero(
            "capital_cost_per_share",
            self.capital_cost_per_share,
        )
        if self.total_capital_cost != _row_total_cost(
            self.paper_notional,
            self.annual_capital_cost_rate,
            self.days_locked,
        ):
            raise ValueError("total_capital_cost must match row inputs")
        if self.capital_cost_per_share != _ratio(
            self.total_capital_cost,
            self.paper_share_quantity,
        ):
            raise ValueError("capital_cost_per_share must match row inputs")
        _must_true("paper_only", self.paper_only)
        _must_true("report_only", self.report_only)
        _must_true("readonly", self.readonly)


@dataclass(frozen=True)
class PaperCapitalCostReport:
    generated_at: datetime
    config_version: str
    row_count: int
    total_paper_notional: Decimal
    total_capital_cost: Decimal
    mean_capital_cost_per_share: Decimal | None
    capital_cost_rows: tuple[PaperCapitalCostRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc_datetime("generated_at", self.generated_at),
        )
        _must_text("config_version", self.config_version)
        _must_int_min_zero("row_count", self.row_count)
        _must_q_decimal_min_zero("total_paper_notional", self.total_paper_notional)
        _must_q_decimal_min_zero("total_capital_cost", self.total_capital_cost)
        if self.mean_capital_cost_per_share is not None:
            _must_q_decimal_min_zero(
                "mean_capital_cost_per_share",
                self.mean_capital_cost_per_share,
            )
        if type(self.capital_cost_rows) is not tuple:
            raise ValueError("capital_cost_rows must be a tuple")
        if not all(type(row) is PaperCapitalCostRow for row in self.capital_cost_rows):
            raise ValueError("capital_cost_rows must contain PaperCapitalCostRow values")
        if self.row_count != len(self.capital_cost_rows):
            raise ValueError("row_count must match capital_cost_rows")
        if self.total_paper_notional != _sum_q(
            row.paper_notional for row in self.capital_cost_rows
        ):
            raise ValueError("total_paper_notional must match capital_cost_rows")
        if self.total_capital_cost != _sum_q(
            row.total_capital_cost for row in self.capital_cost_rows
        ):
            raise ValueError("total_capital_cost must match capital_cost_rows")
        if self.mean_capital_cost_per_share != _mean_row_share_cost(
            self.capital_cost_rows
        ):
            raise ValueError("mean_capital_cost_per_share must match capital_cost_rows")
        _must_true("paper_only", self.paper_only)
        _must_true("report_only", self.report_only)
        _must_true("readonly", self.readonly)


def build_paper_capital_cost_report(
    inputs: Iterable[object],
    *,
    config: PaperCapitalCostConfig,
    generated_at: datetime,
) -> PaperCapitalCostReport:
    if type(config) is not PaperCapitalCostConfig:
        raise ValueError("config must be a PaperCapitalCostConfig")
    generated_at_utc = _as_utc_datetime("generated_at", generated_at)
    try:
        source_rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be iterable") from exc

    rows = tuple(
        _build_row(source_row, annual_rate=config.annual_capital_cost_rate)
        for source_row in source_rows
    )
    return PaperCapitalCostReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=len(rows),
        total_paper_notional=_sum_q(row.paper_notional for row in rows),
        total_capital_cost=_sum_q(row.total_capital_cost for row in rows),
        mean_capital_cost_per_share=_mean_row_share_cost(rows),
        capital_cost_rows=rows,
    )


def _build_row(source_row: object, *, annual_rate: Decimal) -> PaperCapitalCostRow:
    values = {field_name: _row_value(source_row, field_name) for field_name in ROW_FIELDS}
    _must_text("market_slug", values["market_slug"])
    _must_text("question", values["question"])
    _must_side(values["side"])
    _must_q_decimal_min_zero("paper_notional", values["paper_notional"])
    _must_q_decimal_above_zero("paper_share_quantity", values["paper_share_quantity"])
    _must_int_min_zero("days_locked", values["days_locked"])
    total_cost = _row_total_cost(
        values["paper_notional"],
        annual_rate,
        values["days_locked"],
    )
    return PaperCapitalCostRow(
        market_slug=values["market_slug"],
        question=values["question"],
        side=values["side"],
        paper_notional=_q(values["paper_notional"]),
        paper_share_quantity=_q(values["paper_share_quantity"]),
        days_locked=values["days_locked"],
        annual_capital_cost_rate=annual_rate,
        total_capital_cost=total_cost,
        capital_cost_per_share=_ratio(total_cost, values["paper_share_quantity"]),
    )


def _row_value(source_row: object, field_name: str) -> object:
    if isinstance(source_row, Mapping):
        if field_name not in source_row:
            raise ValueError(f"{field_name} is required")
        return source_row[field_name]
    if not hasattr(source_row, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(source_row, field_name)


def _row_total_cost(
    paper_notional: Decimal,
    annual_rate: Decimal,
    days_locked: int,
) -> Decimal:
    _must_decimal_min_zero("paper_notional", paper_notional)
    _must_decimal_min_zero("annual_capital_cost_rate", annual_rate)
    _must_int_min_zero("days_locked", days_locked)
    return _q(paper_notional * annual_rate * Decimal(days_locked) / DAYS_PER_YEAR)


def _mean_row_share_cost(rows: tuple[PaperCapitalCostRow, ...]) -> Decimal | None:
    if not rows:
        return None
    return _q(sum(row.capital_cost_per_share for row in rows) / Decimal(len(rows)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    _must_decimal_min_zero("total_capital_cost", numerator)
    _must_decimal_above_zero("paper_share_quantity", denominator)
    return _q(numerator / denominator)


def _sum_q(values: Iterable[Decimal]) -> Decimal:
    return _q(sum(values, ZERO))


def _as_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _must_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _must_side(value: object) -> None:
    if value not in SIDES:
        raise ValueError("side must be yes or no")


def _must_int_min_zero(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be at least zero")


def _must_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _must_decimal_min_zero(field_name: str, value: object) -> None:
    _must_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be at least zero")


def _must_decimal_above_zero(field_name: str, value: object) -> None:
    _must_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be above zero")


def _must_q_decimal_min_zero(field_name: str, value: object) -> None:
    _must_decimal_min_zero(field_name, value)
    if value != _q(value):
        raise ValueError(f"{field_name} must align to {AMT_UNIT}")


def _must_q_decimal_above_zero(field_name: str, value: object) -> None:
    _must_decimal_above_zero(field_name, value)
    if value != _q(value):
        raise ValueError(f"{field_name} must align to {AMT_UNIT}")


def _must_true(field_name: str, value: object) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _q(value: Decimal) -> Decimal:
    return value.quantize(AMT_UNIT)


__all__ = (
    "PaperCapitalCostConfig",
    "PaperCapitalCostRow",
    "PaperCapitalCostReport",
    "build_paper_capital_cost_report",
)
