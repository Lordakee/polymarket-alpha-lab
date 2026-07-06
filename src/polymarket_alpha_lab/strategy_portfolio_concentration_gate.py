"""Paper-only portfolio concentration gate for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext


__all__ = (
    "StrategyPortfolioConcentrationGateConfig",
    "StrategyPortfolioConcentrationGateReport",
    "evaluate_strategy_portfolio_concentration_gate",
    "strategy_portfolio_concentration_gate_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-portfolio-concentration-gate-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
CONCENTRATION_STATUSES = ("pass", "watch", "blocked")
PASS_REASON_CODE = "portfolio_concentration_pass"
CANDIDATE_EXCEEDS_ALLOWED_REASON_CODE = "candidate_notional_exceeds_allowed"
WATCH_REASON_CODES = (
    "category_concentration_watch",
    "team_concentration_watch",
    "event_cluster_concentration_watch",
)
BLOCK_REASON_CODES = (
    "category_concentration_block",
    "team_concentration_block",
    "event_cluster_concentration_block",
)
ALL_REASON_CODES = (
    PASS_REASON_CODE,
    *WATCH_REASON_CODES,
    *BLOCK_REASON_CODES,
    CANDIDATE_EXCEEDS_ALLOWED_REASON_CODE,
)
DECIMAL_CONTEXT = Context(prec=64)


@dataclass(frozen=True)
class StrategyPortfolioConcentrationGateConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    category_watch_share: Decimal = Decimal("0.200000")
    category_block_share: Decimal = Decimal("0.300000")
    team_watch_share: Decimal = Decimal("0.150000")
    team_block_share: Decimal = Decimal("0.250000")
    event_cluster_watch_share: Decimal = Decimal("0.100000")
    event_cluster_block_share: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_watch_share",
            "category_block_share",
            "team_watch_share",
            "team_block_share",
            "event_cluster_watch_share",
            "event_cluster_block_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_block(
            "category",
            self.category_watch_share,
            self.category_block_share,
        )
        _require_watch_not_above_block(
            "team",
            self.team_watch_share,
            self.team_block_share,
        )
        _require_watch_not_above_block(
            "event_cluster",
            self.event_cluster_watch_share,
            self.event_cluster_block_share,
        )
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyPortfolioConcentrationGateReport:
    config_version: str
    category_exposure: Decimal
    team_exposure: Decimal
    event_cluster_exposure: Decimal
    candidate_notional: Decimal
    nav: Decimal
    post_trade_category_exposure: Decimal
    post_trade_team_exposure: Decimal
    post_trade_event_cluster_exposure: Decimal
    category_exposure_share: Decimal
    team_exposure_share: Decimal
    event_cluster_exposure_share: Decimal
    category_allowed_notional: Decimal
    team_allowed_notional: Decimal
    event_cluster_allowed_notional: Decimal
    allowed_notional: Decimal
    concentration_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_exposure",
            "team_exposure",
            "event_cluster_exposure",
            "candidate_notional",
            "post_trade_category_exposure",
            "post_trade_team_exposure",
            "post_trade_event_cluster_exposure",
            "category_exposure_share",
            "team_exposure_share",
            "event_cluster_exposure_share",
            "category_allowed_notional",
            "team_allowed_notional",
            "event_cluster_allowed_notional",
            "allowed_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "nav", _normalize_positive_decimal("nav", self.nav))
        _require_member(
            "concentration_status",
            self.concentration_status,
            CONCENTRATION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_safety_flags("report", self)


def evaluate_strategy_portfolio_concentration_gate(
    *,
    category_exposure: Decimal,
    team_exposure: Decimal,
    event_cluster_exposure: Decimal,
    candidate_notional: Decimal,
    nav: Decimal,
    config: StrategyPortfolioConcentrationGateConfig,
) -> StrategyPortfolioConcentrationGateReport:
    if type(config) is not StrategyPortfolioConcentrationGateConfig:
        raise ValueError("config must be a StrategyPortfolioConcentrationGateConfig")
    _require_safety_flags("config", config)

    category_exposure = _normalize_nonnegative_decimal(
        "category_exposure",
        category_exposure,
    )
    team_exposure = _normalize_nonnegative_decimal("team_exposure", team_exposure)
    event_cluster_exposure = _normalize_nonnegative_decimal(
        "event_cluster_exposure",
        event_cluster_exposure,
    )
    candidate_notional = _normalize_nonnegative_decimal(
        "candidate_notional",
        candidate_notional,
    )
    nav = _normalize_positive_decimal("nav", nav)

    post_trade_category_exposure = _add_decimal(category_exposure, candidate_notional)
    post_trade_team_exposure = _add_decimal(team_exposure, candidate_notional)
    post_trade_event_cluster_exposure = _add_decimal(
        event_cluster_exposure,
        candidate_notional,
    )
    category_allowed_notional = _remaining_notional(
        category_exposure,
        nav,
        config.category_block_share,
    )
    team_allowed_notional = _remaining_notional(
        team_exposure,
        nav,
        config.team_block_share,
    )
    event_cluster_allowed_notional = _remaining_notional(
        event_cluster_exposure,
        nav,
        config.event_cluster_block_share,
    )
    allowed_notional = min(
        candidate_notional,
        category_allowed_notional,
        team_allowed_notional,
        event_cluster_allowed_notional,
    )
    category_exposure_share = _ratio_decimal(post_trade_category_exposure, nav)
    team_exposure_share = _ratio_decimal(post_trade_team_exposure, nav)
    event_cluster_exposure_share = _ratio_decimal(
        post_trade_event_cluster_exposure,
        nav,
    )
    status, reason_codes = _status_and_reason_codes(
        category_exposure_share=category_exposure_share,
        team_exposure_share=team_exposure_share,
        event_cluster_exposure_share=event_cluster_exposure_share,
        candidate_notional=candidate_notional,
        allowed_notional=allowed_notional,
        config=config,
    )

    return StrategyPortfolioConcentrationGateReport(
        config_version=config.config_version,
        category_exposure=category_exposure,
        team_exposure=team_exposure,
        event_cluster_exposure=event_cluster_exposure,
        candidate_notional=candidate_notional,
        nav=nav,
        post_trade_category_exposure=post_trade_category_exposure,
        post_trade_team_exposure=post_trade_team_exposure,
        post_trade_event_cluster_exposure=post_trade_event_cluster_exposure,
        category_exposure_share=category_exposure_share,
        team_exposure_share=team_exposure_share,
        event_cluster_exposure_share=event_cluster_exposure_share,
        category_allowed_notional=category_allowed_notional,
        team_allowed_notional=team_allowed_notional,
        event_cluster_allowed_notional=event_cluster_allowed_notional,
        allowed_notional=allowed_notional,
        concentration_status=status,
        reason_codes=reason_codes,
    )


def strategy_portfolio_concentration_gate_payload(
    report: StrategyPortfolioConcentrationGateReport,
) -> dict[str, object]:
    if type(report) is not StrategyPortfolioConcentrationGateReport:
        raise ValueError("report must be a StrategyPortfolioConcentrationGateReport")
    _require_safety_flags("report", report)
    return {
        "config_version": report.config_version,
        "category_exposure": _decimal_payload(report.category_exposure),
        "team_exposure": _decimal_payload(report.team_exposure),
        "event_cluster_exposure": _decimal_payload(report.event_cluster_exposure),
        "candidate_notional": _decimal_payload(report.candidate_notional),
        "nav": _decimal_payload(report.nav),
        "post_trade_category_exposure": _decimal_payload(
            getattr(report, "post_trade_category_exposure"),
        ),
        "post_trade_team_exposure": _decimal_payload(
            getattr(report, "post_trade_team_exposure"),
        ),
        "post_trade_event_cluster_exposure": _decimal_payload(
            getattr(report, "post_trade_event_cluster_exposure"),
        ),
        "category_exposure_share": _decimal_payload(report.category_exposure_share),
        "team_exposure_share": _decimal_payload(report.team_exposure_share),
        "event_cluster_exposure_share": _decimal_payload(
            report.event_cluster_exposure_share,
        ),
        "category_allowed_notional": _decimal_payload(
            report.category_allowed_notional,
        ),
        "team_allowed_notional": _decimal_payload(report.team_allowed_notional),
        "event_cluster_allowed_notional": _decimal_payload(
            report.event_cluster_allowed_notional,
        ),
        "allowed_notional": _decimal_payload(report.allowed_notional),
        "concentration_status": report.concentration_status,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _status_and_reason_codes(
    *,
    category_exposure_share: Decimal,
    team_exposure_share: Decimal,
    event_cluster_exposure_share: Decimal,
    candidate_notional: Decimal,
    allowed_notional: Decimal,
    config: StrategyPortfolioConcentrationGateConfig,
) -> tuple[str, tuple[str, ...]]:
    block_codes: list[str] = []
    watch_codes: list[str] = []
    if category_exposure_share > config.category_block_share:
        block_codes.append("category_concentration_block")
    elif category_exposure_share > config.category_watch_share:
        watch_codes.append("category_concentration_watch")
    if team_exposure_share > config.team_block_share:
        block_codes.append("team_concentration_block")
    elif team_exposure_share > config.team_watch_share:
        watch_codes.append("team_concentration_watch")
    if event_cluster_exposure_share > config.event_cluster_block_share:
        block_codes.append("event_cluster_concentration_block")
    elif event_cluster_exposure_share > config.event_cluster_watch_share:
        watch_codes.append("event_cluster_concentration_watch")

    if block_codes:
        codes = tuple(block_codes)
        if candidate_notional > allowed_notional:
            codes = (*codes, CANDIDATE_EXCEEDS_ALLOWED_REASON_CODE)
        return "blocked", codes
    if watch_codes:
        return "watch", tuple(watch_codes)
    return "pass", (PASS_REASON_CODE,)


def _remaining_notional(
    exposure: Decimal,
    nav: Decimal,
    block_share: Decimal,
) -> Decimal:
    return _max_decimal(_subtract_decimal(_multiply_decimal(nav, block_share), exposure), _zero())


def _validate_report(report: StrategyPortfolioConcentrationGateReport) -> None:
    if getattr(report, "post_trade_category_exposure") != _add_decimal(
        report.category_exposure,
        report.candidate_notional,
    ):
        raise ValueError("post_trade_category_exposure must match inputs")
    if getattr(report, "post_trade_team_exposure") != _add_decimal(
        report.team_exposure,
        report.candidate_notional,
    ):
        raise ValueError("post_trade_team_exposure must match inputs")
    if getattr(report, "post_trade_event_cluster_exposure") != _add_decimal(
        report.event_cluster_exposure,
        report.candidate_notional,
    ):
        raise ValueError("post_trade_event_cluster_exposure must match inputs")
    if report.category_exposure_share != _ratio_decimal(
        getattr(report, "post_trade_category_exposure"),
        report.nav,
    ):
        raise ValueError("category_exposure_share must match inputs")
    if report.team_exposure_share != _ratio_decimal(
        getattr(report, "post_trade_team_exposure"),
        report.nav,
    ):
        raise ValueError("team_exposure_share must match inputs")
    if report.event_cluster_exposure_share != _ratio_decimal(
        getattr(report, "post_trade_event_cluster_exposure"),
        report.nav,
    ):
        raise ValueError("event_cluster_exposure_share must match inputs")
    if report.allowed_notional != min(
        report.candidate_notional,
        report.category_allowed_notional,
        report.team_allowed_notional,
        report.event_cluster_allowed_notional,
    ):
        raise ValueError("allowed_notional must match the tightest cap")
    if report.concentration_status == "pass" and report.reason_codes != (
        PASS_REASON_CODE,
    ):
        raise ValueError("pass reports must include only the pass reason")
    if report.concentration_status == "watch" and not any(
        reason_code in WATCH_REASON_CODES for reason_code in report.reason_codes
    ):
        raise ValueError("watch reports must include a watch reason")
    if report.concentration_status == "blocked" and not any(
        reason_code in BLOCK_REASON_CODES for reason_code in report.reason_codes
    ):
        raise ValueError("blocked reports must include a block reason")


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_watch_not_above_block(
    label: str,
    watch_share: Decimal,
    block_share: Decimal,
) -> None:
    if block_share < watch_share:
        raise ValueError(f"{label}_block_share must not be below {label}_watch_share")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        if reason_code not in ALL_REASON_CODES:
            raise ValueError("reason_codes contains an unknown reason code")
    return tuple(dict.fromkeys(values))


def _add_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first + second).quantize(QUANTUM)


def _subtract_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first - second).quantize(QUANTUM)


def _multiply_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first * second).quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _max_decimal(first: Decimal, second: Decimal) -> Decimal:
    return first if first >= second else second


def _zero() -> Decimal:
    return ZERO.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload value must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload value must be finite")
    return str(value)
