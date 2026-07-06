"""Paper/report-only category exposure cap strategy support."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext


__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_EXPOSURE_CAP_V10_CONFIG_VERSION",
    "StrategyCategoryExposureCapV10Input",
    "StrategyCategoryExposureCapV10Report",
    "evaluate_strategy_category_exposure_cap_v10",
    "strategy_category_exposure_cap_v10_payload",
)


DEFAULT_STRATEGY_CATEGORY_EXPOSURE_CAP_V10_CONFIG_VERSION = (
    "strategy-category-exposure-cap-v10"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
DECIMAL_CONTEXT = Context(prec=64)

TAIL_RISK_TIERS = ("low", "medium", "high", "extreme")
CAP_STATUSES = ("pass", "watch", "blocked")
RISK_ACTIONS = ("allow", "reduce", "block")

PASS_REASON = "category_exposure_cap_v10_passed"
CAP_EXHAUSTED_REASON = "category_cap_exhausted"
CORRELATION_ELEVATED_REASON = "cluster_correlation_elevated"
CORRELATION_HIGH_REASON = "cluster_correlation_high"
TAIL_MEDIUM_REASON = "tail_risk_tier_medium"
TAIL_HIGH_REASON = "tail_risk_tier_high"
TAIL_EXTREME_REASON = "tail_risk_tier_extreme"
LIQUIDITY_WATCH_REASON = "liquidity_score_watch"
LIQUIDITY_LOW_REASON = "liquidity_score_low"
CANDIDATE_ZERO_REASON = "candidate_size_zero"
CANDIDATE_CLIPPED_REASON = "candidate_size_clipped_to_category_budget"
CANDIDATE_BLOCKED_REASON = "candidate_size_blocked_by_category_budget"

TAIL_RISK_MULTIPLIERS = {
    "low": ONE,
    "medium": Decimal("1.250000"),
    "high": Decimal("1.500000"),
    "extreme": TWO,
}
TAIL_REASON_BY_TIER = {
    "medium": TAIL_MEDIUM_REASON,
    "high": TAIL_HIGH_REASON,
    "extreme": TAIL_EXTREME_REASON,
}


@dataclass(frozen=True)
class StrategyCategoryExposureCapV10Input:
    team: str
    category: str
    current_nav_exposure: Decimal
    candidate_position_size: Decimal
    category_cap: Decimal
    cluster_correlation: Decimal
    tail_risk_tier: str
    liquidity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team", self.team)
        _require_canonical_string("category", self.category)
        for field_name in (
            "current_nav_exposure",
            "candidate_position_size",
            "category_cap",
            "cluster_correlation",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("tail_risk_tier", self.tail_risk_tier, TAIL_RISK_TIERS)
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategyCategoryExposureCapV10Report:
    config_version: str
    team: str
    category: str
    current_nav_exposure: Decimal
    candidate_position_size: Decimal
    category_cap: Decimal
    cluster_correlation: Decimal
    tail_risk_tier: str
    liquidity_score: Decimal
    remaining_category_cap: Decimal
    correlation_multiplier: Decimal
    tail_risk_multiplier: Decimal
    liquidity_multiplier: Decimal
    risk_multiplier: Decimal
    risk_adjusted_capacity: Decimal
    allowed_size: Decimal
    cap_status: str
    risk_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("team", self.team)
        _require_canonical_string("category", self.category)
        for field_name in (
            "current_nav_exposure",
            "candidate_position_size",
            "category_cap",
            "cluster_correlation",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "remaining_category_cap",
            "correlation_multiplier",
            "tail_risk_multiplier",
            "liquidity_multiplier",
            "risk_multiplier",
            "risk_adjusted_capacity",
            "allowed_size",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("tail_risk_tier", self.tail_risk_tier, TAIL_RISK_TIERS)
        _require_member("cap_status", self.cap_status, CAP_STATUSES)
        _require_member("risk_action", self.risk_action, RISK_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_report(self)
        _require_safety_flags("report", self)


def evaluate_strategy_category_exposure_cap_v10(
    row: object,
) -> StrategyCategoryExposureCapV10Report:
    if type(row) is not StrategyCategoryExposureCapV10Input:
        raise ValueError("input must be a StrategyCategoryExposureCapV10Input")
    _require_safety_flags("input", row)

    remaining_category_cap = _remaining_category_cap(row)
    correlation_multiplier = _correlation_multiplier(row.cluster_correlation)
    tail_risk_multiplier = TAIL_RISK_MULTIPLIERS[row.tail_risk_tier]
    liquidity_multiplier = _liquidity_multiplier(row.liquidity_score)
    risk_multiplier = _multiply_decimal(
        _multiply_decimal(correlation_multiplier, tail_risk_multiplier),
        liquidity_multiplier,
    )
    risk_adjusted_capacity = _risk_adjusted_capacity(
        remaining_category_cap,
        risk_multiplier,
    )
    allowed_size = _min_decimal(row.candidate_position_size, risk_adjusted_capacity)
    risk_action = _risk_action(
        candidate_position_size=row.candidate_position_size,
        allowed_size=allowed_size,
    )
    cap_status = _cap_status(
        candidate_position_size=row.candidate_position_size,
        allowed_size=allowed_size,
        reason_codes=_context_reason_codes(row, remaining_category_cap),
    )
    reason_codes = _reason_codes(
        row=row,
        remaining_category_cap=remaining_category_cap,
        allowed_size=allowed_size,
    )

    return StrategyCategoryExposureCapV10Report(
        config_version=DEFAULT_STRATEGY_CATEGORY_EXPOSURE_CAP_V10_CONFIG_VERSION,
        team=row.team,
        category=row.category,
        current_nav_exposure=row.current_nav_exposure,
        candidate_position_size=row.candidate_position_size,
        category_cap=row.category_cap,
        cluster_correlation=row.cluster_correlation,
        tail_risk_tier=row.tail_risk_tier,
        liquidity_score=row.liquidity_score,
        remaining_category_cap=remaining_category_cap,
        correlation_multiplier=correlation_multiplier,
        tail_risk_multiplier=tail_risk_multiplier,
        liquidity_multiplier=liquidity_multiplier,
        risk_multiplier=risk_multiplier,
        risk_adjusted_capacity=risk_adjusted_capacity,
        allowed_size=allowed_size,
        cap_status=cap_status,
        risk_action=risk_action,
        reason_codes=reason_codes,
    )


def strategy_category_exposure_cap_v10_payload(
    report: object,
) -> dict[str, object]:
    if type(report) is not StrategyCategoryExposureCapV10Report:
        raise ValueError("report must be a StrategyCategoryExposureCapV10Report")
    _require_safety_flags("report", report)
    return {
        "config_version": report.config_version,
        "team": report.team,
        "category": report.category,
        "current_nav_exposure": _decimal_payload(report.current_nav_exposure),
        "candidate_position_size": _decimal_payload(report.candidate_position_size),
        "category_cap": _decimal_payload(report.category_cap),
        "cluster_correlation": _decimal_payload(report.cluster_correlation),
        "tail_risk_tier": report.tail_risk_tier,
        "liquidity_score": _decimal_payload(report.liquidity_score),
        "remaining_category_cap": _decimal_payload(report.remaining_category_cap),
        "correlation_multiplier": _decimal_payload(report.correlation_multiplier),
        "tail_risk_multiplier": _decimal_payload(report.tail_risk_multiplier),
        "liquidity_multiplier": _decimal_payload(report.liquidity_multiplier),
        "risk_multiplier": _decimal_payload(report.risk_multiplier),
        "risk_adjusted_capacity": _decimal_payload(report.risk_adjusted_capacity),
        "allowed_size": _decimal_payload(report.allowed_size),
        "cap_status": report.cap_status,
        "risk_action": report.risk_action,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _remaining_category_cap(row: StrategyCategoryExposureCapV10Input) -> Decimal:
    remaining = _subtract_decimal(row.category_cap, row.current_nav_exposure)
    if remaining <= ZERO:
        return ZERO
    return remaining


def _correlation_multiplier(cluster_correlation: Decimal) -> Decimal:
    return _add_decimal(ONE, cluster_correlation)


def _liquidity_multiplier(liquidity_score: Decimal) -> Decimal:
    return _subtract_decimal(TWO, liquidity_score)


def _risk_adjusted_capacity(
    remaining_category_cap: Decimal,
    risk_multiplier: Decimal,
) -> Decimal:
    if remaining_category_cap <= ZERO:
        return ZERO
    return _divide_decimal(remaining_category_cap, risk_multiplier)


def _context_reason_codes(
    row: StrategyCategoryExposureCapV10Input,
    remaining_category_cap: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if remaining_category_cap <= ZERO:
        reasons.append(CAP_EXHAUSTED_REASON)
    if row.cluster_correlation >= Decimal("0.800000"):
        reasons.append(CORRELATION_HIGH_REASON)
    elif row.cluster_correlation >= Decimal("0.400000"):
        reasons.append(CORRELATION_ELEVATED_REASON)
    tail_reason = TAIL_REASON_BY_TIER.get(row.tail_risk_tier)
    if tail_reason is not None:
        reasons.append(tail_reason)
    if row.liquidity_score <= Decimal("0.250000"):
        reasons.append(LIQUIDITY_LOW_REASON)
    elif row.liquidity_score < Decimal("0.700000"):
        reasons.append(LIQUIDITY_WATCH_REASON)
    return tuple(reasons)


def _reason_codes(
    *,
    row: StrategyCategoryExposureCapV10Input,
    remaining_category_cap: Decimal,
    allowed_size: Decimal,
) -> tuple[str, ...]:
    reasons = list(_context_reason_codes(row, remaining_category_cap))
    if row.candidate_position_size <= ZERO:
        reasons.append(CANDIDATE_ZERO_REASON)
    elif allowed_size <= ZERO:
        reasons.append(CANDIDATE_BLOCKED_REASON)
    elif allowed_size < row.candidate_position_size:
        reasons.append(CANDIDATE_CLIPPED_REASON)
    elif not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons), require_nonempty=True)


def _risk_action(
    *,
    candidate_position_size: Decimal,
    allowed_size: Decimal,
) -> str:
    if candidate_position_size > ZERO and allowed_size <= ZERO:
        return "block"
    if allowed_size < candidate_position_size:
        return "reduce"
    return "allow"


def _cap_status(
    *,
    candidate_position_size: Decimal,
    allowed_size: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    if candidate_position_size <= ZERO:
        return "pass"
    if allowed_size <= ZERO:
        return "blocked"
    if allowed_size < candidate_position_size:
        return "watch"
    if reason_codes:
        return "watch"
    return "pass"


def _validate_report(report: StrategyCategoryExposureCapV10Report) -> None:
    if report.remaining_category_cap != _remaining_category_cap(
        StrategyCategoryExposureCapV10Input(
            team=report.team,
            category=report.category,
            current_nav_exposure=report.current_nav_exposure,
            candidate_position_size=report.candidate_position_size,
            category_cap=report.category_cap,
            cluster_correlation=report.cluster_correlation,
            tail_risk_tier=report.tail_risk_tier,
            liquidity_score=report.liquidity_score,
        ),
    ):
        raise ValueError("remaining_category_cap must match cap less current exposure")
    if report.correlation_multiplier != _correlation_multiplier(report.cluster_correlation):
        raise ValueError("correlation_multiplier must match cluster_correlation")
    if report.tail_risk_multiplier != TAIL_RISK_MULTIPLIERS[report.tail_risk_tier]:
        raise ValueError("tail_risk_multiplier must match tail_risk_tier")
    if report.liquidity_multiplier != _liquidity_multiplier(report.liquidity_score):
        raise ValueError("liquidity_multiplier must match liquidity_score")
    expected_risk_multiplier = _multiply_decimal(
        _multiply_decimal(report.correlation_multiplier, report.tail_risk_multiplier),
        report.liquidity_multiplier,
    )
    if report.risk_multiplier != expected_risk_multiplier:
        raise ValueError("risk_multiplier must match component multipliers")
    if report.risk_adjusted_capacity != _risk_adjusted_capacity(
        report.remaining_category_cap,
        report.risk_multiplier,
    ):
        raise ValueError("risk_adjusted_capacity must match remaining cap and risk multiplier")
    if report.allowed_size != _min_decimal(
        report.candidate_position_size,
        report.risk_adjusted_capacity,
    ):
        raise ValueError("allowed_size must match candidate and risk-adjusted capacity")
    expected_action = _risk_action(
        candidate_position_size=report.candidate_position_size,
        allowed_size=report.allowed_size,
    )
    if report.risk_action != expected_action:
        raise ValueError("risk_action must match allowed_size")
    context_reasons = _context_reason_codes(
        StrategyCategoryExposureCapV10Input(
            team=report.team,
            category=report.category,
            current_nav_exposure=report.current_nav_exposure,
            candidate_position_size=report.candidate_position_size,
            category_cap=report.category_cap,
            cluster_correlation=report.cluster_correlation,
            tail_risk_tier=report.tail_risk_tier,
            liquidity_score=report.liquidity_score,
        ),
        report.remaining_category_cap,
    )
    expected_status = _cap_status(
        candidate_position_size=report.candidate_position_size,
        allowed_size=report.allowed_size,
        reason_codes=context_reasons,
    )
    if report.cap_status != expected_status:
        raise ValueError("cap_status must match allowed_size and context risks")
    expected_reasons = _reason_codes(
        row=StrategyCategoryExposureCapV10Input(
            team=report.team,
            category=report.category,
            current_nav_exposure=report.current_nav_exposure,
            candidate_position_size=report.candidate_position_size,
            category_cap=report.category_cap,
            cluster_correlation=report.cluster_correlation,
            tail_risk_tier=report.tail_risk_tier,
            liquidity_score=report.liquidity_score,
        ),
        remaining_category_cap=report.remaining_category_cap,
        allowed_size=report.allowed_size,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match category exposure cap state")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _add_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first + second).quantize(QUANTUM)


def _subtract_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first - second).quantize(QUANTUM)


def _multiply_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first * second).quantize(QUANTUM)


def _divide_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first / second).quantize(QUANTUM)


def _min_decimal(first: Decimal, second: Decimal) -> Decimal:
    if first <= second:
        return _normalize_decimal("minimum Decimal", first)
    return _normalize_decimal("minimum Decimal", second)


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    if isinstance(values, (set, frozenset)):
        raise ValueError("reason_codes must be an ordered iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")
