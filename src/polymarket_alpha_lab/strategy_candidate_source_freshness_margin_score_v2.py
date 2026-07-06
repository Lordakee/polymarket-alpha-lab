"""Pure paper/report candidate source freshness margin score v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
SECOND_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STALE_SOURCE_BASE_PENALTY_BPS = Decimal("25.000000")
STALE_AGE_OVERAGE_PENALTY_BPS = Decimal("20.000000")
OFFICIAL_SOURCE_BOOST_BPS = Decimal("20.000000")
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
    "source_count",
    "fresh_source_count",
    "stale_source_count",
    "official_source_count",
    "maximum_source_age_seconds",
    "freshness_target_seconds",
    "base_margin_bps",
    "source_freshness_margin_ratio",
    "raw_source_margin_bps",
    "stale_source_penalty_bps",
    "official_source_boost_bps",
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
class StrategyCandidateSourceFreshnessMarginScoreV2Input:
    candidate_id: str
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    official_source_count: Decimal
    maximum_source_age_seconds: Decimal
    freshness_target_seconds: Decimal
    base_margin_bps: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "official_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.source_count <= ZERO:
            raise ValueError("source_count must be positive")
        _validate_input_counts(self)
        object.__setattr__(
            self,
            "maximum_source_age_seconds",
            _normalize_nonnegative_seconds(
                "maximum_source_age_seconds",
                self.maximum_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "freshness_target_seconds",
            _normalize_positive_seconds(
                "freshness_target_seconds",
                self.freshness_target_seconds,
            ),
        )
        for field_name in ("base_margin_bps", "minimum_actionable_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload(
            "candidate source freshness margin score input",
            self,
        )
        _require_paper_flags("candidate source freshness margin score input", self)


@dataclass(frozen=True)
class StrategyCandidateSourceFreshnessMarginScoreV2Result:
    candidate_id: str
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    official_source_count: Decimal
    maximum_source_age_seconds: Decimal
    freshness_target_seconds: Decimal
    base_margin_bps: Decimal
    source_freshness_margin_ratio: Decimal
    raw_source_margin_bps: Decimal
    stale_source_penalty_bps: Decimal
    official_source_boost_bps: Decimal
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
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "official_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.source_count <= ZERO:
            raise ValueError("source_count must be positive")
        _validate_result_counts(self)
        object.__setattr__(
            self,
            "maximum_source_age_seconds",
            _normalize_nonnegative_seconds(
                "maximum_source_age_seconds",
                self.maximum_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "freshness_target_seconds",
            _normalize_positive_seconds(
                "freshness_target_seconds",
                self.freshness_target_seconds,
            ),
        )
        for field_name in (
            "base_margin_bps",
            "source_freshness_margin_ratio",
            "raw_source_margin_bps",
            "stale_source_penalty_bps",
            "official_source_boost_bps",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "paper_score_bps",
            _normalize_decimal("paper_score_bps", self.paper_score_bps),
        )
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        _require_choice("score_decision", self.score_decision, SCORE_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload(
            "candidate source freshness margin score result",
            self,
        )
        _require_paper_flags("candidate source freshness margin score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_source_freshness_margin_score_v2_payload(self)


def estimate_strategy_candidate_source_freshness_margin_score_v2(
    score_input: StrategyCandidateSourceFreshnessMarginScoreV2Input,
) -> StrategyCandidateSourceFreshnessMarginScoreV2Result:
    if type(score_input) is not StrategyCandidateSourceFreshnessMarginScoreV2Input:
        raise ValueError(
            "score_input must be a StrategyCandidateSourceFreshnessMarginScoreV2Input",
        )
    reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload(
        "candidate source freshness margin score input",
        score_input,
    )
    _require_paper_flags("candidate source freshness margin score input", score_input)

    source_freshness_margin_ratio = _source_freshness_margin_ratio(
        score_input.fresh_source_count,
        score_input.source_count,
    )
    raw_source_margin_bps = _raw_source_margin_bps(
        score_input.base_margin_bps,
        source_freshness_margin_ratio,
    )
    stale_source_penalty_bps = _stale_source_penalty_bps(
        score_input.stale_source_count,
        score_input.maximum_source_age_seconds,
        score_input.freshness_target_seconds,
    )
    official_source_boost_bps = _official_source_boost_bps(
        score_input.official_source_count,
    )
    paper_score_bps = _normalize_decimal(
        "paper_score_bps",
        raw_source_margin_bps - stale_source_penalty_bps + official_source_boost_bps,
    )
    score_status = _score_status(
        paper_score_bps,
        score_input.minimum_actionable_score,
    )

    return StrategyCandidateSourceFreshnessMarginScoreV2Result(
        candidate_id=score_input.candidate_id,
        source_count=score_input.source_count,
        fresh_source_count=score_input.fresh_source_count,
        stale_source_count=score_input.stale_source_count,
        official_source_count=score_input.official_source_count,
        maximum_source_age_seconds=score_input.maximum_source_age_seconds,
        freshness_target_seconds=score_input.freshness_target_seconds,
        base_margin_bps=score_input.base_margin_bps,
        source_freshness_margin_ratio=source_freshness_margin_ratio,
        raw_source_margin_bps=raw_source_margin_bps,
        stale_source_penalty_bps=stale_source_penalty_bps,
        official_source_boost_bps=official_source_boost_bps,
        paper_score_bps=paper_score_bps,
        minimum_actionable_score=score_input.minimum_actionable_score,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            source_freshness_margin_ratio=source_freshness_margin_ratio,
            stale_source_penalty_bps=stale_source_penalty_bps,
            official_source_boost_bps=official_source_boost_bps,
            paper_score_bps=paper_score_bps,
            minimum_actionable_score=score_input.minimum_actionable_score,
            score_status=score_status,
        ),
    )


def strategy_candidate_source_freshness_margin_score_v2_payload(
    result: StrategyCandidateSourceFreshnessMarginScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateSourceFreshnessMarginScoreV2Result:
        raise ValueError(
            "result must be a StrategyCandidateSourceFreshnessMarginScoreV2Result",
        )
    _require_paper_flags("candidate source freshness margin score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload(
        "candidate source freshness margin score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _source_freshness_margin_ratio(
    fresh_source_count: Decimal,
    source_count: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "source_freshness_margin_ratio",
        fresh_source_count / source_count,
    )


def _raw_source_margin_bps(
    base_margin_bps: Decimal,
    source_freshness_margin_ratio: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "raw_source_margin_bps",
        base_margin_bps * source_freshness_margin_ratio,
    )


def _stale_source_penalty_bps(
    stale_source_count: Decimal,
    maximum_source_age_seconds: Decimal,
    freshness_target_seconds: Decimal,
) -> Decimal:
    age_overage_ratio = ZERO
    if maximum_source_age_seconds > freshness_target_seconds:
        age_overage_ratio = (
            maximum_source_age_seconds - freshness_target_seconds
        ) / freshness_target_seconds
    return _normalize_nonnegative_decimal(
        "stale_source_penalty_bps",
        stale_source_count * STALE_SOURCE_BASE_PENALTY_BPS
        + age_overage_ratio * STALE_AGE_OVERAGE_PENALTY_BPS,
    )


def _official_source_boost_bps(official_source_count: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(
        "official_source_boost_bps",
        official_source_count * OFFICIAL_SOURCE_BOOST_BPS,
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
    source_freshness_margin_ratio: Decimal,
    stale_source_penalty_bps: Decimal,
    official_source_boost_bps: Decimal,
    paper_score_bps: Decimal,
    minimum_actionable_score: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_source_freshness_margin_score_v2",
        f"score_{score_status}",
        _freshness_reason_code(source_freshness_margin_ratio),
    ]
    if stale_source_penalty_bps > ZERO:
        additions.append("stale_source_penalty_applied")
    if official_source_boost_bps > ZERO:
        additions.append("official_source_boost_applied")
    if paper_score_bps <= ZERO:
        additions.append("score_below_zero")
    elif paper_score_bps < minimum_actionable_score:
        additions.append("score_positive_below_minimum")
    else:
        additions.append("minimum_actionable_score_met")
    return _append_reason_codes(existing, tuple(additions))


def _freshness_reason_code(source_freshness_margin_ratio: Decimal) -> str:
    if source_freshness_margin_ratio >= Decimal("0.500000"):
        return "fresh_source_majority"
    return "fresh_source_minority"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_input_counts(
    score_input: StrategyCandidateSourceFreshnessMarginScoreV2Input,
) -> None:
    if score_input.fresh_source_count + score_input.stale_source_count != (
        score_input.source_count
    ):
        raise ValueError("source counts must classify every source")
    if score_input.official_source_count > score_input.source_count:
        raise ValueError("official_source_count must not exceed source_count")


def _validate_result_counts(
    result: StrategyCandidateSourceFreshnessMarginScoreV2Result,
) -> None:
    if result.fresh_source_count + result.stale_source_count != result.source_count:
        raise ValueError("source counts must classify every source")
    if result.official_source_count > result.source_count:
        raise ValueError("official_source_count must not exceed source_count")


def _validate_result_consistency(
    result: StrategyCandidateSourceFreshnessMarginScoreV2Result,
) -> None:
    if result.source_freshness_margin_ratio != _source_freshness_margin_ratio(
        result.fresh_source_count,
        result.source_count,
    ):
        raise ValueError("source_freshness_margin_ratio must match source counts")
    if result.raw_source_margin_bps != _raw_source_margin_bps(
        result.base_margin_bps,
        result.source_freshness_margin_ratio,
    ):
        raise ValueError("raw_source_margin_bps must match source freshness")
    if result.stale_source_penalty_bps != _stale_source_penalty_bps(
        result.stale_source_count,
        result.maximum_source_age_seconds,
        result.freshness_target_seconds,
    ):
        raise ValueError("stale_source_penalty_bps must match source age")
    if result.official_source_boost_bps != _official_source_boost_bps(
        result.official_source_count,
    ):
        raise ValueError("official_source_boost_bps must match official sources")
    if result.paper_score_bps != _normalize_decimal(
        "paper_score_bps",
        result.raw_source_margin_bps
        - result.stale_source_penalty_bps
        + result.official_source_boost_bps,
    ):
        raise ValueError("paper_score_bps must match score components")
    if result.score_status != _score_status(
        result.paper_score_bps,
        result.minimum_actionable_score,
    ):
        raise ValueError("score_status must match paper_score_bps")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _derived_validation_digest(
    result: StrategyCandidateSourceFreshnessMarginScoreV2Result,
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


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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
    "StrategyCandidateSourceFreshnessMarginScoreV2Input",
    "StrategyCandidateSourceFreshnessMarginScoreV2Result",
    "estimate_strategy_candidate_source_freshness_margin_score_v2",
    "strategy_candidate_source_freshness_margin_score_v2_payload",
    "reject_strategy_candidate_source_freshness_margin_score_v2_unsafe_payload",
)
