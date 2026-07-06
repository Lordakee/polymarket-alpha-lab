"""Pure probability-event feature extraction for Polymarket strategy inputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import re
from typing import Any


PROBABILITY_EVENT_MARKET_MODEL_KIND = "probability_event_market"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)

EVENT_TYPES = (
    "crypto",
    "economic_data",
    "entertainment",
    "legal_regulatory",
    "macro_policy",
    "politics",
    "sports",
    "weather",
    "other",
)
AMBIGUOUS_RESOLUTION_FLAGS = (
    "conditional_resolution_terms",
    "disputed_or_recount_risk",
    "unofficial_source_dependency",
    "subjective_resolution_terms",
)

_THRESHOLD_PATTERNS = (
    re.compile(r"\$[0-9][0-9,]*(?:\.[0-9]+)?"),
    re.compile(
        r"\b[0-9]+(?:\.[0-9]+)?\s*(?:bps?|basis points?|%|percent|points?|"
        r"votes?|seats?|goals?|runs?|dollars?)\b",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class StrategyProbabilityEventFeatures:
    event_type: str
    time_to_resolution_hours: Decimal
    probability_count: Decimal
    normalized_probabilities: tuple[Decimal, ...]
    implied_probability_sum: Decimal
    binary_outcome_hint: bool
    threshold_hint: bool
    threshold_terms: tuple[str, ...]
    multi_outcome_hint: bool
    ambiguous_resolution_flags: tuple[str, ...]
    model_kind: str = PROBABILITY_EVENT_MARKET_MODEL_KIND
    price_asset_model: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyProbabilityEventFeatures:
            raise ValueError("features must be a StrategyProbabilityEventFeatures")
        if self.model_kind != PROBABILITY_EVENT_MARKET_MODEL_KIND:
            raise ValueError("model_kind must be probability_event_market")
        if self.price_asset_model is not False:
            raise ValueError("price_asset_model must be False for probability events")
        _require_member("event_type", self.event_type, EVENT_TYPES)
        object.__setattr__(
            self,
            "time_to_resolution_hours",
            _normalize_nonnegative_decimal(
                "time_to_resolution_hours",
                self.time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "probability_count",
            _normalize_positive_whole_decimal("probability_count", self.probability_count),
        )
        object.__setattr__(
            self,
            "normalized_probabilities",
            _normalize_probabilities(self.normalized_probabilities),
        )
        object.__setattr__(
            self,
            "implied_probability_sum",
            _normalize_probability_sum(
                "implied_probability_sum",
                self.implied_probability_sum,
            ),
        )
        if self.probability_count != Decimal(len(self.normalized_probabilities)):
            raise ValueError("probability_count must match normalized_probabilities")
        if self.implied_probability_sum != _sum_probabilities(self.normalized_probabilities):
            raise ValueError("implied_probability_sum must match normalized_probabilities")
        _require_bool("binary_outcome_hint", self.binary_outcome_hint)
        _require_bool("threshold_hint", self.threshold_hint)
        _require_bool("multi_outcome_hint", self.multi_outcome_hint)
        object.__setattr__(
            self,
            "threshold_terms",
            _normalize_string_tuple("threshold_terms", self.threshold_terms),
        )
        if self.threshold_hint != bool(self.threshold_terms):
            raise ValueError("threshold_hint must match threshold_terms")
        object.__setattr__(
            self,
            "ambiguous_resolution_flags",
            _normalize_flags(
                "ambiguous_resolution_flags",
                self.ambiguous_resolution_flags,
                AMBIGUOUS_RESOLUTION_FLAGS,
            ),
        )
        _require_hard_flags(self)


def extract_strategy_probability_event_features(
    *,
    question: str,
    category: str,
    tags: tuple[str, ...],
    end_date: datetime,
    probabilities: tuple[Decimal, ...],
    as_of: datetime,
) -> StrategyProbabilityEventFeatures:
    """Extract deterministic hints from a probability-event market description."""

    _require_canonical_string("question", question)
    _require_canonical_string("category", category)
    normalized_tags = _normalize_string_tuple("tags", tags)
    end_date = _as_utc("end_date", end_date)
    as_of = _as_utc("as_of", as_of)
    if end_date < as_of:
        raise ValueError("end_date must not be before as_of")

    normalized_probabilities = _normalize_probabilities(probabilities)
    text = _combined_text(question, category, normalized_tags)
    threshold_terms = _threshold_terms(question)

    return StrategyProbabilityEventFeatures(
        event_type=_event_type(text),
        time_to_resolution_hours=_hours_between(as_of, end_date),
        probability_count=Decimal(len(normalized_probabilities)),
        normalized_probabilities=normalized_probabilities,
        implied_probability_sum=_sum_probabilities(normalized_probabilities),
        binary_outcome_hint=len(normalized_probabilities) == 2,
        threshold_hint=bool(threshold_terms),
        threshold_terms=threshold_terms,
        multi_outcome_hint=len(normalized_probabilities) > 2,
        ambiguous_resolution_flags=_ambiguous_resolution_flags(text),
    )


def strategy_probability_event_features_payload(
    features: StrategyProbabilityEventFeatures,
) -> dict[str, Any]:
    if type(features) is not StrategyProbabilityEventFeatures:
        raise ValueError("features must be a StrategyProbabilityEventFeatures")
    return _payload_value(asdict(features))


def _event_type(text: str) -> str:
    if _contains_any(text, ("crypto", "bitcoin", "btc", "ethereum", "eth", "solana")):
        return "crypto"
    if _contains_any(text, ("election", "politic", "candidate", "senate", "president")):
        return "politics"
    if _contains_any(
        text,
        (
            "nba",
            "basketball",
            "nfl",
            "mlb",
            "nhl",
            "soccer",
            "tennis",
            "sports",
            "championship",
            "finals",
        ),
    ):
        return "sports"
    if _contains_any(text, ("fed", "fomc", "interest rate", "rates", "macro", "central bank")):
        return "macro_policy"
    if _contains_any(text, ("cpi", "gdp", "payroll", "jobs report", "inflation")):
        return "economic_data"
    if _contains_any(text, ("court", "injunction", "lawsuit", "regulation", "sec", "fda")):
        return "legal_regulatory"
    if _contains_any(text, ("hurricane", "weather", "rain", "snow", "temperature")):
        return "weather"
    if _contains_any(text, ("oscar", "grammy", "box office", "movie", "album")):
        return "entertainment"
    return "other"


def _threshold_terms(question: str) -> tuple[str, ...]:
    if not _contains_any(
        question.casefold(),
        (
            "above",
            "below",
            "over",
            "under",
            "at least",
            "at most",
            "greater than",
            "less than",
            "more than",
            "fewer than",
            "$",
            "%",
            "bps",
            "basis point",
        ),
    ):
        return ()

    terms: list[str] = []
    for pattern in _THRESHOLD_PATTERNS:
        for match in pattern.finditer(question):
            term = match.group(0).strip()
            if term not in terms:
                terms.append(term)
    return tuple(terms)


def _ambiguous_resolution_flags(text: str) -> tuple[str, ...]:
    flags: list[str] = []
    if _contains_any(text, (" if ", "unless", "pending", "conditional", "provided that")):
        flags.append("conditional_resolution_terms")
    if _contains_any(text, ("recount", "lawsuit", "dispute", "contested", "challenge")):
        flags.append("disputed_or_recount_risk")
    if _contains_any(text, ("called", "projected", "declared by", "media", "unofficial")):
        flags.append("unofficial_source_dependency")
    if _contains_any(text, ("best", "most important", "successful", "significant")):
        flags.append("subjective_resolution_terms")
    return tuple(flags)


def _combined_text(question: str, category: str, tags: tuple[str, ...]) -> str:
    return " ".join((question, category, *tags)).casefold()


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _hours_between(start: datetime, end: datetime) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(str((end - start).total_seconds()))
        return (seconds / Decimal("3600")).quantize(QUANTUM)


def _normalize_probabilities(values: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    if type(values) is not tuple:
        raise ValueError("probabilities must be a tuple")
    if not values:
        raise ValueError("probabilities must contain at least one probability")
    probabilities = tuple(
        _normalize_probability("probabilities", value)
        for value in values
    )
    _sum_probabilities(probabilities)
    return probabilities


def _sum_probabilities(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO).quantize(QUANTUM)
    if total > ONE:
        raise ValueError("probabilities must sum to at most 1")
    return total


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_probability_sum(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_probability(field_name, value)
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANTUM)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(COUNT_QUANTUM)
    if value != decimal_value:
        raise ValueError(f"{field_name} must be a whole number")
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_string_tuple(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _normalize_flags(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    values = _normalize_string_tuple(field_name, values)
    for value in values:
        _require_member(field_name, value, allowed_values)
    return values


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_member(
    field_name: str,
    value: str,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value


__all__ = [
    "PROBABILITY_EVENT_MARKET_MODEL_KIND",
    "StrategyProbabilityEventFeatures",
    "extract_strategy_probability_event_features",
    "strategy_probability_event_features_payload",
]
