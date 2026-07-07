from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
DAY_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DAYS_PER_YEAR = Decimal("365")
SCORE_STATUSES = ("candidate", "watch", "blocked")
SCORE_DECISIONS = ("paper_candidate", "manual_review", "reject")
_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("muta", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "candidate_id",
    "expected_probability",
    "market_probability",
    "gross_edge_probability_delta",
    "taker_fee_probability_delta",
    "spread_probability_delta",
    "slippage_probability_delta",
    "direct_cost_probability_delta",
    "settlement_lag_days",
    "annualized_capital_drag_rate",
    "settlement_lag_capital_drag_probability_delta",
    "liquidity_depth_usd",
    "minimum_liquidity_depth_usd",
    "liquidity_shortfall_ratio",
    "liquidity_haircut_probability_delta",
    "liquidity_haircut_applied_probability_delta",
    "total_drag_probability_delta",
    "break_even_probability",
    "net_break_even_edge_probability_delta",
    "minimum_actionable_edge_probability_delta",
    "score_status",
    "score_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_CODE_MARKER = "strategy_candidate_fee_drag_break_even_v2"


@dataclass(frozen=True)
class StrategyCandidateFeeDragBreakEvenV2Input:
    candidate_id: str
    expected_probability: Decimal
    market_probability: Decimal
    taker_fee_probability_delta: Decimal
    spread_probability_delta: Decimal
    slippage_probability_delta: Decimal
    settlement_lag_days: Decimal
    annualized_capital_drag_rate: Decimal
    liquidity_depth_usd: Decimal
    minimum_liquidity_depth_usd: Decimal
    liquidity_haircut_probability_delta: Decimal
    minimum_actionable_edge_probability_delta: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in ("expected_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_probability_delta",
            "spread_probability_delta",
            "slippage_probability_delta",
            "annualized_capital_drag_rate",
            "liquidity_depth_usd",
            "liquidity_haircut_probability_delta",
            "minimum_actionable_edge_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_lag_days",
            _normalize_nonnegative_days("settlement_lag_days", self.settlement_lag_days),
        )
        object.__setattr__(
            self,
            "minimum_liquidity_depth_usd",
            _normalize_positive_decimal(
                "minimum_liquidity_depth_usd",
                self.minimum_liquidity_depth_usd,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload(
            "candidate fee drag score input",
            self,
        )
        _require_paper_flags("candidate fee drag score input", self)


@dataclass(frozen=True)
class StrategyCandidateFeeDragBreakEvenV2Result:
    candidate_id: str
    expected_probability: Decimal
    market_probability: Decimal
    gross_edge_probability_delta: Decimal
    taker_fee_probability_delta: Decimal
    spread_probability_delta: Decimal
    slippage_probability_delta: Decimal
    direct_cost_probability_delta: Decimal
    settlement_lag_days: Decimal
    annualized_capital_drag_rate: Decimal
    settlement_lag_capital_drag_probability_delta: Decimal
    liquidity_depth_usd: Decimal
    minimum_liquidity_depth_usd: Decimal
    liquidity_shortfall_ratio: Decimal
    liquidity_haircut_probability_delta: Decimal
    liquidity_haircut_applied_probability_delta: Decimal
    total_drag_probability_delta: Decimal
    break_even_probability: Decimal
    net_break_even_edge_probability_delta: Decimal
    minimum_actionable_edge_probability_delta: Decimal
    score_status: str
    score_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in ("expected_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_edge_probability_delta",
            "break_even_probability",
            "net_break_even_edge_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_probability_delta",
            "spread_probability_delta",
            "slippage_probability_delta",
            "direct_cost_probability_delta",
            "annualized_capital_drag_rate",
            "settlement_lag_capital_drag_probability_delta",
            "liquidity_depth_usd",
            "liquidity_shortfall_ratio",
            "liquidity_haircut_probability_delta",
            "liquidity_haircut_applied_probability_delta",
            "total_drag_probability_delta",
            "minimum_actionable_edge_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_lag_days",
            _normalize_nonnegative_days("settlement_lag_days", self.settlement_lag_days),
        )
        object.__setattr__(
            self,
            "minimum_liquidity_depth_usd",
            _normalize_positive_decimal(
                "minimum_liquidity_depth_usd",
                self.minimum_liquidity_depth_usd,
            ),
        )
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        _require_choice("score_decision", self.score_decision, SCORE_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload(
            "candidate fee drag score result",
            self,
        )
        _require_paper_flags("candidate fee drag score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_fee_drag_break_even_v2_payload(self)


def estimate_strategy_candidate_fee_drag_break_even_v2(
    score_input: StrategyCandidateFeeDragBreakEvenV2Input,
) -> StrategyCandidateFeeDragBreakEvenV2Result:
    if type(score_input) is not StrategyCandidateFeeDragBreakEvenV2Input:
        raise ValueError(
            "score_input must be a StrategyCandidateFeeDragBreakEvenV2Input",
        )
    reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload(
        "candidate fee drag score input",
        score_input,
    )
    _require_paper_flags("candidate fee drag score input", score_input)

    gross_edge_probability_delta = _normalize_decimal(
        "gross_edge_probability_delta",
        score_input.expected_probability - score_input.market_probability,
    )
    direct_cost_probability_delta = _direct_cost_probability_delta(
        score_input.taker_fee_probability_delta,
        score_input.spread_probability_delta,
        score_input.slippage_probability_delta,
    )
    settlement_lag_capital_drag_probability_delta = (
        _settlement_lag_capital_drag_probability_delta(
            score_input.market_probability,
            score_input.settlement_lag_days,
            score_input.annualized_capital_drag_rate,
        )
    )
    liquidity_shortfall_ratio = _liquidity_shortfall_ratio(
        score_input.liquidity_depth_usd,
        score_input.minimum_liquidity_depth_usd,
    )
    liquidity_haircut_applied_probability_delta = (
        _liquidity_haircut_applied_probability_delta(
            score_input.liquidity_haircut_probability_delta,
            liquidity_shortfall_ratio,
        )
    )
    total_drag_probability_delta = _total_drag_probability_delta(
        direct_cost_probability_delta,
        settlement_lag_capital_drag_probability_delta,
        liquidity_haircut_applied_probability_delta,
    )
    break_even_probability = _normalize_decimal(
        "break_even_probability",
        score_input.market_probability + total_drag_probability_delta,
    )
    net_break_even_edge_probability_delta = _normalize_decimal(
        "net_break_even_edge_probability_delta",
        gross_edge_probability_delta - total_drag_probability_delta,
    )
    score_status = _score_status(
        net_break_even_edge_probability_delta,
        score_input.minimum_actionable_edge_probability_delta,
    )

    return StrategyCandidateFeeDragBreakEvenV2Result(
        candidate_id=score_input.candidate_id,
        expected_probability=score_input.expected_probability,
        market_probability=score_input.market_probability,
        gross_edge_probability_delta=gross_edge_probability_delta,
        taker_fee_probability_delta=score_input.taker_fee_probability_delta,
        spread_probability_delta=score_input.spread_probability_delta,
        slippage_probability_delta=score_input.slippage_probability_delta,
        direct_cost_probability_delta=direct_cost_probability_delta,
        settlement_lag_days=score_input.settlement_lag_days,
        annualized_capital_drag_rate=score_input.annualized_capital_drag_rate,
        settlement_lag_capital_drag_probability_delta=(
            settlement_lag_capital_drag_probability_delta
        ),
        liquidity_depth_usd=score_input.liquidity_depth_usd,
        minimum_liquidity_depth_usd=score_input.minimum_liquidity_depth_usd,
        liquidity_shortfall_ratio=liquidity_shortfall_ratio,
        liquidity_haircut_probability_delta=(
            score_input.liquidity_haircut_probability_delta
        ),
        liquidity_haircut_applied_probability_delta=(
            liquidity_haircut_applied_probability_delta
        ),
        total_drag_probability_delta=total_drag_probability_delta,
        break_even_probability=break_even_probability,
        net_break_even_edge_probability_delta=net_break_even_edge_probability_delta,
        minimum_actionable_edge_probability_delta=(
            score_input.minimum_actionable_edge_probability_delta
        ),
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            gross_edge_probability_delta=gross_edge_probability_delta,
            taker_fee_probability_delta=score_input.taker_fee_probability_delta,
            spread_probability_delta=score_input.spread_probability_delta,
            slippage_probability_delta=score_input.slippage_probability_delta,
            settlement_lag_capital_drag_probability_delta=(
                settlement_lag_capital_drag_probability_delta
            ),
            liquidity_haircut_applied_probability_delta=(
                liquidity_haircut_applied_probability_delta
            ),
            net_break_even_edge_probability_delta=(
                net_break_even_edge_probability_delta
            ),
            minimum_actionable_edge_probability_delta=(
                score_input.minimum_actionable_edge_probability_delta
            ),
            score_status=score_status,
        ),
    )


def strategy_candidate_fee_drag_break_even_v2_payload(
    result: StrategyCandidateFeeDragBreakEvenV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateFeeDragBreakEvenV2Result:
        raise ValueError("result must be a StrategyCandidateFeeDragBreakEvenV2Result")
    _require_paper_flags("candidate fee drag score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload(
        "candidate fee drag score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _direct_cost_probability_delta(
    taker_fee_probability_delta: Decimal,
    spread_probability_delta: Decimal,
    slippage_probability_delta: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "direct_cost_probability_delta",
        taker_fee_probability_delta
        + spread_probability_delta
        + slippage_probability_delta,
    )


def _settlement_lag_capital_drag_probability_delta(
    market_probability: Decimal,
    settlement_lag_days: Decimal,
    annualized_capital_drag_rate: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "settlement_lag_capital_drag_probability_delta",
        market_probability
        * annualized_capital_drag_rate
        * settlement_lag_days
        / DAYS_PER_YEAR,
    )


def _liquidity_shortfall_ratio(
    liquidity_depth_usd: Decimal,
    minimum_liquidity_depth_usd: Decimal,
) -> Decimal:
    if liquidity_depth_usd >= minimum_liquidity_depth_usd:
        return ZERO
    return _normalize_nonnegative_decimal(
        "liquidity_shortfall_ratio",
        (minimum_liquidity_depth_usd - liquidity_depth_usd)
        / minimum_liquidity_depth_usd,
    )


def _liquidity_haircut_applied_probability_delta(
    liquidity_haircut_probability_delta: Decimal,
    liquidity_shortfall_ratio: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "liquidity_haircut_applied_probability_delta",
        liquidity_haircut_probability_delta * liquidity_shortfall_ratio,
    )


def _total_drag_probability_delta(
    direct_cost_probability_delta: Decimal,
    settlement_lag_capital_drag_probability_delta: Decimal,
    liquidity_haircut_applied_probability_delta: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "total_drag_probability_delta",
        direct_cost_probability_delta
        + settlement_lag_capital_drag_probability_delta
        + liquidity_haircut_applied_probability_delta,
    )


def _score_status(
    net_break_even_edge_probability_delta: Decimal,
    minimum_actionable_edge_probability_delta: Decimal,
) -> str:
    if net_break_even_edge_probability_delta <= ZERO:
        return "blocked"
    if net_break_even_edge_probability_delta < minimum_actionable_edge_probability_delta:
        return "watch"
    return "candidate"


def _score_decision(score_status: str) -> str:
    if score_status == "candidate":
        return "paper_candidate"
    if score_status == "watch":
        return "manual_review"
    if score_status == "blocked":
        return "reject"
    raise ValueError("score_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    gross_edge_probability_delta: Decimal,
    taker_fee_probability_delta: Decimal,
    spread_probability_delta: Decimal,
    slippage_probability_delta: Decimal,
    settlement_lag_capital_drag_probability_delta: Decimal,
    liquidity_haircut_applied_probability_delta: Decimal,
    net_break_even_edge_probability_delta: Decimal,
    minimum_actionable_edge_probability_delta: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_fee_drag_break_even_v2",
        f"score_{score_status}",
        _edge_reason_code(gross_edge_probability_delta),
    ]
    if taker_fee_probability_delta > ZERO:
        additions.append("taker_fee_drag_applied")
    if spread_probability_delta > ZERO:
        additions.append("spread_drag_applied")
    if slippage_probability_delta > ZERO:
        additions.append("slippage_drag_applied")
    if settlement_lag_capital_drag_probability_delta > ZERO:
        additions.append("settlement_lag_capital_drag_applied")
    if liquidity_haircut_applied_probability_delta > ZERO:
        additions.append("liquidity_haircut_applied")
    if net_break_even_edge_probability_delta <= ZERO:
        additions.append("net_edge_below_zero")
    elif net_break_even_edge_probability_delta < minimum_actionable_edge_probability_delta:
        additions.append("net_edge_positive_below_minimum")
    else:
        additions.append("minimum_actionable_edge_met")
    return _append_reason_codes(existing, tuple(additions))


def _edge_reason_code(gross_edge_probability_delta: Decimal) -> str:
    if gross_edge_probability_delta > ZERO:
        return "edge_positive"
    if gross_edge_probability_delta == ZERO:
        return "edge_flat"
    return "edge_negative"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_result_consistency(
    result: StrategyCandidateFeeDragBreakEvenV2Result,
) -> None:
    if result.gross_edge_probability_delta != _normalize_decimal(
        "gross_edge_probability_delta",
        result.expected_probability - result.market_probability,
    ):
        raise ValueError("gross_edge_probability_delta must match probability inputs")
    if result.direct_cost_probability_delta != _direct_cost_probability_delta(
        result.taker_fee_probability_delta,
        result.spread_probability_delta,
        result.slippage_probability_delta,
    ):
        raise ValueError("direct_cost_probability_delta must match cost inputs")
    if (
        result.settlement_lag_capital_drag_probability_delta
        != _settlement_lag_capital_drag_probability_delta(
            result.market_probability,
            result.settlement_lag_days,
            result.annualized_capital_drag_rate,
        )
    ):
        raise ValueError(
            "settlement_lag_capital_drag_probability_delta must match lag inputs",
        )
    if result.liquidity_shortfall_ratio != _liquidity_shortfall_ratio(
        result.liquidity_depth_usd,
        result.minimum_liquidity_depth_usd,
    ):
        raise ValueError("liquidity_shortfall_ratio must match depth inputs")
    if (
        result.liquidity_haircut_applied_probability_delta
        != _liquidity_haircut_applied_probability_delta(
            result.liquidity_haircut_probability_delta,
            result.liquidity_shortfall_ratio,
        )
    ):
        raise ValueError(
            "liquidity_haircut_applied_probability_delta must match depth inputs",
        )
    if result.total_drag_probability_delta != _total_drag_probability_delta(
        result.direct_cost_probability_delta,
        result.settlement_lag_capital_drag_probability_delta,
        result.liquidity_haircut_applied_probability_delta,
    ):
        raise ValueError("total_drag_probability_delta must match drag inputs")
    if result.break_even_probability != _normalize_decimal(
        "break_even_probability",
        result.market_probability + result.total_drag_probability_delta,
    ):
        raise ValueError("break_even_probability must match drag inputs")
    if result.net_break_even_edge_probability_delta != _normalize_decimal(
        "net_break_even_edge_probability_delta",
        result.gross_edge_probability_delta - result.total_drag_probability_delta,
    ):
        raise ValueError("net_break_even_edge_probability_delta must match drag inputs")
    if result.score_status != _score_status(
        result.net_break_even_edge_probability_delta,
        result.minimum_actionable_edge_probability_delta,
    ):
        raise ValueError("score_status must match net break-even edge")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")
    expected_reason_codes = _reason_codes(
        _source_reason_codes(result.reason_codes),
        gross_edge_probability_delta=result.gross_edge_probability_delta,
        taker_fee_probability_delta=result.taker_fee_probability_delta,
        spread_probability_delta=result.spread_probability_delta,
        slippage_probability_delta=result.slippage_probability_delta,
        settlement_lag_capital_drag_probability_delta=(
            result.settlement_lag_capital_drag_probability_delta
        ),
        liquidity_haircut_applied_probability_delta=(
            result.liquidity_haircut_applied_probability_delta
        ),
        net_break_even_edge_probability_delta=(
            result.net_break_even_edge_probability_delta
        ),
        minimum_actionable_edge_probability_delta=(
            result.minimum_actionable_edge_probability_delta
        ),
        score_status=result.score_status,
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match input fields")


def _source_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if _REASON_CODE_MARKER not in reason_codes:
        return reason_codes
    return reason_codes[: reason_codes.index(_REASON_CODE_MARKER)]


def _derived_validation_digest(
    result: StrategyCandidateFeeDragBreakEvenV2Result,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_days(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(DAY_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
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
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != len(sha256(b"").hexdigest()) or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "SCORE_STATUSES",
    "SCORE_DECISIONS",
    "StrategyCandidateFeeDragBreakEvenV2Input",
    "StrategyCandidateFeeDragBreakEvenV2Result",
    "estimate_strategy_candidate_fee_drag_break_even_v2",
    "strategy_candidate_fee_drag_break_even_v2_payload",
    "reject_strategy_candidate_fee_drag_break_even_v2_unsafe_payload",
)
