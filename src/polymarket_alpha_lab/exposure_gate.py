from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.positions import PaperNavSnapshot, PaperPortfolio, PaperPosition


ZERO = Decimal("0")
PASS_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = PASS_STATUSES
STATUS_SEVERITY = {"blocked": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class PaperExposureGateConfig:
    config_version: str
    max_market_exposure: Decimal
    max_total_exposure: Decimal
    max_position_count: int
    min_cash_buffer: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal("max_market_exposure", self.max_market_exposure)
        _require_nonnegative_decimal("max_total_exposure", self.max_total_exposure)
        _require_nonnegative_int("max_position_count", self.max_position_count)
        _require_nonnegative_decimal("min_cash_buffer", self.min_cash_buffer)


@dataclass(frozen=True)
class PaperExposureGateRow:
    market_slug: str
    exposure_amount: Decimal
    status: str
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_nonnegative_decimal("exposure_amount", self.exposure_amount)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )


@dataclass(frozen=True)
class PaperExposureGateReport:
    generated_at: datetime
    config_version: str
    status: str
    position_count: int
    total_exposure: Decimal
    cash_buffer: Decimal | None
    rows: tuple[PaperExposureGateRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_nonnegative_int("position_count", self.position_count)
        _require_nonnegative_decimal("total_exposure", self.total_exposure)
        _require_optional_nonnegative_decimal("cash_buffer", self.cash_buffer)
        rows = _normalize_rows(self.rows)
        object.__setattr__(self, "rows", rows)
        if self.total_exposure != _exact_sum(row.exposure_amount for row in rows):
            raise ValueError("total_exposure must match rows")
        reason_codes = _normalize_reason_codes(self.reason_codes)
        object.__setattr__(self, "reason_codes", reason_codes)
        for reason_code in _dedupe(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
        ):
            if reason_code not in reason_codes:
                raise ValueError("reason_codes must include row reason_codes")
        if self.status != _report_status(reason_codes):
            raise ValueError("status must match reason_codes")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_exposure_gate_report(
    positions: PaperPortfolio | Iterable[PaperPosition],
    *,
    config: PaperExposureGateConfig,
    generated_at: datetime,
    nav_snapshot: PaperNavSnapshot | None = None,
) -> PaperExposureGateReport:
    if type(config) is not PaperExposureGateConfig:
        raise ValueError("config must be a PaperExposureGateConfig")
    generated_at = _as_utc(generated_at)
    if nav_snapshot is not None and type(nav_snapshot) is not PaperNavSnapshot:
        raise ValueError("nav_snapshot must be a PaperNavSnapshot or None")

    normalized_positions, cash_buffer = _normalize_position_input(positions)
    if nav_snapshot is not None:
        cash_buffer = nav_snapshot.cash_balance

    rows = _build_rows(normalized_positions, config)
    total_exposure = _exact_sum(position.cost_basis for position in normalized_positions)
    reason_codes = _report_reason_codes(
        position_count=len(normalized_positions),
        total_exposure=total_exposure,
        cash_buffer=cash_buffer,
        rows=rows,
        config=config,
    )

    return PaperExposureGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(reason_codes),
        position_count=len(normalized_positions),
        total_exposure=total_exposure,
        cash_buffer=cash_buffer,
        rows=rows,
        reason_codes=reason_codes,
    )


def _normalize_position_input(
    value: PaperPortfolio | Iterable[PaperPosition],
) -> tuple[tuple[PaperPosition, ...], Decimal | None]:
    if type(value) is PaperPortfolio:
        return value.positions, value.cash_balance
    if isinstance(value, (str, bytes)):
        raise ValueError("positions must be a PaperPortfolio or iterable of PaperPosition values")
    try:
        positions = tuple(value)
    except TypeError as exc:
        raise ValueError(
            "positions must be a PaperPortfolio or iterable of PaperPosition values",
        ) from exc

    for position in positions:
        if type(position) is not PaperPosition:
            raise ValueError("positions must contain only PaperPosition values")
    return positions, None


def _build_rows(
    positions: tuple[PaperPosition, ...],
    config: PaperExposureGateConfig,
) -> tuple[PaperExposureGateRow, ...]:
    exposure_by_market: dict[str, Decimal] = {}
    for position in positions:
        exposure_by_market[position.market_slug] = (
            exposure_by_market.get(position.market_slug, ZERO) + position.cost_basis
        )

    rows = tuple(
        PaperExposureGateRow(
            market_slug=market_slug,
            exposure_amount=exposure_amount,
            status=_row_status(exposure_amount, config.max_market_exposure),
            reason_codes=_row_reason_codes(exposure_amount, config.max_market_exposure),
        )
        for market_slug, exposure_amount in exposure_by_market.items()
    )
    return tuple(
        sorted(rows, key=lambda row: (STATUS_SEVERITY[row.status], row.market_slug)),
    )


def _row_status(exposure_amount: Decimal, max_market_exposure: Decimal) -> str:
    if exposure_amount > max_market_exposure:
        return "blocked"
    if exposure_amount == max_market_exposure and exposure_amount > ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    exposure_amount: Decimal,
    max_market_exposure: Decimal,
) -> tuple[str, ...]:
    if exposure_amount > max_market_exposure:
        return ("market_exposure_exceeds_max",)
    if exposure_amount == max_market_exposure and exposure_amount > ZERO:
        return ("market_exposure_at_max",)
    return ()


def _report_reason_codes(
    *,
    position_count: int,
    total_exposure: Decimal,
    cash_buffer: Decimal | None,
    rows: tuple[PaperExposureGateRow, ...],
    config: PaperExposureGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if position_count == 0:
        reason_codes.append("no_positions")
    if position_count > config.max_position_count:
        reason_codes.append("position_count_exceeds_max")
    if total_exposure > config.max_total_exposure:
        reason_codes.append("total_exposure_exceeds_max")
    if cash_buffer is not None and cash_buffer < config.min_cash_buffer:
        reason_codes.append("cash_buffer_below_min")
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _dedupe(reason_codes)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_exceeds_max") or code == "cash_buffer_below_min" for code in reason_codes):
        return "blocked"
    if reason_codes:
        return "watch"
    return "pass"


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _exact_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        _require_nonnegative_decimal("exposure_amount", value)
        total += value
    return total


def _normalize_rows(
    value: Iterable[PaperExposureGateRow],
) -> tuple[PaperExposureGateRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperExposureGateRow:
            raise ValueError("rows must contain PaperExposureGateRow values")
    return rows


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return reason_codes


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in PASS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


__all__ = (
    "PaperExposureGateConfig",
    "PaperExposureGateRow",
    "PaperExposureGateReport",
    "build_paper_exposure_gate_report",
)
