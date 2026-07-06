"""Pure typed paper-only watchlist policy v2 for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


__all__ = (
    "StrategyCandidateWatchlistPolicyV2Candidate",
    "StrategyCandidateWatchlistPolicyV2Config",
    "StrategyCandidateWatchlistPolicyV2Decision",
    "classify_strategy_candidate_watchlist_policy_v2",
    "strategy_candidate_watchlist_policy_v2_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-candidate-watchlist-policy-v2"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
WATCHLIST_STATUSES = (
    "wait_for_price",
    "wait_for_source",
    "wait_for_liquidity",
    "wait_for_resolution_clarity",
    "drop",
)
STATUS_REASON_PREFIX = "strategy_candidate_watchlist_v2_"


@dataclass(frozen=True)
class StrategyCandidateWatchlistPolicyV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_edge: Decimal = Decimal("0.030000")
    minimum_source_count: int = 2
    minimum_liquidity_notional: Decimal = Decimal("1000.000000")
    price_review_minutes: int = 30
    source_review_minutes: int = 360
    liquidity_review_minutes: int = 60
    resolution_review_minutes: int = 720
    drop_review_minutes: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateWatchlistPolicyV2Config:
            raise TypeError("StrategyCandidateWatchlistPolicyV2Config is final")

    def __post_init__(self) -> None:
        _require_exact_self_type(
            "config",
            self,
            StrategyCandidateWatchlistPolicyV2Config,
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_edge",
            _normalize_probability_decimal("minimum_edge", self.minimum_edge),
        )
        object.__setattr__(
            self,
            "minimum_source_count",
            _normalize_positive_int("minimum_source_count", self.minimum_source_count),
        )
        object.__setattr__(
            self,
            "minimum_liquidity_notional",
            _normalize_nonnegative_decimal(
                "minimum_liquidity_notional",
                self.minimum_liquidity_notional,
            ),
        )
        for field_name in (
            "price_review_minutes",
            "source_review_minutes",
            "liquidity_review_minutes",
            "resolution_review_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_int(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "drop_review_minutes",
            _normalize_nonnegative_int("drop_review_minutes", self.drop_review_minutes),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateWatchlistPolicyV2Candidate:
    candidate_id: str
    market_slug: str
    outcome_name: str
    best_ask_price: Decimal
    target_entry_price: Decimal
    estimated_edge: Decimal
    source_count: int
    available_liquidity_notional: Decimal
    resolution_is_clear: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateWatchlistPolicyV2Candidate:
            raise TypeError("StrategyCandidateWatchlistPolicyV2Candidate is final")

    def __post_init__(self) -> None:
        _require_exact_self_type(
            "candidate_state",
            self,
            StrategyCandidateWatchlistPolicyV2Candidate,
        )
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("best_ask_price", "target_entry_price", "estimated_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_int("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "available_liquidity_notional",
            _normalize_nonnegative_decimal(
                "available_liquidity_notional",
                self.available_liquidity_notional,
            ),
        )
        if type(self.resolution_is_clear) is not bool:
            raise ValueError("resolution_is_clear must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate_state", self)


@dataclass(frozen=True)
class StrategyCandidateWatchlistPolicyV2Decision:
    config_version: str
    candidate_id: str
    market_slug: str
    outcome_name: str
    watchlist_status: str
    next_review_minutes: int
    best_ask_price: Decimal
    target_entry_price: Decimal
    estimated_edge: Decimal
    source_count: int
    available_liquidity_notional: Decimal
    resolution_is_clear: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateWatchlistPolicyV2Decision:
            raise TypeError("StrategyCandidateWatchlistPolicyV2Decision is final")

    def __post_init__(self) -> None:
        _require_exact_self_type(
            "decision",
            self,
            StrategyCandidateWatchlistPolicyV2Decision,
        )
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "outcome_name",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("watchlist_status", self.watchlist_status, WATCHLIST_STATUSES)
        object.__setattr__(
            self,
            "next_review_minutes",
            _normalize_nonnegative_int("next_review_minutes", self.next_review_minutes),
        )
        for field_name in ("best_ask_price", "target_entry_price", "estimated_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_int("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "available_liquidity_notional",
            _normalize_nonnegative_decimal(
                "available_liquidity_notional",
                self.available_liquidity_notional,
            ),
        )
        if type(self.resolution_is_clear) is not bool:
            raise ValueError("resolution_is_clear must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_decision_consistency(self)
        _require_hard_flags("decision", self)


def classify_strategy_candidate_watchlist_policy_v2(
    candidate_state: StrategyCandidateWatchlistPolicyV2Candidate,
    config: StrategyCandidateWatchlistPolicyV2Config,
) -> StrategyCandidateWatchlistPolicyV2Decision:
    """Classify one candidate into a pure typed paper-only v2 watchlist bucket."""

    _require_exact_type(
        "candidate_state",
        candidate_state,
        StrategyCandidateWatchlistPolicyV2Candidate,
    )
    _require_exact_type("config", config, StrategyCandidateWatchlistPolicyV2Config)

    watchlist_status, next_review_minutes, generated_reason_codes = (
        _watchlist_status_review_and_reasons(candidate_state, config)
    )
    return StrategyCandidateWatchlistPolicyV2Decision(
        config_version=config.config_version,
        candidate_id=candidate_state.candidate_id,
        market_slug=candidate_state.market_slug,
        outcome_name=candidate_state.outcome_name,
        watchlist_status=watchlist_status,
        next_review_minutes=next_review_minutes,
        best_ask_price=candidate_state.best_ask_price,
        target_entry_price=candidate_state.target_entry_price,
        estimated_edge=candidate_state.estimated_edge,
        source_count=candidate_state.source_count,
        available_liquidity_notional=candidate_state.available_liquidity_notional,
        resolution_is_clear=candidate_state.resolution_is_clear,
        reason_codes=_decision_reason_codes(
            watchlist_status,
            candidate_state.reason_codes,
            generated_reason_codes,
        ),
    )


def strategy_candidate_watchlist_policy_v2_payload(
    decision: StrategyCandidateWatchlistPolicyV2Decision,
) -> dict[str, object]:
    if type(decision) is not StrategyCandidateWatchlistPolicyV2Decision:
        raise ValueError("decision must be a StrategyCandidateWatchlistPolicyV2Decision")
    _require_hard_flags("decision", decision)
    return {
        "config_version": decision.config_version,
        "candidate_id": decision.candidate_id,
        "market_slug": decision.market_slug,
        "outcome_name": decision.outcome_name,
        "watchlist_status": decision.watchlist_status,
        "next_review_minutes": decision.next_review_minutes,
        "best_ask_price": _decimal_payload(decision.best_ask_price),
        "target_entry_price": _decimal_payload(decision.target_entry_price),
        "estimated_edge": _decimal_payload(decision.estimated_edge),
        "source_count": decision.source_count,
        "available_liquidity_notional": _decimal_payload(
            decision.available_liquidity_notional,
        ),
        "resolution_is_clear": decision.resolution_is_clear,
        "reason_codes": list(decision.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _watchlist_status_review_and_reasons(
    candidate_state: StrategyCandidateWatchlistPolicyV2Candidate,
    config: StrategyCandidateWatchlistPolicyV2Config,
) -> tuple[str, int, tuple[str, ...]]:
    if candidate_state.estimated_edge < config.minimum_edge:
        return "drop", config.drop_review_minutes, ("estimated_edge_below_minimum",)

    gap_reason_codes = _current_gap_reason_codes(candidate_state, config)
    if not gap_reason_codes:
        return "drop", config.drop_review_minutes, ("candidate_already_trade_ready",)
    if "source_count_below_minimum" in gap_reason_codes:
        return "wait_for_source", config.source_review_minutes, gap_reason_codes
    if "liquidity_below_minimum" in gap_reason_codes:
        return "wait_for_liquidity", config.liquidity_review_minutes, gap_reason_codes
    if "resolution_clarity_missing" in gap_reason_codes:
        return (
            "wait_for_resolution_clarity",
            config.resolution_review_minutes,
            gap_reason_codes,
        )
    return "wait_for_price", config.price_review_minutes, gap_reason_codes


def _current_gap_reason_codes(
    candidate_state: StrategyCandidateWatchlistPolicyV2Candidate,
    config: StrategyCandidateWatchlistPolicyV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate_state.source_count < config.minimum_source_count:
        reason_codes.append("source_count_below_minimum")
    if candidate_state.available_liquidity_notional < config.minimum_liquidity_notional:
        reason_codes.append("liquidity_below_minimum")
    if not candidate_state.resolution_is_clear:
        reason_codes.append("resolution_clarity_missing")
    if candidate_state.best_ask_price > candidate_state.target_entry_price:
        reason_codes.append("entry_price_above_target")
    return tuple(reason_codes)


def _decision_reason_codes(
    watchlist_status: str,
    upstream_reason_codes: tuple[str, ...],
    generated_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = [
        f"{STATUS_REASON_PREFIX}{watchlist_status}",
        *upstream_reason_codes,
        *generated_reason_codes,
    ]
    return tuple(dict.fromkeys(reason_codes))


def _validate_decision_consistency(
    decision: StrategyCandidateWatchlistPolicyV2Decision,
) -> None:
    expected_reason_code = f"{STATUS_REASON_PREFIX}{decision.watchlist_status}"
    if not decision.reason_codes or decision.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with watchlist_status reason code")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_exact_self_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _normalize_positive_int(field_name: str, value: object) -> int:
    normalized = _normalize_int(field_name, value)
    if normalized <= 0:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_int(field_name: str, value: object) -> int:
    normalized = _normalize_int(field_name, value)
    if normalized < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_int(field_name: str, value: object) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")
