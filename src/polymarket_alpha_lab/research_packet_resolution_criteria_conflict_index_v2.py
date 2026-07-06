"""Pure paper/report resolution criteria conflict index v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
WORDING_CONFLICT_TERM_BPS = Decimal("40.000000")
OFFICIAL_SOURCE_GAP_PENALTY_BPS = Decimal("125.000000")
OBSERVED_CONFLICT_EVIDENCE_PENALTY_BPS = Decimal("90.000000")
OBSERVED_SUPPORT_EVIDENCE_CREDIT_BPS = Decimal("25.000000")
CONFLICT_STATUSES = ("clear", "watch", "blocked")
CONFLICT_DECISIONS = ("paper_clear", "manual_review", "reject")
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
    "market_slug",
    "market_question",
    "resolution_criteria",
    "official_source_count",
    "minimum_official_source_count",
    "observed_evidence_count",
    "conflicting_evidence_count",
    "watch_conflict_index_bps",
    "blocked_conflict_index_bps",
    "question_only_term_count",
    "criteria_only_term_count",
    "shared_resolution_term_count",
    "wording_conflict_term_count",
    "wording_conflict_bps",
    "official_source_gap_count",
    "official_source_gap_penalty_bps",
    "observed_support_evidence_count",
    "observed_conflict_evidence_penalty_bps",
    "observed_support_evidence_credit_bps",
    "raw_conflict_index_bps",
    "paper_conflict_index_bps",
    "conflict_status",
    "conflict_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchPacketResolutionCriteriaConflictIndexV2Input:
    packet_id: str
    market_slug: str
    market_question: str
    resolution_criteria: str
    official_source_count: Decimal
    minimum_official_source_count: Decimal
    observed_evidence_count: Decimal
    conflicting_evidence_count: Decimal
    watch_conflict_index_bps: Decimal
    blocked_conflict_index_bps: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_nonblank_text("market_question", self.market_question)
        _require_nonblank_text("resolution_criteria", self.resolution_criteria)
        for field_name in (
            "official_source_count",
            "minimum_official_source_count",
            "observed_evidence_count",
            "conflicting_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_index_bps",
            "blocked_conflict_index_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_evidence_count > self.observed_evidence_count:
            raise ValueError(
                "conflicting_evidence_count cannot exceed observed evidence count",
            )
        if self.blocked_conflict_index_bps < self.watch_conflict_index_bps:
            raise ValueError(
                "blocked_conflict_index_bps must be at least watch threshold",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload(
            "resolution criteria conflict input",
            self,
        )
        _require_paper_flags("resolution criteria conflict input", self)


@dataclass(frozen=True)
class ResearchPacketResolutionCriteriaConflictIndexV2Result:
    packet_id: str
    market_slug: str
    market_question: str
    resolution_criteria: str
    official_source_count: Decimal
    minimum_official_source_count: Decimal
    observed_evidence_count: Decimal
    conflicting_evidence_count: Decimal
    watch_conflict_index_bps: Decimal
    blocked_conflict_index_bps: Decimal
    question_only_term_count: Decimal
    criteria_only_term_count: Decimal
    shared_resolution_term_count: Decimal
    wording_conflict_term_count: Decimal
    wording_conflict_bps: Decimal
    official_source_gap_count: Decimal
    official_source_gap_penalty_bps: Decimal
    observed_support_evidence_count: Decimal
    observed_conflict_evidence_penalty_bps: Decimal
    observed_support_evidence_credit_bps: Decimal
    raw_conflict_index_bps: Decimal
    paper_conflict_index_bps: Decimal
    conflict_status: str
    conflict_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_nonblank_text("market_question", self.market_question)
        _require_nonblank_text("resolution_criteria", self.resolution_criteria)
        for field_name in (
            "official_source_count",
            "minimum_official_source_count",
            "observed_evidence_count",
            "conflicting_evidence_count",
            "question_only_term_count",
            "criteria_only_term_count",
            "shared_resolution_term_count",
            "wording_conflict_term_count",
            "official_source_gap_count",
            "observed_support_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_index_bps",
            "blocked_conflict_index_bps",
            "wording_conflict_bps",
            "official_source_gap_penalty_bps",
            "observed_conflict_evidence_penalty_bps",
            "observed_support_evidence_credit_bps",
            "raw_conflict_index_bps",
            "paper_conflict_index_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("conflict_status", self.conflict_status, CONFLICT_STATUSES)
        _require_choice("conflict_decision", self.conflict_decision, CONFLICT_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload(
            "resolution criteria conflict result",
            self,
        )
        _require_paper_flags("resolution criteria conflict result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_resolution_criteria_conflict_index_v2_payload(self)


def estimate_research_packet_resolution_criteria_conflict_index_v2(
    score_input: ResearchPacketResolutionCriteriaConflictIndexV2Input,
) -> ResearchPacketResolutionCriteriaConflictIndexV2Result:
    if type(score_input) is not ResearchPacketResolutionCriteriaConflictIndexV2Input:
        raise ValueError(
            "score_input must be a ResearchPacketResolutionCriteriaConflictIndexV2Input",
        )
    reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload(
        "resolution criteria conflict input",
        score_input,
    )
    _require_paper_flags("resolution criteria conflict input", score_input)

    question_terms = _terms(score_input.market_question)
    criteria_terms = _terms(score_input.resolution_criteria)
    question_only_term_count = _count_terms(
        tuple(term for term in question_terms if term not in criteria_terms),
    )
    criteria_only_term_count = _count_terms(
        tuple(term for term in criteria_terms if term not in question_terms),
    )
    shared_resolution_term_count = _count_terms(
        tuple(term for term in question_terms if term in criteria_terms),
    )
    wording_conflict_term_count = _normalize_nonnegative_count(
        "wording_conflict_term_count",
        question_only_term_count + criteria_only_term_count,
    )
    wording_conflict_bps = _wording_conflict_bps(wording_conflict_term_count)
    official_source_gap_count = _official_source_gap_count(
        score_input.official_source_count,
        score_input.minimum_official_source_count,
    )
    official_source_gap_penalty_bps = _official_source_gap_penalty_bps(
        official_source_gap_count,
    )
    observed_support_evidence_count = _observed_support_evidence_count(
        score_input.observed_evidence_count,
        score_input.conflicting_evidence_count,
    )
    observed_conflict_evidence_penalty_bps = (
        _observed_conflict_evidence_penalty_bps(
            score_input.conflicting_evidence_count,
        )
    )
    observed_support_evidence_credit_bps = _observed_support_evidence_credit_bps(
        observed_support_evidence_count,
    )
    raw_conflict_index_bps = _normalize_nonnegative_decimal(
        "raw_conflict_index_bps",
        wording_conflict_bps
        + official_source_gap_penalty_bps
        + observed_conflict_evidence_penalty_bps,
    )
    paper_conflict_index_bps = _paper_conflict_index_bps(
        raw_conflict_index_bps,
        observed_support_evidence_credit_bps,
    )
    conflict_status = _conflict_status(
        paper_conflict_index_bps,
        score_input.watch_conflict_index_bps,
        score_input.blocked_conflict_index_bps,
    )

    return ResearchPacketResolutionCriteriaConflictIndexV2Result(
        packet_id=score_input.packet_id,
        market_slug=score_input.market_slug,
        market_question=score_input.market_question,
        resolution_criteria=score_input.resolution_criteria,
        official_source_count=score_input.official_source_count,
        minimum_official_source_count=score_input.minimum_official_source_count,
        observed_evidence_count=score_input.observed_evidence_count,
        conflicting_evidence_count=score_input.conflicting_evidence_count,
        watch_conflict_index_bps=score_input.watch_conflict_index_bps,
        blocked_conflict_index_bps=score_input.blocked_conflict_index_bps,
        question_only_term_count=question_only_term_count,
        criteria_only_term_count=criteria_only_term_count,
        shared_resolution_term_count=shared_resolution_term_count,
        wording_conflict_term_count=wording_conflict_term_count,
        wording_conflict_bps=wording_conflict_bps,
        official_source_gap_count=official_source_gap_count,
        official_source_gap_penalty_bps=official_source_gap_penalty_bps,
        observed_support_evidence_count=observed_support_evidence_count,
        observed_conflict_evidence_penalty_bps=observed_conflict_evidence_penalty_bps,
        observed_support_evidence_credit_bps=observed_support_evidence_credit_bps,
        raw_conflict_index_bps=raw_conflict_index_bps,
        paper_conflict_index_bps=paper_conflict_index_bps,
        conflict_status=conflict_status,
        conflict_decision=_conflict_decision(conflict_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            wording_conflict_term_count=wording_conflict_term_count,
            official_source_gap_count=official_source_gap_count,
            conflicting_evidence_count=score_input.conflicting_evidence_count,
            observed_support_evidence_credit_bps=observed_support_evidence_credit_bps,
            paper_conflict_index_bps=paper_conflict_index_bps,
            blocked_conflict_index_bps=score_input.blocked_conflict_index_bps,
            conflict_status=conflict_status,
        ),
    )


def research_packet_resolution_criteria_conflict_index_v2_payload(
    result: ResearchPacketResolutionCriteriaConflictIndexV2Result,
) -> dict[str, Any]:
    if type(result) is not ResearchPacketResolutionCriteriaConflictIndexV2Result:
        raise ValueError(
            "result must be a ResearchPacketResolutionCriteriaConflictIndexV2Result",
        )
    _require_paper_flags("resolution criteria conflict result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload(
        "resolution criteria conflict result",
        result,
    )
    return _json_ready(asdict(result))


def reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _terms(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current = ""
    for character in value.lower():
        if character.isalnum():
            current += character
        elif current:
            tokens.append(current)
            current = ""
    if current:
        tokens.append(current)
    unique_terms: list[str] = []
    for token in tokens:
        if token not in unique_terms:
            unique_terms.append(token)
    return tuple(unique_terms)


def _count_terms(value: tuple[str, ...]) -> Decimal:
    return Decimal(str(len(value))).quantize(COUNT_QUANTUM)


def _wording_conflict_bps(wording_conflict_term_count: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(
        "wording_conflict_bps",
        wording_conflict_term_count * WORDING_CONFLICT_TERM_BPS,
    )


def _official_source_gap_count(
    official_source_count: Decimal,
    minimum_official_source_count: Decimal,
) -> Decimal:
    return _normalize_nonnegative_count(
        "official_source_gap_count",
        max(minimum_official_source_count - official_source_count, ZERO),
    )


def _official_source_gap_penalty_bps(official_source_gap_count: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal(
        "official_source_gap_penalty_bps",
        official_source_gap_count * OFFICIAL_SOURCE_GAP_PENALTY_BPS,
    )


def _observed_support_evidence_count(
    observed_evidence_count: Decimal,
    conflicting_evidence_count: Decimal,
) -> Decimal:
    return _normalize_nonnegative_count(
        "observed_support_evidence_count",
        observed_evidence_count - conflicting_evidence_count,
    )


def _observed_conflict_evidence_penalty_bps(
    conflicting_evidence_count: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "observed_conflict_evidence_penalty_bps",
        conflicting_evidence_count * OBSERVED_CONFLICT_EVIDENCE_PENALTY_BPS,
    )


def _observed_support_evidence_credit_bps(
    observed_support_evidence_count: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "observed_support_evidence_credit_bps",
        observed_support_evidence_count * OBSERVED_SUPPORT_EVIDENCE_CREDIT_BPS,
    )


def _paper_conflict_index_bps(
    raw_conflict_index_bps: Decimal,
    observed_support_evidence_credit_bps: Decimal,
) -> Decimal:
    adjusted = raw_conflict_index_bps - observed_support_evidence_credit_bps
    if adjusted < ZERO:
        adjusted = ZERO
    return _normalize_nonnegative_decimal("paper_conflict_index_bps", adjusted)


def _conflict_status(
    paper_conflict_index_bps: Decimal,
    watch_conflict_index_bps: Decimal,
    blocked_conflict_index_bps: Decimal,
) -> str:
    if paper_conflict_index_bps >= blocked_conflict_index_bps:
        return "blocked"
    if paper_conflict_index_bps >= watch_conflict_index_bps:
        return "watch"
    return "clear"


def _conflict_decision(conflict_status: str) -> str:
    if conflict_status == "clear":
        return "paper_clear"
    if conflict_status == "watch":
        return "manual_review"
    if conflict_status == "blocked":
        return "reject"
    raise ValueError("conflict_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    wording_conflict_term_count: Decimal,
    official_source_gap_count: Decimal,
    conflicting_evidence_count: Decimal,
    observed_support_evidence_credit_bps: Decimal,
    paper_conflict_index_bps: Decimal,
    blocked_conflict_index_bps: Decimal,
    conflict_status: str,
) -> tuple[str, ...]:
    additions = [
        "research_packet_resolution_criteria_conflict_index_v2",
        f"conflict_status_{conflict_status}",
    ]
    if wording_conflict_term_count > ZERO:
        additions.append("wording_conflict_detected")
    if official_source_gap_count > ZERO:
        additions.append("official_source_gap_detected")
    if conflicting_evidence_count > ZERO:
        additions.append("observed_conflict_evidence_detected")
    if observed_support_evidence_credit_bps > ZERO:
        additions.append("observed_support_evidence_credit_applied")
    if paper_conflict_index_bps <= ZERO:
        additions.append("no_conflict_index_detected")
    elif paper_conflict_index_bps < blocked_conflict_index_bps:
        additions.append("conflict_index_positive_below_blocked")
    else:
        additions.append("conflict_index_blocked")
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
    result: ResearchPacketResolutionCriteriaConflictIndexV2Result,
) -> None:
    if result.conflicting_evidence_count > result.observed_evidence_count:
        raise ValueError("conflicting_evidence_count cannot exceed observed evidence count")
    if result.blocked_conflict_index_bps < result.watch_conflict_index_bps:
        raise ValueError("blocked_conflict_index_bps must be at least watch threshold")
    question_terms = _terms(result.market_question)
    criteria_terms = _terms(result.resolution_criteria)
    if result.question_only_term_count != _count_terms(
        tuple(term for term in question_terms if term not in criteria_terms),
    ):
        raise ValueError("question_only_term_count must match resolution text")
    if result.criteria_only_term_count != _count_terms(
        tuple(term for term in criteria_terms if term not in question_terms),
    ):
        raise ValueError("criteria_only_term_count must match resolution text")
    if result.shared_resolution_term_count != _count_terms(
        tuple(term for term in question_terms if term in criteria_terms),
    ):
        raise ValueError("shared_resolution_term_count must match resolution text")
    if result.wording_conflict_term_count != _normalize_nonnegative_count(
        "wording_conflict_term_count",
        result.question_only_term_count + result.criteria_only_term_count,
    ):
        raise ValueError("wording_conflict_term_count must match term counts")
    if result.wording_conflict_bps != _wording_conflict_bps(
        result.wording_conflict_term_count,
    ):
        raise ValueError("wording_conflict_bps must match wording conflict terms")
    if result.official_source_gap_count != _official_source_gap_count(
        result.official_source_count,
        result.minimum_official_source_count,
    ):
        raise ValueError("official_source_gap_count must match source counts")
    if result.official_source_gap_penalty_bps != _official_source_gap_penalty_bps(
        result.official_source_gap_count,
    ):
        raise ValueError("official_source_gap_penalty_bps must match source gap")
    if result.observed_support_evidence_count != _observed_support_evidence_count(
        result.observed_evidence_count,
        result.conflicting_evidence_count,
    ):
        raise ValueError("observed_support_evidence_count must match evidence counts")
    if result.observed_conflict_evidence_penalty_bps != (
        _observed_conflict_evidence_penalty_bps(result.conflicting_evidence_count)
    ):
        raise ValueError(
            "observed_conflict_evidence_penalty_bps must match conflict evidence",
        )
    if result.observed_support_evidence_credit_bps != (
        _observed_support_evidence_credit_bps(result.observed_support_evidence_count)
    ):
        raise ValueError(
            "observed_support_evidence_credit_bps must match support evidence",
        )
    if result.raw_conflict_index_bps != _normalize_nonnegative_decimal(
        "raw_conflict_index_bps",
        result.wording_conflict_bps
        + result.official_source_gap_penalty_bps
        + result.observed_conflict_evidence_penalty_bps,
    ):
        raise ValueError("raw_conflict_index_bps must match score components")
    if result.paper_conflict_index_bps != _paper_conflict_index_bps(
        result.raw_conflict_index_bps,
        result.observed_support_evidence_credit_bps,
    ):
        raise ValueError("paper_conflict_index_bps must match score components")
    if result.conflict_status != _conflict_status(
        result.paper_conflict_index_bps,
        result.watch_conflict_index_bps,
        result.blocked_conflict_index_bps,
    ):
        raise ValueError("conflict_status must match paper_conflict_index_bps")
    if result.conflict_decision != _conflict_decision(result.conflict_status):
        raise ValueError("conflict_decision must match conflict_status")


def _derived_validation_digest(
    result: ResearchPacketResolutionCriteriaConflictIndexV2Result,
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


def _require_nonblank_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonblank text")


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
    if type(value) is bool or type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    raise ValueError("value must be JSON-ready public data")


__all__ = (
    "CONFLICT_STATUSES",
    "CONFLICT_DECISIONS",
    "ResearchPacketResolutionCriteriaConflictIndexV2Input",
    "ResearchPacketResolutionCriteriaConflictIndexV2Result",
    "estimate_research_packet_resolution_criteria_conflict_index_v2",
    "research_packet_resolution_criteria_conflict_index_v2_payload",
    "reject_research_packet_resolution_criteria_conflict_index_v2_unsafe_payload",
)
