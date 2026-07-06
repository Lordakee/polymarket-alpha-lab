"""Typed paper-only sizing risk budget v4 reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256


__all__ = (
    "StrategySizingRiskBudgetV4Candidate",
    "StrategySizingRiskBudgetV4Config",
    "StrategySizingRiskBudgetV4Decision",
    "build_strategy_sizing_risk_budget_v4",
    "strategy_sizing_risk_budget_v4_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-sizing-risk-budget-v4"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)
SIZING_STATUSES = ("pass", "watch", "blocked")
PASS_REASON_CODE = "strategy_sizing_risk_budget_v4_pass"
WATCH_REASON_CODE = "strategy_sizing_risk_budget_v4_watch"
BLOCK_REASON_CODE = "strategy_sizing_risk_budget_v4_block"
TERMINAL_REASON_BY_STATUS = {
    "pass": PASS_REASON_CODE,
    "watch": WATCH_REASON_CODE,
    "blocked": BLOCK_REASON_CODE,
}
TERMINAL_REASON_CODES = frozenset(TERMINAL_REASON_BY_STATUS.values())
DIAGNOSTIC_REASON_CODES = frozenset(
    (
        "expected_value_below_minimum",
        "expected_value_watch",
        "expected_value_pass",
        "liquidity_capacity_exhausted",
        "liquidity_capacity_limited",
        "liquidity_capacity_available",
        "team_allocation_cap_exhausted",
        "team_allocation_cap_limited",
        "team_allocation_capacity_available",
        "market_correlation_cluster_cap_exhausted",
        "market_correlation_cluster_cap_limited",
        "market_correlation_cluster_capacity_available",
        "resolution_risk_high",
        "resolution_risk_watch",
        "resolution_risk_contained",
    ),
)
REDUCER_OWNED_REASON_CODES = TERMINAL_REASON_CODES | DIAGNOSTIC_REASON_CODES
SENSITIVE_REFERENCE_TOKENS = (
    "auth",
    "bearer",
    "credential",
    "dsn",
    "jwt",
    "key",
    "passphrase",
    "password",
    "private",
    "secret",
    "session",
    "token",
    "wallet",
)
LIVE_REFERENCE_TOKENS = (
    "broker",
    "cancel",
    "order",
    "replace",
    "sign",
    "trade",
)
REDACTED_REFERENCE_TOKENS = SENSITIVE_REFERENCE_TOKENS + LIVE_REFERENCE_TOKENS
UNSAFE_FIELD_FRAGMENTS = (
    "auth",
    "broker",
    "cancel",
    "exchange_mutation",
    "order",
    "private_key",
    "replace",
    "sign",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class StrategySizingRiskBudgetV4Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    nav: Decimal = Decimal("100000.000000")
    max_nav_share: Decimal = Decimal("0.050000")
    full_size_expected_value: Decimal = Decimal("0.100000")
    min_expected_value: Decimal = Decimal("0.020000")
    watch_expected_value: Decimal = Decimal("0.050000")
    max_resolution_risk: Decimal = Decimal("0.600000")
    watch_resolution_risk: Decimal = Decimal("0.350000")
    watch_capacity_headroom_share: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "nav", _normalize_positive_decimal("nav", self.nav))
        object.__setattr__(
            self,
            "max_nav_share",
            _normalize_positive_probability_decimal("max_nav_share", self.max_nav_share),
        )
        object.__setattr__(
            self,
            "full_size_expected_value",
            _normalize_positive_decimal(
                "full_size_expected_value",
                self.full_size_expected_value,
            ),
        )
        for field_name in (
            "min_expected_value",
            "watch_expected_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolution_risk",
            "watch_resolution_risk",
            "watch_capacity_headroom_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_expected_value < self.min_expected_value:
            raise ValueError("watch_expected_value must not be below min_expected_value")
        if self.full_size_expected_value < self.watch_expected_value:
            raise ValueError(
                "full_size_expected_value must not be below watch_expected_value",
            )
        if self.max_resolution_risk < self.watch_resolution_risk:
            raise ValueError("max_resolution_risk must not be below watch_resolution_risk")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategySizingRiskBudgetV4Candidate:
    market_id: str
    market_reference: str
    correlation_cluster_id: str
    expected_value: Decimal
    liquidity_capacity: Decimal
    team_allocated_notional: Decimal
    team_allocation_cap: Decimal
    cluster_allocated_notional: Decimal
    cluster_allocation_cap: Decimal
    resolution_risk: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("market_reference", self.market_reference)
        _require_canonical_string("correlation_cluster_id", self.correlation_cluster_id)
        object.__setattr__(
            self,
            "market_reference",
            _redacted_reference(self.market_reference),
        )
        for field_name in (
            "expected_value",
            "liquidity_capacity",
            "team_allocated_notional",
            "team_allocation_cap",
            "cluster_allocated_notional",
            "cluster_allocation_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_risk",
            _normalize_probability_decimal("resolution_risk", self.resolution_risk),
        )
        if self.team_allocated_notional > self.team_allocation_cap:
            raise ValueError("team_allocated_notional cannot exceed team_allocation_cap")
        if self.cluster_allocated_notional > self.cluster_allocation_cap:
            raise ValueError(
                "cluster_allocated_notional cannot exceed cluster_allocation_cap",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class StrategySizingRiskBudgetV4Decision:
    config_version: str
    market_id: str
    redacted_market_reference: str
    correlation_cluster_id: str
    expected_value: Decimal
    nav_limit: Decimal
    expected_value_multiplier: Decimal
    liquidity_capacity: Decimal
    team_allocated_notional: Decimal
    team_allocation_cap: Decimal
    team_capacity_headroom: Decimal
    cluster_allocated_notional: Decimal
    cluster_allocation_cap: Decimal
    cluster_capacity_headroom: Decimal
    binding_capacity: Decimal
    resolution_risk: Decimal
    resolution_risk_multiplier: Decimal
    paper_notional: Decimal
    sizing_status: str
    risk_budget_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string(
            "redacted_market_reference",
            self.redacted_market_reference,
        )
        _require_redacted_reference(self.redacted_market_reference)
        _require_canonical_string("correlation_cluster_id", self.correlation_cluster_id)
        for field_name in (
            "expected_value",
            "nav_limit",
            "expected_value_multiplier",
            "liquidity_capacity",
            "team_allocated_notional",
            "team_allocation_cap",
            "team_capacity_headroom",
            "cluster_allocated_notional",
            "cluster_allocation_cap",
            "cluster_capacity_headroom",
            "binding_capacity",
            "resolution_risk_multiplier",
            "paper_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_risk",
            _normalize_probability_decimal("resolution_risk", self.resolution_risk),
        )
        _require_member("sizing_status", self.sizing_status, SIZING_STATUSES)
        object.__setattr__(
            self,
            "risk_budget_reason_codes",
            _normalize_reason_codes(
                self.risk_budget_reason_codes,
                require_nonempty=True,
            ),
        )
        _validate_decision(self)
        _require_safety_flags("decision", self)


def build_strategy_sizing_risk_budget_v4(
    row: object,
    *,
    config: StrategySizingRiskBudgetV4Config,
) -> StrategySizingRiskBudgetV4Decision:
    if type(config) is not StrategySizingRiskBudgetV4Config:
        raise ValueError("config must be a StrategySizingRiskBudgetV4Config")
    if type(row) is not StrategySizingRiskBudgetV4Candidate:
        raise ValueError("row must be a StrategySizingRiskBudgetV4Candidate")
    _require_safety_flags("config", config)
    _require_safety_flags("row", row)

    nav_limit = _multiply_decimal(config.nav, config.max_nav_share)
    expected_value_multiplier = _bounded_probability_decimal(
        _ratio_decimal(row.expected_value, config.full_size_expected_value),
    )
    resolution_risk_multiplier = _max_decimal(
        _subtract_decimal(ONE, row.resolution_risk),
        _zero(),
    )
    team_capacity_headroom = _max_decimal(
        _subtract_decimal(row.team_allocation_cap, row.team_allocated_notional),
        _zero(),
    )
    cluster_capacity_headroom = _max_decimal(
        _subtract_decimal(row.cluster_allocation_cap, row.cluster_allocated_notional),
        _zero(),
    )
    binding_capacity = min(
        nav_limit,
        row.liquidity_capacity,
        team_capacity_headroom,
        cluster_capacity_headroom,
    )
    sizing_status = _sizing_status(
        row,
        config=config,
        binding_capacity=binding_capacity,
        nav_limit=nav_limit,
    )
    paper_notional = _paper_notional(
        sizing_status,
        binding_capacity=binding_capacity,
        expected_value_multiplier=expected_value_multiplier,
        resolution_risk_multiplier=resolution_risk_multiplier,
    )

    return StrategySizingRiskBudgetV4Decision(
        config_version=config.config_version,
        market_id=row.market_id,
        redacted_market_reference=row.market_reference,
        correlation_cluster_id=row.correlation_cluster_id,
        expected_value=row.expected_value,
        nav_limit=nav_limit,
        expected_value_multiplier=expected_value_multiplier,
        liquidity_capacity=row.liquidity_capacity,
        team_allocated_notional=row.team_allocated_notional,
        team_allocation_cap=row.team_allocation_cap,
        team_capacity_headroom=team_capacity_headroom,
        cluster_allocated_notional=row.cluster_allocated_notional,
        cluster_allocation_cap=row.cluster_allocation_cap,
        cluster_capacity_headroom=cluster_capacity_headroom,
        binding_capacity=binding_capacity,
        resolution_risk=row.resolution_risk,
        resolution_risk_multiplier=resolution_risk_multiplier,
        paper_notional=paper_notional,
        sizing_status=sizing_status,
        risk_budget_reason_codes=_risk_budget_reason_codes(
            row,
            config=config,
            sizing_status=sizing_status,
            nav_limit=nav_limit,
            binding_capacity=binding_capacity,
            team_capacity_headroom=team_capacity_headroom,
            cluster_capacity_headroom=cluster_capacity_headroom,
        ),
    )


def strategy_sizing_risk_budget_v4_payload(
    decision: StrategySizingRiskBudgetV4Decision,
) -> dict[str, object]:
    if type(decision) is not StrategySizingRiskBudgetV4Decision:
        raise ValueError("decision must be a StrategySizingRiskBudgetV4Decision")
    _require_safety_flags("decision", decision)
    return {
        "config_version": decision.config_version,
        "market_id": decision.market_id,
        "redacted_market_reference": decision.redacted_market_reference,
        "correlation_cluster_id": decision.correlation_cluster_id,
        "expected_value": _decimal_payload(decision.expected_value),
        "nav_limit": _decimal_payload(decision.nav_limit),
        "expected_value_multiplier": _decimal_payload(
            decision.expected_value_multiplier,
        ),
        "liquidity_capacity": _decimal_payload(decision.liquidity_capacity),
        "team_allocated_notional": _decimal_payload(decision.team_allocated_notional),
        "team_allocation_cap": _decimal_payload(decision.team_allocation_cap),
        "team_capacity_headroom": _decimal_payload(decision.team_capacity_headroom),
        "cluster_allocated_notional": _decimal_payload(
            decision.cluster_allocated_notional,
        ),
        "cluster_allocation_cap": _decimal_payload(decision.cluster_allocation_cap),
        "cluster_capacity_headroom": _decimal_payload(
            decision.cluster_capacity_headroom,
        ),
        "binding_capacity": _decimal_payload(decision.binding_capacity),
        "resolution_risk": _decimal_payload(decision.resolution_risk),
        "resolution_risk_multiplier": _decimal_payload(
            decision.resolution_risk_multiplier,
        ),
        "paper_notional": _decimal_payload(decision.paper_notional),
        "sizing_status": decision.sizing_status,
        "risk_budget_reason_codes": list(decision.risk_budget_reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _sizing_status(
    row: StrategySizingRiskBudgetV4Candidate,
    *,
    config: StrategySizingRiskBudgetV4Config,
    binding_capacity: Decimal,
    nav_limit: Decimal,
) -> str:
    if (
        row.expected_value < config.min_expected_value
        or row.resolution_risk > config.max_resolution_risk
        or binding_capacity <= ZERO
    ):
        return "blocked"
    if (
        row.expected_value < config.watch_expected_value
        or row.resolution_risk >= config.watch_resolution_risk
        or binding_capacity
        <= _multiply_decimal(nav_limit, config.watch_capacity_headroom_share)
    ):
        return "watch"
    return "pass"


def _paper_notional(
    sizing_status: str,
    *,
    binding_capacity: Decimal,
    expected_value_multiplier: Decimal,
    resolution_risk_multiplier: Decimal,
) -> Decimal:
    if sizing_status == "blocked":
        return _zero()
    return _multiply_decimal(
        _multiply_decimal(binding_capacity, expected_value_multiplier),
        resolution_risk_multiplier,
    )


def _risk_budget_reason_codes(
    row: StrategySizingRiskBudgetV4Candidate,
    *,
    config: StrategySizingRiskBudgetV4Config,
    sizing_status: str,
    nav_limit: Decimal,
    binding_capacity: Decimal,
    team_capacity_headroom: Decimal,
    cluster_capacity_headroom: Decimal,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            *row.reason_codes,
            TERMINAL_REASON_BY_STATUS[sizing_status],
            _expected_value_reason(row.expected_value, config=config),
            _liquidity_capacity_reason(
                row.liquidity_capacity,
                nav_limit=nav_limit,
                binding_capacity=binding_capacity,
            ),
            _team_capacity_reason(
                team_capacity_headroom,
                nav_limit=nav_limit,
                binding_capacity=binding_capacity,
            ),
            _cluster_capacity_reason(
                cluster_capacity_headroom,
                nav_limit=nav_limit,
                binding_capacity=binding_capacity,
            ),
            _resolution_risk_reason(row.resolution_risk, config=config),
        ),
        require_nonempty=True,
    )


def _expected_value_reason(
    expected_value: Decimal,
    *,
    config: StrategySizingRiskBudgetV4Config,
) -> str:
    if expected_value < config.min_expected_value:
        return "expected_value_below_minimum"
    if expected_value < config.watch_expected_value:
        return "expected_value_watch"
    return "expected_value_pass"


def _liquidity_capacity_reason(
    liquidity_capacity: Decimal,
    *,
    nav_limit: Decimal,
    binding_capacity: Decimal,
) -> str:
    if liquidity_capacity <= ZERO:
        return "liquidity_capacity_exhausted"
    if liquidity_capacity == binding_capacity and binding_capacity < nav_limit:
        return "liquidity_capacity_limited"
    return "liquidity_capacity_available"


def _team_capacity_reason(
    team_capacity_headroom: Decimal,
    *,
    nav_limit: Decimal,
    binding_capacity: Decimal,
) -> str:
    if team_capacity_headroom <= ZERO:
        return "team_allocation_cap_exhausted"
    if team_capacity_headroom == binding_capacity and binding_capacity < nav_limit:
        return "team_allocation_cap_limited"
    return "team_allocation_capacity_available"


def _cluster_capacity_reason(
    cluster_capacity_headroom: Decimal,
    *,
    nav_limit: Decimal,
    binding_capacity: Decimal,
) -> str:
    if cluster_capacity_headroom <= ZERO:
        return "market_correlation_cluster_cap_exhausted"
    if cluster_capacity_headroom == binding_capacity and binding_capacity < nav_limit:
        return "market_correlation_cluster_cap_limited"
    return "market_correlation_cluster_capacity_available"


def _resolution_risk_reason(
    resolution_risk: Decimal,
    *,
    config: StrategySizingRiskBudgetV4Config,
) -> str:
    if resolution_risk > config.max_resolution_risk:
        return "resolution_risk_high"
    if resolution_risk >= config.watch_resolution_risk:
        return "resolution_risk_watch"
    return "resolution_risk_contained"


def _validate_decision(decision: StrategySizingRiskBudgetV4Decision) -> None:
    expected_terminal_reason = TERMINAL_REASON_BY_STATUS[decision.sizing_status]
    if expected_terminal_reason not in decision.risk_budget_reason_codes:
        raise ValueError("risk_budget_reason_codes must include status terminal reason")
    conflicting_terminal_reasons = (
        TERMINAL_REASON_CODES
        - frozenset((expected_terminal_reason,))
    ).intersection(decision.risk_budget_reason_codes)
    if conflicting_terminal_reasons:
        raise ValueError(
            "risk_budget_reason_codes must not contain conflicting status reasons",
        )
    if decision.team_allocated_notional > decision.team_allocation_cap:
        raise ValueError("team_allocated_notional cannot exceed team_allocation_cap")
    if decision.cluster_allocated_notional > decision.cluster_allocation_cap:
        raise ValueError(
            "cluster_allocated_notional cannot exceed cluster_allocation_cap",
        )
    if decision.binding_capacity > decision.nav_limit:
        raise ValueError("binding_capacity cannot exceed nav_limit")
    if decision.paper_notional > decision.binding_capacity:
        raise ValueError("paper_notional cannot exceed binding_capacity")


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_fields(label, value)


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _normalize_positive_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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


def _subtract_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first - second).quantize(QUANTUM)


def _multiply_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first * second).quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _bounded_probability_decimal(value: Decimal) -> Decimal:
    return _min_decimal(_max_decimal(value, _zero()), ONE)


def _min_decimal(first: Decimal, second: Decimal) -> Decimal:
    return first if first <= second else second


def _max_decimal(first: Decimal, second: Decimal) -> Decimal:
    return first if first >= second else second


def _zero() -> Decimal:
    return ZERO.quantize(QUANTUM)


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


def _normalize_input_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values, require_nonempty=True)
    for reason_code in reason_codes:
        if reason_code in REDUCER_OWNED_REASON_CODES:
            raise ValueError("input reason_codes must not include reducer-owned reason codes")
    return reason_codes


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")
    if any(token in value for token in REDACTED_REFERENCE_TOKENS):
        raise ValueError(
            f"{field_name} must not expose sensitive or live-reference tokens",
        )


def _redacted_reference(market_reference: str) -> str:
    lowered = market_reference.lower()
    if any(token in lowered for token in REDACTED_REFERENCE_TOKENS):
        digest = sha256(market_reference.encode("utf-8")).hexdigest()[:16]
        return f"market_ref_{digest}"
    return market_reference


def _require_redacted_reference(value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in REDACTED_REFERENCE_TOKENS):
        raise ValueError("redacted_market_reference must not expose sensitive tokens")


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")
