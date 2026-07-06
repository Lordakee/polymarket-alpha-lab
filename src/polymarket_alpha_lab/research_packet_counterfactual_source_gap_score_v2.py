"""Pure paper/report counterfactual source gap score v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SOURCE_EVIDENCE_BPS = Decimal("50.000000")
SOURCE_GAP_PENALTY_BPS = Decimal("25.000000")
MISSING_BEAR_CASE_EVIDENCE_PENALTY_BPS = Decimal("75.000000")
INDEPENDENT_SOURCE_DIVERSITY_BPS = Decimal("10.000000")
CONFLICTING_SOURCE_DIVERSITY_BPS = Decimal("15.000000")
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
    "base_case_source_count",
    "counterfactual_source_count",
    "independent_source_count",
    "conflicting_source_count",
    "bear_case_evidence_count",
    "minimum_bear_case_evidence_count",
    "minimum_source_diversity_count",
    "source_gap_count",
    "counterfactual_source_coverage_ratio",
    "source_gap_penalty_bps",
    "missing_bear_case_evidence_count",
    "missing_bear_case_evidence_penalty_bps",
    "source_diversity_boost_bps",
    "raw_counterfactual_source_score_bps",
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
class ResearchPacketCounterfactualSourceGapScoreV2Input:
    packet_id: str
    base_case_source_count: Decimal
    counterfactual_source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    bear_case_evidence_count: Decimal
    minimum_bear_case_evidence_count: Decimal
    minimum_source_diversity_count: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        for field_name in (
            "base_case_source_count",
            "counterfactual_source_count",
            "independent_source_count",
            "conflicting_source_count",
            "bear_case_evidence_count",
            "minimum_bear_case_evidence_count",
            "minimum_source_diversity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.base_case_source_count <= ZERO:
            raise ValueError("base_case_source_count must be positive")
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
        reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload(
            "counterfactual source gap score input",
            self,
        )
        _require_paper_flags("counterfactual source gap score input", self)


@dataclass(frozen=True)
class ResearchPacketCounterfactualSourceGapScoreV2Result:
    packet_id: str
    base_case_source_count: Decimal
    counterfactual_source_count: Decimal
    independent_source_count: Decimal
    conflicting_source_count: Decimal
    bear_case_evidence_count: Decimal
    minimum_bear_case_evidence_count: Decimal
    minimum_source_diversity_count: Decimal
    source_gap_count: Decimal
    counterfactual_source_coverage_ratio: Decimal
    source_gap_penalty_bps: Decimal
    missing_bear_case_evidence_count: Decimal
    missing_bear_case_evidence_penalty_bps: Decimal
    source_diversity_boost_bps: Decimal
    raw_counterfactual_source_score_bps: Decimal
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
        _require_canonical_string("packet_id", self.packet_id)
        for field_name in (
            "base_case_source_count",
            "counterfactual_source_count",
            "independent_source_count",
            "conflicting_source_count",
            "bear_case_evidence_count",
            "minimum_bear_case_evidence_count",
            "minimum_source_diversity_count",
            "source_gap_count",
            "missing_bear_case_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.base_case_source_count <= ZERO:
            raise ValueError("base_case_source_count must be positive")
        for field_name in (
            "counterfactual_source_coverage_ratio",
            "source_gap_penalty_bps",
            "missing_bear_case_evidence_penalty_bps",
            "source_diversity_boost_bps",
            "raw_counterfactual_source_score_bps",
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
        reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload(
            "counterfactual source gap score result",
            self,
        )
        _require_paper_flags("counterfactual source gap score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_counterfactual_source_gap_score_v2_payload(self)


def estimate_research_packet_counterfactual_source_gap_score_v2(
    score_input: ResearchPacketCounterfactualSourceGapScoreV2Input,
) -> ResearchPacketCounterfactualSourceGapScoreV2Result:
    if type(score_input) is not ResearchPacketCounterfactualSourceGapScoreV2Input:
        raise ValueError(
            "score_input must be a ResearchPacketCounterfactualSourceGapScoreV2Input",
        )
    reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload(
        "counterfactual source gap score input",
        score_input,
    )
    _require_paper_flags("counterfactual source gap score input", score_input)

    source_gap_count = _source_gap_count(
        score_input.base_case_source_count,
        score_input.counterfactual_source_count,
    )
    coverage_ratio = _counterfactual_source_coverage_ratio(
        score_input.base_case_source_count,
        score_input.counterfactual_source_count,
    )
    source_gap_penalty_bps = _source_gap_penalty_bps(source_gap_count)
    missing_bear_case_evidence_count = _missing_bear_case_evidence_count(
        score_input.bear_case_evidence_count,
        score_input.minimum_bear_case_evidence_count,
    )
    missing_bear_case_evidence_penalty_bps = (
        _missing_bear_case_evidence_penalty_bps(missing_bear_case_evidence_count)
    )
    source_diversity_boost_bps = _source_diversity_boost_bps(
        score_input.independent_source_count,
        score_input.conflicting_source_count,
        score_input.minimum_source_diversity_count,
    )
    raw_counterfactual_source_score_bps = _raw_counterfactual_source_score_bps(
        score_input.counterfactual_source_count,
    )
    paper_score_bps = _normalize_decimal(
        "paper_score_bps",
        raw_counterfactual_source_score_bps
        - source_gap_penalty_bps
        - missing_bear_case_evidence_penalty_bps
        + source_diversity_boost_bps,
    )
    score_status = _score_status(
        paper_score_bps,
        score_input.minimum_actionable_score,
    )

    return ResearchPacketCounterfactualSourceGapScoreV2Result(
        packet_id=score_input.packet_id,
        base_case_source_count=score_input.base_case_source_count,
        counterfactual_source_count=score_input.counterfactual_source_count,
        independent_source_count=score_input.independent_source_count,
        conflicting_source_count=score_input.conflicting_source_count,
        bear_case_evidence_count=score_input.bear_case_evidence_count,
        minimum_bear_case_evidence_count=score_input.minimum_bear_case_evidence_count,
        minimum_source_diversity_count=score_input.minimum_source_diversity_count,
        source_gap_count=source_gap_count,
        counterfactual_source_coverage_ratio=coverage_ratio,
        source_gap_penalty_bps=source_gap_penalty_bps,
        missing_bear_case_evidence_count=missing_bear_case_evidence_count,
        missing_bear_case_evidence_penalty_bps=(
            missing_bear_case_evidence_penalty_bps
        ),
        source_diversity_boost_bps=source_diversity_boost_bps,
        raw_counterfactual_source_score_bps=raw_counterfactual_source_score_bps,
        paper_score_bps=paper_score_bps,
        minimum_actionable_score=score_input.minimum_actionable_score,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            source_gap_count=source_gap_count,
            missing_bear_case_evidence_count=missing_bear_case_evidence_count,
            source_diversity_boost_bps=source_diversity_boost_bps,
            paper_score_bps=paper_score_bps,
            minimum_actionable_score=score_input.minimum_actionable_score,
            score_status=score_status,
        ),
    )


def research_packet_counterfactual_source_gap_score_v2_payload(
    result: ResearchPacketCounterfactualSourceGapScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not ResearchPacketCounterfactualSourceGapScoreV2Result:
        raise ValueError(
            "result must be a ResearchPacketCounterfactualSourceGapScoreV2Result",
        )
    _require_paper_flags("counterfactual source gap score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload(
        "counterfactual source gap score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _source_gap_count(base_case_count: Decimal, counterfactual_count: Decimal) -> Decimal:
    return _normalize_nonnegative_count(
        "source_gap_count",
        max(base_case_count - counterfactual_count, ZERO),
    )


def _counterfactual_source_coverage_ratio(
    base_case_count: Decimal,
    counterfactual_count: Decimal,
) -> Decimal:
    if counterfactual_count >= base_case_count:
        return ONE
    return _normalize_nonnegative_decimal(
        "counterfactual_source_coverage_ratio",
        counterfactual_count / base_case_count,
    )


def _source_gap_penalty_bps(source_gap_count: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(
        "source_gap_penalty_bps",
        source_gap_count * SOURCE_GAP_PENALTY_BPS,
    )


def _missing_bear_case_evidence_count(
    bear_case_evidence_count: Decimal,
    minimum_bear_case_evidence_count: Decimal,
) -> Decimal:
    return _normalize_nonnegative_count(
        "missing_bear_case_evidence_count",
        max(minimum_bear_case_evidence_count - bear_case_evidence_count, ZERO),
    )


def _missing_bear_case_evidence_penalty_bps(
    missing_bear_case_evidence_count: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "missing_bear_case_evidence_penalty_bps",
        missing_bear_case_evidence_count * MISSING_BEAR_CASE_EVIDENCE_PENALTY_BPS,
    )


def _source_diversity_boost_bps(
    independent_source_count: Decimal,
    conflicting_source_count: Decimal,
    minimum_source_diversity_count: Decimal,
) -> Decimal:
    if independent_source_count < minimum_source_diversity_count:
        return ZERO
    return _normalize_nonnegative_decimal(
        "source_diversity_boost_bps",
        independent_source_count * INDEPENDENT_SOURCE_DIVERSITY_BPS
        + conflicting_source_count * CONFLICTING_SOURCE_DIVERSITY_BPS,
    )


def _raw_counterfactual_source_score_bps(counterfactual_source_count: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(
        "raw_counterfactual_source_score_bps",
        counterfactual_source_count * SOURCE_EVIDENCE_BPS,
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
    source_gap_count: Decimal,
    missing_bear_case_evidence_count: Decimal,
    source_diversity_boost_bps: Decimal,
    paper_score_bps: Decimal,
    minimum_actionable_score: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "research_packet_counterfactual_source_gap_score_v2",
        f"score_{score_status}",
    ]
    if source_gap_count > ZERO:
        additions.append("counterfactual_source_gap_detected")
    if missing_bear_case_evidence_count > ZERO:
        additions.append("missing_bear_case_evidence_penalty_applied")
    if source_diversity_boost_bps > ZERO:
        additions.append("source_diversity_boost_applied")
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


def _validate_result_consistency(
    result: ResearchPacketCounterfactualSourceGapScoreV2Result,
) -> None:
    if result.source_gap_count != _source_gap_count(
        result.base_case_source_count,
        result.counterfactual_source_count,
    ):
        raise ValueError("source_gap_count must match source counts")
    if result.counterfactual_source_coverage_ratio != (
        _counterfactual_source_coverage_ratio(
            result.base_case_source_count,
            result.counterfactual_source_count,
        )
    ):
        raise ValueError("counterfactual_source_coverage_ratio must match source counts")
    if result.source_gap_penalty_bps != _source_gap_penalty_bps(
        result.source_gap_count,
    ):
        raise ValueError("source_gap_penalty_bps must match source gap")
    if result.missing_bear_case_evidence_count != (
        _missing_bear_case_evidence_count(
            result.bear_case_evidence_count,
            result.minimum_bear_case_evidence_count,
        )
    ):
        raise ValueError("missing_bear_case_evidence_count must match bear-case counts")
    if result.missing_bear_case_evidence_penalty_bps != (
        _missing_bear_case_evidence_penalty_bps(
            result.missing_bear_case_evidence_count,
        )
    ):
        raise ValueError("missing_bear_case_evidence_penalty_bps must match shortfall")
    if result.source_diversity_boost_bps != _source_diversity_boost_bps(
        result.independent_source_count,
        result.conflicting_source_count,
        result.minimum_source_diversity_count,
    ):
        raise ValueError("source_diversity_boost_bps must match source mix")
    if result.raw_counterfactual_source_score_bps != (
        _raw_counterfactual_source_score_bps(result.counterfactual_source_count)
    ):
        raise ValueError("raw_counterfactual_source_score_bps must match sources")
    if result.paper_score_bps != _normalize_decimal(
        "paper_score_bps",
        result.raw_counterfactual_source_score_bps
        - result.source_gap_penalty_bps
        - result.missing_bear_case_evidence_penalty_bps
        + result.source_diversity_boost_bps,
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
    result: ResearchPacketCounterfactualSourceGapScoreV2Result,
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
    "ResearchPacketCounterfactualSourceGapScoreV2Input",
    "ResearchPacketCounterfactualSourceGapScoreV2Result",
    "estimate_research_packet_counterfactual_source_gap_score_v2",
    "research_packet_counterfactual_source_gap_score_v2_payload",
    "reject_research_packet_counterfactual_source_gap_score_v2_unsafe_payload",
)
