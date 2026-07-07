"""Pure paper/report candidate expected-value decay score v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
SECOND_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
HUNDRED = Decimal("100.000000")
SECONDS_PER_MINUTE = Decimal("60")
STALE_OVERAGE_BPS_PER_MINUTE = Decimal("7.000000")
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
    "current_expected_value_bps",
    "previous_expected_value_bps",
    "peak_expected_value_bps",
    "ev_delta_bps",
    "ev_decay_from_peak_bps",
    "ev_decay_ratio",
    "edge_half_life_seconds",
    "stale_quote_age_seconds",
    "stale_edge_penalty_bps",
    "liquidity_depth_usd",
    "minimum_liquidity_depth_usd",
    "liquidity_damping_bps",
    "fee_bps",
    "spread_bps",
    "slippage_bps",
    "total_cost_bps",
    "raw_decay_adjusted_edge_bps",
    "paper_score_bps",
    "minimum_actionable_score",
    "score_status",
    "score_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyCandidateExpectedValueDecayScoreV2Input:
    candidate_id: str
    current_expected_value_bps: Decimal
    previous_expected_value_bps: Decimal
    peak_expected_value_bps: Decimal
    edge_half_life_seconds: Decimal
    stale_quote_age_seconds: Decimal
    liquidity_depth_usd: Decimal
    minimum_liquidity_depth_usd: Decimal
    fee_bps: Decimal
    spread_bps: Decimal
    slippage_bps: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "current_expected_value_bps",
            "previous_expected_value_bps",
            "peak_expected_value_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_half_life_seconds",
            _normalize_positive_seconds(
                "edge_half_life_seconds",
                self.edge_half_life_seconds,
            ),
        )
        object.__setattr__(
            self,
            "stale_quote_age_seconds",
            _normalize_nonnegative_seconds(
                "stale_quote_age_seconds",
                self.stale_quote_age_seconds,
            ),
        )
        for field_name in (
            "liquidity_depth_usd",
            "fee_bps",
            "spread_bps",
            "slippage_bps",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload(
            "candidate decay score input",
            self,
        )
        _require_paper_flags("candidate decay score input", self)


@dataclass(frozen=True)
class StrategyCandidateExpectedValueDecayScoreV2Result:
    candidate_id: str
    current_expected_value_bps: Decimal
    previous_expected_value_bps: Decimal
    peak_expected_value_bps: Decimal
    ev_delta_bps: Decimal
    ev_decay_from_peak_bps: Decimal
    ev_decay_ratio: Decimal
    edge_half_life_seconds: Decimal
    stale_quote_age_seconds: Decimal
    stale_edge_penalty_bps: Decimal
    liquidity_depth_usd: Decimal
    minimum_liquidity_depth_usd: Decimal
    liquidity_damping_bps: Decimal
    fee_bps: Decimal
    spread_bps: Decimal
    slippage_bps: Decimal
    total_cost_bps: Decimal
    raw_decay_adjusted_edge_bps: Decimal
    paper_score_bps: Decimal
    minimum_actionable_score: Decimal
    score_status: str
    score_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "current_expected_value_bps",
            "previous_expected_value_bps",
            "peak_expected_value_bps",
            "ev_delta_bps",
            "raw_decay_adjusted_edge_bps",
            "paper_score_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ev_decay_from_peak_bps",
            "ev_decay_ratio",
            "stale_edge_penalty_bps",
            "liquidity_depth_usd",
            "liquidity_damping_bps",
            "fee_bps",
            "spread_bps",
            "slippage_bps",
            "total_cost_bps",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_half_life_seconds",
            _normalize_positive_seconds(
                "edge_half_life_seconds",
                self.edge_half_life_seconds,
            ),
        )
        object.__setattr__(
            self,
            "stale_quote_age_seconds",
            _normalize_nonnegative_seconds(
                "stale_quote_age_seconds",
                self.stale_quote_age_seconds,
            ),
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
        reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload(
            "candidate decay score result",
            self,
        )
        _require_paper_flags("candidate decay score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_expected_value_decay_score_v2_payload(self)


def estimate_strategy_candidate_expected_value_decay_score_v2(
    score_input: StrategyCandidateExpectedValueDecayScoreV2Input,
) -> StrategyCandidateExpectedValueDecayScoreV2Result:
    if type(score_input) is not StrategyCandidateExpectedValueDecayScoreV2Input:
        raise ValueError(
            "score_input must be a StrategyCandidateExpectedValueDecayScoreV2Input",
        )
    reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload(
        "candidate decay score input",
        score_input,
    )
    _require_paper_flags("candidate decay score input", score_input)

    ev_delta_bps = _normalize_decimal(
        "ev_delta_bps",
        score_input.current_expected_value_bps
        - score_input.previous_expected_value_bps,
    )
    ev_decay_from_peak_bps = _normalize_nonnegative_decimal(
        "ev_decay_from_peak_bps",
        max(
            score_input.peak_expected_value_bps
            - score_input.current_expected_value_bps,
            ZERO,
        ),
    )
    ev_decay_ratio = _decay_ratio(
        ev_decay_from_peak_bps,
        score_input.peak_expected_value_bps,
    )
    stale_edge_penalty_bps = _stale_edge_penalty_bps(
        score_input.current_expected_value_bps,
        score_input.edge_half_life_seconds,
        score_input.stale_quote_age_seconds,
    )
    liquidity_damping_bps = _liquidity_damping_bps(
        score_input.liquidity_depth_usd,
        score_input.minimum_liquidity_depth_usd,
    )
    total_cost_bps = _normalize_nonnegative_decimal(
        "total_cost_bps",
        score_input.fee_bps + score_input.spread_bps + score_input.slippage_bps,
    )
    raw_decay_adjusted_edge_bps = _normalize_decimal(
        "raw_decay_adjusted_edge_bps",
        score_input.current_expected_value_bps - ev_decay_from_peak_bps,
    )
    paper_score_bps = _normalize_decimal(
        "paper_score_bps",
        raw_decay_adjusted_edge_bps
        - stale_edge_penalty_bps
        - liquidity_damping_bps
        - total_cost_bps,
    )
    score_status = _score_status(
        paper_score_bps,
        score_input.minimum_actionable_score,
    )

    return StrategyCandidateExpectedValueDecayScoreV2Result(
        candidate_id=score_input.candidate_id,
        current_expected_value_bps=score_input.current_expected_value_bps,
        previous_expected_value_bps=score_input.previous_expected_value_bps,
        peak_expected_value_bps=score_input.peak_expected_value_bps,
        ev_delta_bps=ev_delta_bps,
        ev_decay_from_peak_bps=ev_decay_from_peak_bps,
        ev_decay_ratio=ev_decay_ratio,
        edge_half_life_seconds=score_input.edge_half_life_seconds,
        stale_quote_age_seconds=score_input.stale_quote_age_seconds,
        stale_edge_penalty_bps=stale_edge_penalty_bps,
        liquidity_depth_usd=score_input.liquidity_depth_usd,
        minimum_liquidity_depth_usd=score_input.minimum_liquidity_depth_usd,
        liquidity_damping_bps=liquidity_damping_bps,
        fee_bps=score_input.fee_bps,
        spread_bps=score_input.spread_bps,
        slippage_bps=score_input.slippage_bps,
        total_cost_bps=total_cost_bps,
        raw_decay_adjusted_edge_bps=raw_decay_adjusted_edge_bps,
        paper_score_bps=paper_score_bps,
        minimum_actionable_score=score_input.minimum_actionable_score,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            current_expected_value_bps=score_input.current_expected_value_bps,
            ev_decay_from_peak_bps=ev_decay_from_peak_bps,
            stale_edge_penalty_bps=stale_edge_penalty_bps,
            liquidity_damping_bps=liquidity_damping_bps,
            total_cost_bps=total_cost_bps,
            paper_score_bps=paper_score_bps,
            minimum_actionable_score=score_input.minimum_actionable_score,
            score_status=score_status,
        ),
    )


def strategy_candidate_expected_value_decay_score_v2_payload(
    result: StrategyCandidateExpectedValueDecayScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateExpectedValueDecayScoreV2Result:
        raise ValueError(
            "result must be a StrategyCandidateExpectedValueDecayScoreV2Result",
        )
    _require_paper_flags("candidate decay score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload(
        "candidate decay score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _decay_ratio(ev_decay_from_peak_bps: Decimal, peak_expected_value_bps: Decimal) -> Decimal:
    if peak_expected_value_bps <= ZERO:
        return ZERO
    return _normalize_nonnegative_decimal(
        "ev_decay_ratio",
        ev_decay_from_peak_bps / peak_expected_value_bps,
    )


def _stale_edge_penalty_bps(
    current_expected_value_bps: Decimal,
    edge_half_life_seconds: Decimal,
    stale_quote_age_seconds: Decimal,
) -> Decimal:
    if stale_quote_age_seconds <= edge_half_life_seconds:
        return ZERO
    return _normalize_nonnegative_decimal(
        "stale_edge_penalty_bps",
        (stale_quote_age_seconds - edge_half_life_seconds)
        / SECONDS_PER_MINUTE
        * STALE_OVERAGE_BPS_PER_MINUTE,
    )


def _liquidity_damping_bps(
    liquidity_depth_usd: Decimal,
    minimum_liquidity_depth_usd: Decimal,
) -> Decimal:
    if liquidity_depth_usd >= minimum_liquidity_depth_usd:
        return ZERO
    shortfall_ratio = (minimum_liquidity_depth_usd - liquidity_depth_usd) / (
        minimum_liquidity_depth_usd
    )
    return _normalize_nonnegative_decimal(
        "liquidity_damping_bps",
        shortfall_ratio * HUNDRED,
    )


def _score_status(paper_score_bps: Decimal, minimum_actionable_score: Decimal) -> str:
    if paper_score_bps <= ZERO:
        return "blocked"
    if paper_score_bps < minimum_actionable_score:
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
    current_expected_value_bps: Decimal,
    ev_decay_from_peak_bps: Decimal,
    stale_edge_penalty_bps: Decimal,
    liquidity_damping_bps: Decimal,
    total_cost_bps: Decimal,
    paper_score_bps: Decimal,
    minimum_actionable_score: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_expected_value_decay_score_v2",
        f"score_{score_status}",
        _edge_reason_code(current_expected_value_bps),
    ]
    if ev_decay_from_peak_bps > ZERO:
        additions.append("ev_decay_from_peak_detected")
    if stale_edge_penalty_bps > ZERO:
        additions.append("stale_edge_penalty_applied")
    if liquidity_damping_bps > ZERO:
        additions.append("liquidity_damping_applied")
    if total_cost_bps > ZERO:
        additions.append("cost_damping_applied")
    if paper_score_bps <= ZERO:
        additions.append("score_below_zero")
    elif paper_score_bps < minimum_actionable_score:
        additions.append("score_positive_below_minimum")
    else:
        additions.append("minimum_actionable_score_met")
    return _append_reason_codes(existing, tuple(additions))


def _edge_reason_code(current_expected_value_bps: Decimal) -> str:
    if current_expected_value_bps > ZERO:
        return "edge_positive"
    if current_expected_value_bps == ZERO:
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
    result: StrategyCandidateExpectedValueDecayScoreV2Result,
) -> None:
    if result.ev_delta_bps != _normalize_decimal(
        "ev_delta_bps",
        result.current_expected_value_bps - result.previous_expected_value_bps,
    ):
        raise ValueError("ev_delta_bps must match expected-value inputs")
    if result.ev_decay_from_peak_bps != _normalize_nonnegative_decimal(
        "ev_decay_from_peak_bps",
        max(result.peak_expected_value_bps - result.current_expected_value_bps, ZERO),
    ):
        raise ValueError("ev_decay_from_peak_bps must match expected-value inputs")
    if result.ev_decay_ratio != _decay_ratio(
        result.ev_decay_from_peak_bps,
        result.peak_expected_value_bps,
    ):
        raise ValueError("ev_decay_ratio must match expected-value inputs")
    if result.stale_edge_penalty_bps != _stale_edge_penalty_bps(
        result.current_expected_value_bps,
        result.edge_half_life_seconds,
        result.stale_quote_age_seconds,
    ):
        raise ValueError("stale_edge_penalty_bps must match age inputs")
    if result.liquidity_damping_bps != _liquidity_damping_bps(
        result.liquidity_depth_usd,
        result.minimum_liquidity_depth_usd,
    ):
        raise ValueError("liquidity_damping_bps must match depth inputs")
    if result.total_cost_bps != _normalize_nonnegative_decimal(
        "total_cost_bps",
        result.fee_bps + result.spread_bps + result.slippage_bps,
    ):
        raise ValueError("total_cost_bps must match cost inputs")
    if result.raw_decay_adjusted_edge_bps != _normalize_decimal(
        "raw_decay_adjusted_edge_bps",
        result.current_expected_value_bps - result.ev_decay_from_peak_bps,
    ):
        raise ValueError("raw_decay_adjusted_edge_bps must match decay inputs")
    if result.paper_score_bps != _normalize_decimal(
        "paper_score_bps",
        result.raw_decay_adjusted_edge_bps
        - result.stale_edge_penalty_bps
        - result.liquidity_damping_bps
        - result.total_cost_bps,
    ):
        raise ValueError("paper_score_bps must match damping inputs")
    if result.score_status != _score_status(
        result.paper_score_bps,
        result.minimum_actionable_score,
    ):
        raise ValueError("score_status must match paper_score_bps")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _derived_validation_digest(
    result: StrategyCandidateExpectedValueDecayScoreV2Result,
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


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(SECOND_QUANTUM)
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
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
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
    "StrategyCandidateExpectedValueDecayScoreV2Input",
    "StrategyCandidateExpectedValueDecayScoreV2Result",
    "estimate_strategy_candidate_expected_value_decay_score_v2",
    "strategy_candidate_expected_value_decay_score_v2_payload",
    "reject_strategy_candidate_expected_value_decay_score_v2_unsafe_payload",
)
