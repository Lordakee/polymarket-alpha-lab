from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext


DEFAULT_CONFIG_VERSION = "portfolio-probability-event-exposure-report-v0"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
RISK_STATUSES = ("clear", "watch", "block")
RISK_STATUS_RANK = {"block": 0, "watch": 1, "clear": 2}
REASON_SEQUENCE = (
    "domain_concentration_block",
    "correlation_concentration_block",
    "domain_concentration_watch",
    "correlation_concentration_watch",
    "low_liquidity_depth",
    "settlement_window_block",
    "settlement_window_watch",
    "probability_event_exposure_clear",
)


@dataclass(frozen=True)
class PortfolioProbabilityEventExposureConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    domain_watch_concentration: Decimal = Decimal("0.500000")
    domain_block_concentration: Decimal = Decimal("0.650000")
    correlation_watch_concentration: Decimal = Decimal("0.500000")
    correlation_block_concentration: Decimal = Decimal("0.650000")
    settlement_window_watch_seconds: Decimal = Decimal("900")
    settlement_window_block_seconds: Decimal = Decimal("3600")
    minimum_liquidity_depth_usdc: Decimal = Decimal("10.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "domain_watch_concentration",
            "domain_block_concentration",
            "correlation_watch_concentration",
            "correlation_block_concentration",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_window_watch_seconds",
            "settlement_window_block_seconds",
            "minimum_liquidity_depth_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.domain_watch_concentration > self.domain_block_concentration:
            raise ValueError(
                "domain_watch_concentration must not exceed domain_block_concentration",
            )
        if self.correlation_watch_concentration > self.correlation_block_concentration:
            raise ValueError(
                "correlation_watch_concentration must not exceed correlation_block_concentration",
            )
        if self.settlement_window_watch_seconds > self.settlement_window_block_seconds:
            raise ValueError(
                "settlement_window_watch_seconds must not exceed settlement_window_block_seconds",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class PortfolioProbabilityEventExposureInput:
    market_id: str
    domain: str
    team: str
    yes_probability_exposure: Decimal
    no_probability_exposure: Decimal
    settlement_window_seconds: Decimal
    liquidity_depth_usdc: Decimal
    correlation_bucket: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "domain", "team", "correlation_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "yes_probability_exposure",
            "no_probability_exposure",
            "settlement_window_seconds",
            "liquidity_depth_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("input", self)


@dataclass(frozen=True)
class PortfolioProbabilityEventExposureRow:
    market_id: str
    domain: str
    team: str
    yes_probability_exposure: Decimal
    no_probability_exposure: Decimal
    net_probability_exposure: Decimal
    absolute_net_probability_exposure: Decimal
    domain_concentration: Decimal
    correlation_bucket: str
    correlation_concentration: Decimal
    settlement_window_seconds: Decimal
    settlement_window_risk_band: str
    liquidity_depth_usdc: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "domain", "team", "correlation_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "yes_probability_exposure",
            "no_probability_exposure",
            "absolute_net_probability_exposure",
            "domain_concentration",
            "correlation_concentration",
            "settlement_window_seconds",
            "liquidity_depth_usdc",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_probability_exposure",
            _require_decimal("net_probability_exposure", self.net_probability_exposure),
        )
        object.__setattr__(
            self,
            "settlement_window_risk_band",
            _require_member(
                "settlement_window_risk_band",
                self.settlement_window_risk_band,
                RISK_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_member("report_status", self.report_status, RISK_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class PortfolioProbabilityEventExposureReport:
    config_version: str
    market_count: Decimal
    total_yes_probability_exposure: Decimal
    total_no_probability_exposure: Decimal
    net_probability_exposure: Decimal
    max_domain_concentration: Decimal
    max_correlation_concentration: Decimal
    blocker_count: Decimal
    attention_count: Decimal
    clear_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PortfolioProbabilityEventExposureRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "market_count",
            "blocker_count",
            "attention_count",
            "clear_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_yes_probability_exposure",
            "total_no_probability_exposure",
            "max_domain_concentration",
            "max_correlation_concentration",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_probability_exposure",
            _require_decimal("net_probability_exposure", self.net_probability_exposure),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_member("report_status", self.report_status, RISK_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reasons(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_flags("report", self)


def build_portfolio_probability_event_exposure_report(
    exposures: Iterable[PortfolioProbabilityEventExposureInput],
    *,
    config: PortfolioProbabilityEventExposureConfig,
) -> PortfolioProbabilityEventExposureReport:
    if type(config) is not PortfolioProbabilityEventExposureConfig:
        raise ValueError("config must be PortfolioProbabilityEventExposureConfig")
    _require_flags("config", config)
    input_rows = tuple(exposures)
    for row in input_rows:
        if type(row) is not PortfolioProbabilityEventExposureInput:
            raise ValueError("rows must contain PortfolioProbabilityEventExposureInput")
        _require_flags("input", row)

    total_yes = _sum_decimal(row.yes_probability_exposure for row in input_rows)
    total_no = _sum_decimal(row.no_probability_exposure for row in input_rows)
    total_gross = _sum_decimal(
        row.yes_probability_exposure + row.no_probability_exposure
        for row in input_rows
    )
    domain_totals = _bucket_totals(input_rows, "domain")
    correlation_totals = _bucket_totals(input_rows, "correlation_bucket")
    rows = tuple(
        sorted(
            (
                _report_row(
                    row,
                    config=config,
                    total_gross=total_gross,
                    domain_total=domain_totals[row.domain],
                    correlation_total=correlation_totals[row.correlation_bucket],
                )
                for row in input_rows
            ),
            key=lambda row: row.market_id,
        ),
    )
    reason_codes = _report_reasons(rows)
    return PortfolioProbabilityEventExposureReport(
        config_version=config.config_version,
        market_count=_count_decimal(len(rows)),
        total_yes_probability_exposure=total_yes,
        total_no_probability_exposure=total_no,
        net_probability_exposure=_quantize(total_yes - total_no),
        max_domain_concentration=_max_decimal(
            (row.domain_concentration for row in rows),
        ),
        max_correlation_concentration=_max_decimal(
            (row.correlation_concentration for row in rows),
        ),
        blocker_count=_count_decimal(
            sum(1 for row in rows if row.report_status == "block"),
        ),
        attention_count=_count_decimal(
            sum(1 for row in rows if row.report_status == "watch"),
        ),
        clear_count=_count_decimal(
            sum(1 for row in rows if row.report_status == "clear"),
        ),
        report_status=_highest_status(rows),
        reason_codes=reason_codes,
        rows=rows,
    )


def _report_row(
    row: PortfolioProbabilityEventExposureInput,
    *,
    config: PortfolioProbabilityEventExposureConfig,
    total_gross: Decimal,
    domain_total: Decimal,
    correlation_total: Decimal,
) -> PortfolioProbabilityEventExposureRow:
    net_exposure = _quantize(row.yes_probability_exposure - row.no_probability_exposure)
    absolute_net_exposure = _quantize(abs(net_exposure))
    domain_concentration = _ratio(domain_total, total_gross)
    correlation_concentration = _ratio(correlation_total, total_gross)
    settlement_band = _settlement_band(row.settlement_window_seconds, config)
    reason_codes = _row_reasons(
        domain_concentration=domain_concentration,
        correlation_concentration=correlation_concentration,
        settlement_band=settlement_band,
        liquidity_depth_usdc=row.liquidity_depth_usdc,
        config=config,
    )
    status = _row_status(reason_codes)
    return PortfolioProbabilityEventExposureRow(
        market_id=row.market_id,
        domain=row.domain,
        team=row.team,
        yes_probability_exposure=row.yes_probability_exposure,
        no_probability_exposure=row.no_probability_exposure,
        net_probability_exposure=net_exposure,
        absolute_net_probability_exposure=absolute_net_exposure,
        domain_concentration=domain_concentration,
        correlation_bucket=row.correlation_bucket,
        correlation_concentration=correlation_concentration,
        settlement_window_seconds=row.settlement_window_seconds,
        settlement_window_risk_band=settlement_band,
        liquidity_depth_usdc=row.liquidity_depth_usdc,
        report_status=status,
        reason_codes=reason_codes,
    )


def _row_reasons(
    *,
    domain_concentration: Decimal,
    correlation_concentration: Decimal,
    settlement_band: str,
    liquidity_depth_usdc: Decimal,
    config: PortfolioProbabilityEventExposureConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if domain_concentration >= config.domain_block_concentration:
        reasons.append("domain_concentration_block")
    elif domain_concentration >= config.domain_watch_concentration:
        reasons.append("domain_concentration_watch")
    if correlation_concentration >= config.correlation_block_concentration:
        reasons.append("correlation_concentration_block")
    elif correlation_concentration >= config.correlation_watch_concentration:
        reasons.append("correlation_concentration_watch")
    if liquidity_depth_usdc < config.minimum_liquidity_depth_usdc:
        reasons.append("low_liquidity_depth")
    if settlement_band == "block":
        reasons.append("settlement_window_block")
    elif settlement_band == "watch":
        reasons.append("settlement_window_watch")
    if not reasons:
        reasons.append("probability_event_exposure_clear")
    return tuple(reason for reason in REASON_SEQUENCE if reason in reasons)


def _report_reasons(
    rows: tuple[PortfolioProbabilityEventExposureRow, ...],
) -> tuple[str, ...]:
    reasons = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "probability_event_exposure_clear"
    }
    if not reasons:
        return ("probability_event_exposure_clear",)
    return tuple(reason for reason in REASON_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes != ("probability_event_exposure_clear",):
        return "watch"
    return "clear"


def _highest_status(rows: tuple[PortfolioProbabilityEventExposureRow, ...]) -> str:
    if any(row.report_status == "block" for row in rows):
        return "block"
    if any(row.report_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _settlement_band(
    settlement_window_seconds: Decimal,
    config: PortfolioProbabilityEventExposureConfig,
) -> str:
    if settlement_window_seconds >= config.settlement_window_block_seconds:
        return "block"
    if settlement_window_seconds >= config.settlement_window_watch_seconds:
        return "watch"
    return "clear"


def _bucket_totals(
    rows: tuple[PortfolioProbabilityEventExposureInput, ...],
    field_name: str,
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        key = getattr(row, field_name)
        current = totals.get(key, ZERO)
        totals[key] = _quantize(
            current + row.yes_probability_exposure + row.no_probability_exposure,
        )
    return totals


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > Decimal("1.000000"):
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return decimal_value


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be text")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if normalized != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _normalize_reasons(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason in normalized:
        if reason not in REASON_SEQUENCE:
            raise ValueError("reason_codes must be known")
    expected = tuple(reason for reason in REASON_SEQUENCE if reason in set(normalized))
    if normalized != expected:
        raise ValueError("reason_codes must be sorted and unique")
    return normalized


def _normalize_rows(
    rows: Iterable[PortfolioProbabilityEventExposureRow],
) -> tuple[PortfolioProbabilityEventExposureRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PortfolioProbabilityEventExposureRow:
            raise ValueError("rows must contain PortfolioProbabilityEventExposureRow")
    if normalized != tuple(sorted(normalized, key=lambda row: row.market_id)):
        raise ValueError("rows must be sorted")
    return normalized


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _validate_row_consistency(row: PortfolioProbabilityEventExposureRow) -> None:
    if row.net_probability_exposure != _quantize(
        row.yes_probability_exposure - row.no_probability_exposure,
    ):
        raise ValueError("net_probability_exposure must match yes minus no")
    if row.absolute_net_probability_exposure != _quantize(
        abs(row.net_probability_exposure),
    ):
        raise ValueError("absolute_net_probability_exposure must match net exposure")
    if row.report_status != _row_status(row.reason_codes):
        raise ValueError("report_status must match reason_codes")
    if row.settlement_window_risk_band == "block" and (
        "settlement_window_block" not in row.reason_codes
    ):
        raise ValueError("settlement_window_risk_band must match reasons")
    if row.settlement_window_risk_band == "watch" and (
        "settlement_window_watch" not in row.reason_codes
    ):
        raise ValueError("settlement_window_risk_band must match reasons")


def _validate_report_consistency(
    report: PortfolioProbabilityEventExposureReport,
) -> None:
    if report.market_count != _count_decimal(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.total_yes_probability_exposure != _sum_decimal(
        row.yes_probability_exposure for row in report.rows
    ):
        raise ValueError("total_yes_probability_exposure must match rows")
    if report.total_no_probability_exposure != _sum_decimal(
        row.no_probability_exposure for row in report.rows
    ):
        raise ValueError("total_no_probability_exposure must match rows")
    if report.net_probability_exposure != _quantize(
        report.total_yes_probability_exposure - report.total_no_probability_exposure,
    ):
        raise ValueError("net_probability_exposure must match totals")
    if report.max_domain_concentration != _max_decimal(
        row.domain_concentration for row in report.rows
    ):
        raise ValueError("max_domain_concentration must match rows")
    if report.max_correlation_concentration != _max_decimal(
        row.correlation_concentration for row in report.rows
    ):
        raise ValueError("max_correlation_concentration must match rows")
    if report.blocker_count != _count_decimal(
        sum(1 for row in report.rows if row.report_status == "block"),
    ):
        raise ValueError("blocker_count must match rows")
    if report.attention_count != _count_decimal(
        sum(1 for row in report.rows if row.report_status == "watch"),
    ):
        raise ValueError("attention_count must match rows")
    if report.clear_count != _count_decimal(
        sum(1 for row in report.rows if row.report_status == "clear"),
    ):
        raise ValueError("clear_count must match rows")
    if report.report_status != _highest_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reasons(report.rows):
        raise ValueError("reason_codes must match rows")
