from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.nav_risk_metrics import PaperNavRiskMetricsReport
from polymarket_alpha_lab.paper_settlement_timing import (
    PaperSettlementTimingReport,
    PaperSettlementTimingRow,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64)
OVERLAY_STATUSES = ("acceptable", "watch", "blocked")
REPORT_STATUSES = (
    "empty_nav_settlement_risk_overlay",
    "settlement_nav_risk_clear",
    "settlement_nav_risk_watch",
    "settlement_nav_risk_blocked",
)
ROW_STATUS_PRIORITY = {
    "blocked": 0,
    "watch": 1,
    "acceptable": 2,
}
TIMING_STATUS_SEVERITY = {
    "acceptable": 0,
    "watch": 1,
    "blocked": 2,
}
MISSING_REASON_CODES = ("missing_settlement_timing",)


@dataclass(frozen=True)
class PaperNavSettlementRiskOverlayConfig:
    config_version: str
    max_blocked_settlement_exposure_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_ratio_decimal(
            "max_blocked_settlement_exposure_share",
            self.max_blocked_settlement_exposure_share,
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperNavSettlementRiskOverlayRow:
    condition_id: str
    market_slug: str
    token_count: int
    open_size: Decimal
    cost_basis: Decimal
    exit_value: Decimal
    share_of_exit_nav: Decimal | None
    overlay_status: str
    settlement_timing_status: str | None
    timing_cost_per_share: Decimal | None
    adjusted_net_probability_edge: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_positive_int("token_count", self.token_count)
        for field_name in ("open_size", "cost_basis", "exit_value"):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        if self.open_size <= ZERO:
            raise ValueError("open_size must be positive")
        if self.cost_basis > self.open_size:
            raise ValueError("cost_basis must not exceed open_size")
        if self.exit_value > self.open_size:
            raise ValueError("exit_value must not exceed open_size")
        _require_optional_ratio_decimal("share_of_exit_nav", self.share_of_exit_nav)
        if self.overlay_status not in OVERLAY_STATUSES:
            raise ValueError("overlay_status must be acceptable, watch, or blocked")
        if (
            self.settlement_timing_status is not None
            and self.settlement_timing_status not in OVERLAY_STATUSES
        ):
            raise ValueError(
                "settlement_timing_status must be acceptable, watch, blocked, or None",
            )
        _require_optional_nonnegative_decimal(
            "timing_cost_per_share",
            self.timing_cost_per_share,
        )
        _require_optional_decimal(
            "adjusted_net_probability_edge",
            self.adjusted_net_probability_edge,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperNavSettlementRiskOverlayReport:
    generated_at: datetime
    config_version: str
    nav_risk_config_version: str
    settlement_timing_config_version: str
    nav_snapshot_count: int
    first_marked_at: datetime | None
    last_marked_at: datetime | None
    settlement_row_count: int
    exposure_row_count: int
    acceptable_count: int
    watch_count: int
    blocked_count: int
    missing_settlement_count: int
    acceptable_exit_value: Decimal
    watch_exit_value: Decimal
    blocked_exit_value: Decimal
    missing_settlement_exit_value: Decimal
    blocked_or_missing_exit_value: Decimal
    blocked_or_missing_exit_nav_share: Decimal | None
    max_blocked_settlement_exposure_share: Decimal
    status: str
    rows: tuple[PaperNavSettlementRiskOverlayRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string(
            "nav_risk_config_version",
            self.nav_risk_config_version,
        )
        _require_canonical_string(
            "settlement_timing_config_version",
            self.settlement_timing_config_version,
        )
        for field_name in (
            "nav_snapshot_count",
            "settlement_row_count",
            "exposure_row_count",
            "acceptable_count",
            "watch_count",
            "blocked_count",
            "missing_settlement_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_marked_at",
            _as_optional_utc("first_marked_at", self.first_marked_at),
        )
        object.__setattr__(
            self,
            "last_marked_at",
            _as_optional_utc("last_marked_at", self.last_marked_at),
        )
        if (self.first_marked_at is None) != (self.last_marked_at is None):
            raise ValueError("marked_at fields must match presence")
        for field_name in (
            "acceptable_exit_value",
            "watch_exit_value",
            "blocked_exit_value",
            "missing_settlement_exit_value",
            "blocked_or_missing_exit_value",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_optional_ratio_decimal(
            "blocked_or_missing_exit_nav_share",
            self.blocked_or_missing_exit_nav_share,
        )
        _require_ratio_decimal(
            "max_blocked_settlement_exposure_share",
            self.max_blocked_settlement_exposure_share,
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known overlay status")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_nav_settlement_risk_overlay_report(
    *,
    nav_risk_report: PaperNavRiskMetricsReport,
    settlement_timing_report: PaperSettlementTimingReport,
    config: PaperNavSettlementRiskOverlayConfig,
    generated_at: datetime,
) -> PaperNavSettlementRiskOverlayReport:
    if type(nav_risk_report) is not PaperNavRiskMetricsReport:
        raise ValueError("nav_risk_report must be a PaperNavRiskMetricsReport")
    if type(settlement_timing_report) is not PaperSettlementTimingReport:
        raise ValueError(
            "settlement_timing_report must be a PaperSettlementTimingReport",
        )
    if type(config) is not PaperNavSettlementRiskOverlayConfig:
        raise ValueError("config must be a PaperNavSettlementRiskOverlayConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_report_flags("nav_risk_report", nav_risk_report)
    _require_report_flags("settlement_timing_report", settlement_timing_report)
    _require_safety_flags(config)

    timing_rows_by_market = _timing_rows_by_market(settlement_timing_report.rows)
    rows = tuple(
        sorted(
            (
                _overlay_row_from_exposure(
                    exposure_row,
                    timing_row=timing_rows_by_market.get(exposure_row.market_slug),
                )
                for exposure_row in nav_risk_report.exposure_rows
            ),
            key=_row_sort_key,
        ),
    )
    blocked_or_missing_exit_value = _sum_decimal(
        row.exit_value
        for row in rows
        if row.overlay_status == "blocked"
    )
    blocked_or_missing_share = _optional_ratio(
        blocked_or_missing_exit_value,
        nav_risk_report.latest_exit_nav,
    )
    status = _report_status(
        rows=rows,
        blocked_or_missing_exit_value=blocked_or_missing_exit_value,
        blocked_or_missing_exit_nav_share=blocked_or_missing_share,
        max_blocked_settlement_exposure_share=(
            config.max_blocked_settlement_exposure_share
        ),
    )

    return PaperNavSettlementRiskOverlayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        nav_risk_config_version=nav_risk_report.config_version,
        settlement_timing_config_version=settlement_timing_report.config_version,
        nav_snapshot_count=nav_risk_report.nav_snapshot_count,
        first_marked_at=nav_risk_report.first_marked_at,
        last_marked_at=nav_risk_report.last_marked_at,
        settlement_row_count=settlement_timing_report.row_count,
        exposure_row_count=len(rows),
        acceptable_count=_row_status_count(rows, "acceptable"),
        watch_count=_row_status_count(rows, "watch"),
        blocked_count=_row_status_count(rows, "blocked"),
        missing_settlement_count=_missing_settlement_count(rows),
        acceptable_exit_value=_row_status_exit_value(rows, "acceptable"),
        watch_exit_value=_row_status_exit_value(rows, "watch"),
        blocked_exit_value=_explicit_blocked_exit_value(rows),
        missing_settlement_exit_value=_missing_settlement_exit_value(rows),
        blocked_or_missing_exit_value=blocked_or_missing_exit_value,
        blocked_or_missing_exit_nav_share=blocked_or_missing_share,
        max_blocked_settlement_exposure_share=(
            config.max_blocked_settlement_exposure_share
        ),
        status=status,
        rows=rows,
    )


def _overlay_row_from_exposure(
    exposure_row: object,
    *,
    timing_row: PaperSettlementTimingRow | None,
) -> PaperNavSettlementRiskOverlayRow:
    if timing_row is None:
        return PaperNavSettlementRiskOverlayRow(
            condition_id=exposure_row.condition_id,
            market_slug=exposure_row.market_slug,
            token_count=exposure_row.token_count,
            open_size=exposure_row.open_size,
            cost_basis=exposure_row.cost_basis,
            exit_value=exposure_row.exit_value,
            share_of_exit_nav=exposure_row.share_of_exit_nav,
            overlay_status="blocked",
            settlement_timing_status=None,
            timing_cost_per_share=None,
            adjusted_net_probability_edge=None,
            reason_codes=MISSING_REASON_CODES,
        )

    return PaperNavSettlementRiskOverlayRow(
        condition_id=exposure_row.condition_id,
        market_slug=exposure_row.market_slug,
        token_count=exposure_row.token_count,
        open_size=exposure_row.open_size,
        cost_basis=exposure_row.cost_basis,
        exit_value=exposure_row.exit_value,
        share_of_exit_nav=exposure_row.share_of_exit_nav,
        overlay_status=timing_row.timing_status,
        settlement_timing_status=timing_row.timing_status,
        timing_cost_per_share=timing_row.timing_cost_per_share,
        adjusted_net_probability_edge=timing_row.adjusted_net_probability_edge,
        reason_codes=timing_row.reason_codes,
    )


def _timing_rows_by_market(
    rows: tuple[PaperSettlementTimingRow, ...],
) -> dict[str, PaperSettlementTimingRow]:
    result: dict[str, PaperSettlementTimingRow] = {}
    for row in rows:
        existing = result.get(row.market_slug)
        if existing is None or _timing_row_sort_key(row) < _timing_row_sort_key(existing):
            result[row.market_slug] = row
    return result


def _timing_row_sort_key(row: PaperSettlementTimingRow) -> tuple[int, Decimal, str]:
    return (
        -TIMING_STATUS_SEVERITY[row.timing_status],
        row.adjusted_net_probability_edge,
        row.side,
    )


def _row_sort_key(
    row: PaperNavSettlementRiskOverlayRow,
) -> tuple[int, Decimal, str, str]:
    return (
        ROW_STATUS_PRIORITY[row.overlay_status],
        -row.exit_value,
        row.market_slug,
        row.condition_id,
    )


def _report_status(
    *,
    rows: tuple[PaperNavSettlementRiskOverlayRow, ...],
    blocked_or_missing_exit_value: Decimal,
    blocked_or_missing_exit_nav_share: Decimal | None,
    max_blocked_settlement_exposure_share: Decimal,
) -> str:
    if not rows:
        return "empty_nav_settlement_risk_overlay"
    if _missing_settlement_count(rows) > 0:
        return "settlement_nav_risk_blocked"
    if blocked_or_missing_exit_nav_share is None:
        if blocked_or_missing_exit_value > ZERO:
            return "settlement_nav_risk_blocked"
    elif blocked_or_missing_exit_nav_share > max_blocked_settlement_exposure_share:
        return "settlement_nav_risk_blocked"
    if any(row.overlay_status != "acceptable" for row in rows):
        return "settlement_nav_risk_watch"
    return "settlement_nav_risk_clear"


def _row_status_count(
    rows: tuple[PaperNavSettlementRiskOverlayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.overlay_status == status)


def _missing_settlement_count(rows: tuple[PaperNavSettlementRiskOverlayRow, ...]) -> int:
    return sum(1 for row in rows if row.settlement_timing_status is None)


def _row_status_exit_value(
    rows: tuple[PaperNavSettlementRiskOverlayRow, ...],
    status: str,
) -> Decimal:
    return _sum_decimal(
        row.exit_value
        for row in rows
        if row.overlay_status == status
    )


def _explicit_blocked_exit_value(
    rows: tuple[PaperNavSettlementRiskOverlayRow, ...],
) -> Decimal:
    return _sum_decimal(
        row.exit_value
        for row in rows
        if row.settlement_timing_status == "blocked"
    )


def _missing_settlement_exit_value(
    rows: tuple[PaperNavSettlementRiskOverlayRow, ...],
) -> Decimal:
    return _sum_decimal(
        row.exit_value
        for row in rows
        if row.settlement_timing_status is None
    )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        with localcontext(DECIMAL_CONTEXT):
            total += value
    return total


def _optional_ratio(
    numerator: Decimal,
    denominator: Decimal | None,
) -> Decimal | None:
    if denominator is None or denominator <= ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _validate_row_consistency(row: PaperNavSettlementRiskOverlayRow) -> None:
    if row.settlement_timing_status is None:
        if row.overlay_status != "blocked":
            raise ValueError("overlay_status must be blocked without settlement timing")
        if row.timing_cost_per_share is not None:
            raise ValueError("timing_cost_per_share must be None without settlement timing")
        if row.adjusted_net_probability_edge is not None:
            raise ValueError(
                "adjusted_net_probability_edge must be None without settlement timing",
            )
        if row.reason_codes != MISSING_REASON_CODES:
            raise ValueError("reason_codes must identify missing settlement timing")
        return
    if row.overlay_status != row.settlement_timing_status:
        raise ValueError("overlay_status must match settlement_timing_status")
    if row.timing_cost_per_share is None:
        raise ValueError("timing_cost_per_share is required with settlement timing")
    if row.adjusted_net_probability_edge is None:
        raise ValueError("adjusted_net_probability_edge is required with settlement timing")


def _validate_report_consistency(report: PaperNavSettlementRiskOverlayReport) -> None:
    if report.exposure_row_count != len(report.rows):
        raise ValueError("exposure_row_count must match rows")
    if report.acceptable_count != _row_status_count(report.rows, "acceptable"):
        raise ValueError("acceptable_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _row_status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.missing_settlement_count != _missing_settlement_count(report.rows):
        raise ValueError("missing_settlement_count must match rows")
    if report.acceptable_count + report.watch_count + report.blocked_count != len(
        report.rows,
    ):
        raise ValueError("status counts must match rows")
    if report.acceptable_exit_value != _row_status_exit_value(
        report.rows,
        "acceptable",
    ):
        raise ValueError("acceptable_exit_value must match rows")
    if report.watch_exit_value != _row_status_exit_value(report.rows, "watch"):
        raise ValueError("watch_exit_value must match rows")
    if report.blocked_exit_value != _explicit_blocked_exit_value(report.rows):
        raise ValueError("blocked_exit_value must match rows")
    if report.missing_settlement_exit_value != _missing_settlement_exit_value(
        report.rows,
    ):
        raise ValueError("missing_settlement_exit_value must match rows")
    if report.blocked_or_missing_exit_value != (
        report.blocked_exit_value + report.missing_settlement_exit_value
    ):
        raise ValueError("blocked_or_missing_exit_value must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    expected_status = _report_status(
        rows=report.rows,
        blocked_or_missing_exit_value=report.blocked_or_missing_exit_value,
        blocked_or_missing_exit_nav_share=report.blocked_or_missing_exit_nav_share,
        max_blocked_settlement_exposure_share=(
            report.max_blocked_settlement_exposure_share
        ),
    )
    if report.status != expected_status:
        raise ValueError("status must match settlement NAV overlay risk")


def _normalize_rows(
    rows: Iterable[PaperNavSettlementRiskOverlayRow],
) -> tuple[PaperNavSettlementRiskOverlayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperNavSettlementRiskOverlayRow:
            raise ValueError("rows must contain PaperNavSettlementRiskOverlayRow values")
    return normalized


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_report_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if hasattr(value, "readonly") and getattr(value, "readonly") is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: int) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be at most one")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must use ratio quantum")


def _require_optional_ratio_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_ratio_decimal(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


__all__ = (
    "PaperNavSettlementRiskOverlayConfig",
    "PaperNavSettlementRiskOverlayRow",
    "PaperNavSettlementRiskOverlayReport",
    "build_paper_nav_settlement_risk_overlay_report",
)
