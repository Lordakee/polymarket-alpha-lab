"""Pure paper/report primary source confidence ladder v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
SECOND_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
OFFICIAL_SOURCE_SCORE_BPS = Decimal("120.000000")
PRIMARY_SOURCE_SCORE_BPS = Decimal("90.000000")
SECONDARY_SOURCE_SCORE_BPS = Decimal("80.000000")
MARKET_DERIVED_SOURCE_SCORE_BPS = Decimal("60.000000")
SOCIAL_SOURCE_SCORE_BPS = Decimal("30.000000")
STALE_SOURCE_RECENCY_PENALTY_BPS = Decimal("4.000000")
AGE_OVER_TARGET_RECENCY_PENALTY_BPS = Decimal("44.000000")
INDEPENDENT_SOURCE_BOOST_BPS = Decimal("15.000000")
SOCIAL_ONLY_INDEPENDENT_SOURCE_BOOST_BPS = Decimal("10.000000")
CONTRADICTION_PENALTY_BPS = Decimal("60.000000")
RESOLUTION_RULE_RELEVANCE_BOOST_BPS = Decimal("20.000000")
SOURCE_TIERS = (
    "official",
    "primary",
    "secondary",
    "market_derived",
    "social",
)
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
    "packet_id",
    "official_source_count",
    "primary_source_count",
    "secondary_source_count",
    "market_derived_source_count",
    "social_source_count",
    "fresh_source_count",
    "stale_source_count",
    "independent_source_count",
    "contradicting_source_count",
    "resolution_relevant_source_count",
    "source_count",
    "freshness_target_seconds",
    "maximum_source_age_seconds",
    "raw_source_confidence_score_bps",
    "recency_adjustment_bps",
    "independence_adjustment_bps",
    "contradiction_adjustment_bps",
    "resolution_rule_relevance_adjustment_bps",
    "paper_score_bps",
    "top_source_tier",
    "ladder_rank_summary",
    "minimum_actionable_score",
    "score_status",
    "score_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchPacketPrimarySourceConfidenceLadderV2Input:
    packet_id: str
    official_source_count: Decimal
    primary_source_count: Decimal
    secondary_source_count: Decimal
    market_derived_source_count: Decimal
    social_source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    independent_source_count: Decimal
    contradicting_source_count: Decimal
    resolution_relevant_source_count: Decimal
    source_count: Decimal
    freshness_target_seconds: Decimal
    maximum_source_age_seconds: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        for field_name in _COUNT_FIELDS:
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
            "freshness_target_seconds",
            _normalize_positive_seconds(
                "freshness_target_seconds",
                self.freshness_target_seconds,
            ),
        )
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
            "minimum_actionable_score",
            _normalize_nonnegative_decimal(
                "minimum_actionable_score",
                self.minimum_actionable_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload(
            "primary source confidence ladder input",
            self,
        )
        _require_paper_flags("primary source confidence ladder input", self)


@dataclass(frozen=True)
class ResearchPacketPrimarySourceConfidenceLadderV2Result:
    packet_id: str
    official_source_count: Decimal
    primary_source_count: Decimal
    secondary_source_count: Decimal
    market_derived_source_count: Decimal
    social_source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    independent_source_count: Decimal
    contradicting_source_count: Decimal
    resolution_relevant_source_count: Decimal
    source_count: Decimal
    freshness_target_seconds: Decimal
    maximum_source_age_seconds: Decimal
    raw_source_confidence_score_bps: Decimal
    recency_adjustment_bps: Decimal
    independence_adjustment_bps: Decimal
    contradiction_adjustment_bps: Decimal
    resolution_rule_relevance_adjustment_bps: Decimal
    paper_score_bps: Decimal
    top_source_tier: str
    ladder_rank_summary: tuple[str, ...]
    minimum_actionable_score: Decimal
    score_status: str
    score_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        for field_name in _COUNT_FIELDS:
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
            "freshness_target_seconds",
            _normalize_positive_seconds(
                "freshness_target_seconds",
                self.freshness_target_seconds,
            ),
        )
        object.__setattr__(
            self,
            "maximum_source_age_seconds",
            _normalize_nonnegative_seconds(
                "maximum_source_age_seconds",
                self.maximum_source_age_seconds,
            ),
        )
        for field_name in (
            "raw_source_confidence_score_bps",
            "independence_adjustment_bps",
            "resolution_rule_relevance_adjustment_bps",
            "minimum_actionable_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recency_adjustment_bps",
            "contradiction_adjustment_bps",
            "paper_score_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("top_source_tier", self.top_source_tier, SOURCE_TIERS)
        if self.ladder_rank_summary != SOURCE_TIERS:
            raise ValueError("ladder_rank_summary must match SOURCE_TIERS")
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        _require_choice("score_decision", self.score_decision, SCORE_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload(
            "primary source confidence ladder result",
            self,
        )
        _require_paper_flags("primary source confidence ladder result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_primary_source_confidence_ladder_v2_payload(self)


_COUNT_FIELDS = (
    "official_source_count",
    "primary_source_count",
    "secondary_source_count",
    "market_derived_source_count",
    "social_source_count",
    "fresh_source_count",
    "stale_source_count",
    "independent_source_count",
    "contradicting_source_count",
    "resolution_relevant_source_count",
    "source_count",
)


def estimate_research_packet_primary_source_confidence_ladder_v2(
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
) -> ResearchPacketPrimarySourceConfidenceLadderV2Result:
    if type(score_input) is not ResearchPacketPrimarySourceConfidenceLadderV2Input:
        raise ValueError(
            "score_input must be a ResearchPacketPrimarySourceConfidenceLadderV2Input",
        )
    reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload(
        "primary source confidence ladder input",
        score_input,
    )
    _require_paper_flags("primary source confidence ladder input", score_input)

    top_source_tier = _top_source_tier(score_input)
    raw_source_confidence_score_bps = _raw_source_confidence_score_bps(score_input)
    recency_adjustment_bps = _recency_adjustment_bps(score_input)
    independence_adjustment_bps = _independence_adjustment_bps(
        score_input,
        top_source_tier,
    )
    contradiction_adjustment_bps = _contradiction_adjustment_bps(score_input)
    resolution_rule_relevance_adjustment_bps = (
        _resolution_rule_relevance_adjustment_bps(score_input)
    )
    paper_score_bps = _normalize_decimal(
        "paper_score_bps",
        raw_source_confidence_score_bps
        + recency_adjustment_bps
        + independence_adjustment_bps
        + contradiction_adjustment_bps
        + resolution_rule_relevance_adjustment_bps,
    )
    score_status = _score_status(
        paper_score_bps,
        score_input.minimum_actionable_score,
    )

    return ResearchPacketPrimarySourceConfidenceLadderV2Result(
        packet_id=score_input.packet_id,
        official_source_count=score_input.official_source_count,
        primary_source_count=score_input.primary_source_count,
        secondary_source_count=score_input.secondary_source_count,
        market_derived_source_count=score_input.market_derived_source_count,
        social_source_count=score_input.social_source_count,
        fresh_source_count=score_input.fresh_source_count,
        stale_source_count=score_input.stale_source_count,
        independent_source_count=score_input.independent_source_count,
        contradicting_source_count=score_input.contradicting_source_count,
        resolution_relevant_source_count=score_input.resolution_relevant_source_count,
        source_count=score_input.source_count,
        freshness_target_seconds=score_input.freshness_target_seconds,
        maximum_source_age_seconds=score_input.maximum_source_age_seconds,
        raw_source_confidence_score_bps=raw_source_confidence_score_bps,
        recency_adjustment_bps=recency_adjustment_bps,
        independence_adjustment_bps=independence_adjustment_bps,
        contradiction_adjustment_bps=contradiction_adjustment_bps,
        resolution_rule_relevance_adjustment_bps=(
            resolution_rule_relevance_adjustment_bps
        ),
        paper_score_bps=paper_score_bps,
        top_source_tier=top_source_tier,
        ladder_rank_summary=SOURCE_TIERS,
        minimum_actionable_score=score_input.minimum_actionable_score,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            top_source_tier=top_source_tier,
            recency_adjustment_bps=recency_adjustment_bps,
            independence_adjustment_bps=independence_adjustment_bps,
            contradiction_adjustment_bps=contradiction_adjustment_bps,
            resolution_rule_relevance_adjustment_bps=(
                resolution_rule_relevance_adjustment_bps
            ),
            paper_score_bps=paper_score_bps,
            minimum_actionable_score=score_input.minimum_actionable_score,
            score_status=score_status,
        ),
    )


def research_packet_primary_source_confidence_ladder_v2_payload(
    result: ResearchPacketPrimarySourceConfidenceLadderV2Result,
) -> dict[str, Any]:
    if type(result) is not ResearchPacketPrimarySourceConfidenceLadderV2Result:
        raise ValueError(
            "result must be a ResearchPacketPrimarySourceConfidenceLadderV2Result",
        )
    _require_paper_flags("primary source confidence ladder result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload(
        "primary source confidence ladder result",
        result,
    )
    return _json_ready(asdict(result))


def reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _raw_source_confidence_score_bps(
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "raw_source_confidence_score_bps",
        score_input.official_source_count * OFFICIAL_SOURCE_SCORE_BPS
        + score_input.primary_source_count * PRIMARY_SOURCE_SCORE_BPS
        + score_input.secondary_source_count * SECONDARY_SOURCE_SCORE_BPS
        + score_input.market_derived_source_count * MARKET_DERIVED_SOURCE_SCORE_BPS
        + score_input.social_source_count * SOCIAL_SOURCE_SCORE_BPS,
    )


def _recency_adjustment_bps(
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
) -> Decimal:
    age_over_target_ratio = ZERO
    if score_input.maximum_source_age_seconds > score_input.freshness_target_seconds:
        age_over_target_ratio = (
            score_input.maximum_source_age_seconds
            - score_input.freshness_target_seconds
        ) / score_input.freshness_target_seconds
    return _normalize_decimal(
        "recency_adjustment_bps",
        -(
            score_input.stale_source_count * STALE_SOURCE_RECENCY_PENALTY_BPS
            + age_over_target_ratio * AGE_OVER_TARGET_RECENCY_PENALTY_BPS
        ),
    )


def _independence_adjustment_bps(
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
    top_source_tier: str,
) -> Decimal:
    source_boost_bps = INDEPENDENT_SOURCE_BOOST_BPS
    if top_source_tier == "social":
        source_boost_bps = SOCIAL_ONLY_INDEPENDENT_SOURCE_BOOST_BPS
    return _normalize_nonnegative_decimal(
        "independence_adjustment_bps",
        score_input.independent_source_count * source_boost_bps,
    )


def _contradiction_adjustment_bps(
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
) -> Decimal:
    return _normalize_decimal(
        "contradiction_adjustment_bps",
        -(score_input.contradicting_source_count * CONTRADICTION_PENALTY_BPS),
    )


def _resolution_rule_relevance_adjustment_bps(
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "resolution_rule_relevance_adjustment_bps",
        score_input.resolution_relevant_source_count
        * RESOLUTION_RULE_RELEVANCE_BOOST_BPS,
    )


def _top_source_tier(
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
) -> str:
    if score_input.official_source_count > ZERO:
        return "official"
    if score_input.primary_source_count > ZERO:
        return "primary"
    if score_input.secondary_source_count > ZERO:
        return "secondary"
    if score_input.market_derived_source_count > ZERO:
        return "market_derived"
    if score_input.social_source_count > ZERO:
        return "social"
    raise ValueError("at least one source tier must be present")


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
    top_source_tier: str,
    recency_adjustment_bps: Decimal,
    independence_adjustment_bps: Decimal,
    contradiction_adjustment_bps: Decimal,
    resolution_rule_relevance_adjustment_bps: Decimal,
    paper_score_bps: Decimal,
    minimum_actionable_score: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "research_packet_primary_source_confidence_ladder_v2",
        f"score_{score_status}",
        f"{top_source_tier}_source_top_ranked",
    ]
    if recency_adjustment_bps < ZERO:
        additions.append("recency_penalty_applied")
    if independence_adjustment_bps > ZERO:
        additions.append("independence_boost_applied")
    if contradiction_adjustment_bps < ZERO:
        additions.append("contradiction_penalty_applied")
    if resolution_rule_relevance_adjustment_bps > ZERO:
        additions.append("resolution_rule_relevance_boost_applied")
    if paper_score_bps <= ZERO:
        additions.append("score_below_zero")
    elif paper_score_bps < minimum_actionable_score:
        additions.append("score_positive_below_minimum")
    else:
        additions.append("minimum_actionable_score_met")
    return _append_reason_codes(existing, tuple(additions))


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
    score_input: ResearchPacketPrimarySourceConfidenceLadderV2Input,
) -> None:
    if _tier_source_count(score_input) != score_input.source_count:
        raise ValueError("source counts must classify every source")
    if score_input.fresh_source_count + score_input.stale_source_count != (
        score_input.source_count
    ):
        raise ValueError("fresh and stale counts must classify every source")
    _validate_subset_counts(score_input)


def _validate_result_counts(
    result: ResearchPacketPrimarySourceConfidenceLadderV2Result,
) -> None:
    if _tier_source_count(result) != result.source_count:
        raise ValueError("source counts must classify every source")
    if result.fresh_source_count + result.stale_source_count != result.source_count:
        raise ValueError("fresh and stale counts must classify every source")
    _validate_subset_counts(result)


def _validate_subset_counts(value: object) -> None:
    for field_name in (
        "independent_source_count",
        "contradicting_source_count",
        "resolution_relevant_source_count",
    ):
        if getattr(value, field_name) > getattr(value, "source_count"):
            raise ValueError(f"{field_name} must not exceed source_count")


def _validate_result_consistency(
    result: ResearchPacketPrimarySourceConfidenceLadderV2Result,
) -> None:
    if result.raw_source_confidence_score_bps != _raw_source_confidence_score_bps(
        result,
    ):
        raise ValueError("raw_source_confidence_score_bps must match source tiers")
    if result.recency_adjustment_bps != _recency_adjustment_bps(result):
        raise ValueError("recency_adjustment_bps must match source freshness")
    if result.independence_adjustment_bps != _independence_adjustment_bps(
        result,
        result.top_source_tier,
    ):
        raise ValueError("independence_adjustment_bps must match independent sources")
    if result.contradiction_adjustment_bps != _contradiction_adjustment_bps(result):
        raise ValueError("contradiction_adjustment_bps must match contradicting sources")
    if result.resolution_rule_relevance_adjustment_bps != (
        _resolution_rule_relevance_adjustment_bps(result)
    ):
        raise ValueError(
            "resolution_rule_relevance_adjustment_bps must match source relevance",
        )
    if result.top_source_tier != _top_source_tier(result):
        raise ValueError("top_source_tier must match source tiers")
    if result.paper_score_bps != _normalize_decimal(
        "paper_score_bps",
        result.raw_source_confidence_score_bps
        + result.recency_adjustment_bps
        + result.independence_adjustment_bps
        + result.contradiction_adjustment_bps
        + result.resolution_rule_relevance_adjustment_bps,
    ):
        raise ValueError("paper_score_bps must match score components")
    if result.score_status != _score_status(
        result.paper_score_bps,
        result.minimum_actionable_score,
    ):
        raise ValueError("score_status must match paper_score_bps")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _tier_source_count(value: object) -> Decimal:
    return _normalize_nonnegative_count(
        "tier_source_count",
        getattr(value, "official_source_count")
        + getattr(value, "primary_source_count")
        + getattr(value, "secondary_source_count")
        + getattr(value, "market_derived_source_count")
        + getattr(value, "social_source_count"),
    )


def _derived_validation_digest(
    result: ResearchPacketPrimarySourceConfidenceLadderV2Result,
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
    "SOURCE_TIERS",
    "ResearchPacketPrimarySourceConfidenceLadderV2Input",
    "ResearchPacketPrimarySourceConfidenceLadderV2Result",
    "estimate_research_packet_primary_source_confidence_ladder_v2",
    "research_packet_primary_source_confidence_ladder_v2_payload",
    "reject_research_packet_primary_source_confidence_ladder_v2_unsafe_payload",
)
