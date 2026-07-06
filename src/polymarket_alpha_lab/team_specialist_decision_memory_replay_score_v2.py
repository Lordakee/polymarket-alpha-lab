"""Pure Phase 1 decision memory replay report score v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
FIFTY = Decimal("50.000000")
HUNDRED = Decimal("100.000000")
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
    "specialist_id",
    "memory_id",
    "decision_memory_count",
    "replayed_decision_count",
    "matching_replay_count",
    "stale_replay_count",
    "recent_learning_count",
    "replay_coverage_ratio",
    "replay_match_ratio",
    "stale_replay_ratio",
    "recent_learning_ratio",
    "raw_memory_replay_score_bps",
    "stale_replay_penalty_bps",
    "recent_learning_boost_bps",
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
class TeamSpecialistDecisionMemoryReplayScoreV2Input:
    specialist_id: str
    memory_id: str
    decision_memory_count: Decimal
    replayed_decision_count: Decimal
    matching_replay_count: Decimal
    stale_replay_count: Decimal
    recent_learning_count: Decimal
    minimum_actionable_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("specialist_id", self.specialist_id)
        _require_canonical_string("memory_id", self.memory_id)
        for field_name in (
            "decision_memory_count",
            "replayed_decision_count",
            "matching_replay_count",
            "stale_replay_count",
            "recent_learning_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
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
        _validate_count_consistency(self)
        reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload(
            "decision memory replay score input",
            self,
        )
        _require_paper_flags("decision memory replay score input", self)


@dataclass(frozen=True)
class TeamSpecialistDecisionMemoryReplayScoreV2Result:
    specialist_id: str
    memory_id: str
    decision_memory_count: Decimal
    replayed_decision_count: Decimal
    matching_replay_count: Decimal
    stale_replay_count: Decimal
    recent_learning_count: Decimal
    replay_coverage_ratio: Decimal
    replay_match_ratio: Decimal
    stale_replay_ratio: Decimal
    recent_learning_ratio: Decimal
    raw_memory_replay_score_bps: Decimal
    stale_replay_penalty_bps: Decimal
    recent_learning_boost_bps: Decimal
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
        _require_canonical_string("specialist_id", self.specialist_id)
        _require_canonical_string("memory_id", self.memory_id)
        for field_name in (
            "decision_memory_count",
            "replayed_decision_count",
            "matching_replay_count",
            "stale_replay_count",
            "recent_learning_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "replay_coverage_ratio",
            "replay_match_ratio",
            "stale_replay_ratio",
            "recent_learning_ratio",
            "raw_memory_replay_score_bps",
            "stale_replay_penalty_bps",
            "recent_learning_boost_bps",
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
        reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload(
            "decision memory replay score result",
            self,
        )
        _require_paper_flags("decision memory replay score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_decision_memory_replay_score_v2_payload(self)


def estimate_team_specialist_decision_memory_replay_score_v2(
    score_input: TeamSpecialistDecisionMemoryReplayScoreV2Input,
) -> TeamSpecialistDecisionMemoryReplayScoreV2Result:
    if type(score_input) is not TeamSpecialistDecisionMemoryReplayScoreV2Input:
        raise ValueError(
            "score_input must be a TeamSpecialistDecisionMemoryReplayScoreV2Input",
        )
    reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload(
        "decision memory replay score input",
        score_input,
    )
    _require_paper_flags("decision memory replay score input", score_input)

    replay_coverage_ratio = _safe_ratio(
        score_input.replayed_decision_count,
        score_input.decision_memory_count,
    )
    replay_match_ratio = _safe_ratio(
        score_input.matching_replay_count,
        score_input.replayed_decision_count,
    )
    stale_replay_ratio = _safe_ratio(
        score_input.stale_replay_count,
        score_input.replayed_decision_count,
    )
    recent_learning_ratio = _safe_ratio(
        score_input.recent_learning_count,
        score_input.decision_memory_count,
    )
    raw_memory_replay_score_bps = _normalize_nonnegative_decimal(
        "raw_memory_replay_score_bps",
        replay_coverage_ratio * HUNDRED + replay_match_ratio * HUNDRED,
    )
    stale_replay_penalty_bps = _normalize_nonnegative_decimal(
        "stale_replay_penalty_bps",
        stale_replay_ratio * HUNDRED,
    )
    recent_learning_boost_bps = _normalize_nonnegative_decimal(
        "recent_learning_boost_bps",
        recent_learning_ratio * FIFTY,
    )
    paper_score_bps = _normalize_decimal(
        "paper_score_bps",
        raw_memory_replay_score_bps
        - stale_replay_penalty_bps
        + recent_learning_boost_bps,
    )
    score_status = _score_status(
        paper_score_bps,
        score_input.minimum_actionable_score,
    )

    return TeamSpecialistDecisionMemoryReplayScoreV2Result(
        specialist_id=score_input.specialist_id,
        memory_id=score_input.memory_id,
        decision_memory_count=score_input.decision_memory_count,
        replayed_decision_count=score_input.replayed_decision_count,
        matching_replay_count=score_input.matching_replay_count,
        stale_replay_count=score_input.stale_replay_count,
        recent_learning_count=score_input.recent_learning_count,
        replay_coverage_ratio=replay_coverage_ratio,
        replay_match_ratio=replay_match_ratio,
        stale_replay_ratio=stale_replay_ratio,
        recent_learning_ratio=recent_learning_ratio,
        raw_memory_replay_score_bps=raw_memory_replay_score_bps,
        stale_replay_penalty_bps=stale_replay_penalty_bps,
        recent_learning_boost_bps=recent_learning_boost_bps,
        paper_score_bps=paper_score_bps,
        minimum_actionable_score=score_input.minimum_actionable_score,
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            replay_coverage_ratio=replay_coverage_ratio,
            stale_replay_penalty_bps=stale_replay_penalty_bps,
            recent_learning_boost_bps=recent_learning_boost_bps,
            paper_score_bps=paper_score_bps,
            minimum_actionable_score=score_input.minimum_actionable_score,
            score_status=score_status,
        ),
    )


def team_specialist_decision_memory_replay_score_v2_payload(
    result: TeamSpecialistDecisionMemoryReplayScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not TeamSpecialistDecisionMemoryReplayScoreV2Result:
        raise ValueError(
            "result must be a TeamSpecialistDecisionMemoryReplayScoreV2Result",
        )
    _require_paper_flags("decision memory replay score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload(
        "decision memory replay score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("ratio", numerator / denominator)


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
    replay_coverage_ratio: Decimal,
    stale_replay_penalty_bps: Decimal,
    recent_learning_boost_bps: Decimal,
    paper_score_bps: Decimal,
    minimum_actionable_score: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "team_specialist_decision_memory_replay_score_v2",
        f"score_{score_status}",
    ]
    if replay_coverage_ratio > ZERO:
        additions.append("replay_coverage_present")
    if stale_replay_penalty_bps > ZERO:
        additions.append("stale_replay_penalty_applied")
    if recent_learning_boost_bps > ZERO:
        additions.append("recent_learning_boost_applied")
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


def _validate_count_consistency(value: object) -> None:
    decision_memory_count = getattr(value, "decision_memory_count")
    replayed_decision_count = getattr(value, "replayed_decision_count")
    matching_replay_count = getattr(value, "matching_replay_count")
    stale_replay_count = getattr(value, "stale_replay_count")
    recent_learning_count = getattr(value, "recent_learning_count")
    if replayed_decision_count > decision_memory_count:
        raise ValueError("replayed_decision_count must not exceed decision_memory_count")
    if matching_replay_count > replayed_decision_count:
        raise ValueError("matching_replay_count must not exceed replayed_decision_count")
    if stale_replay_count > replayed_decision_count:
        raise ValueError("stale_replay_count must not exceed replayed_decision_count")
    if recent_learning_count > decision_memory_count:
        raise ValueError("recent_learning_count must not exceed decision_memory_count")


def _validate_result_consistency(
    result: TeamSpecialistDecisionMemoryReplayScoreV2Result,
) -> None:
    _validate_count_consistency(result)
    if result.replay_coverage_ratio != _safe_ratio(
        result.replayed_decision_count,
        result.decision_memory_count,
    ):
        raise ValueError("replay_coverage_ratio must match counts")
    if result.replay_match_ratio != _safe_ratio(
        result.matching_replay_count,
        result.replayed_decision_count,
    ):
        raise ValueError("replay_match_ratio must match counts")
    if result.stale_replay_ratio != _safe_ratio(
        result.stale_replay_count,
        result.replayed_decision_count,
    ):
        raise ValueError("stale_replay_ratio must match counts")
    if result.recent_learning_ratio != _safe_ratio(
        result.recent_learning_count,
        result.decision_memory_count,
    ):
        raise ValueError("recent_learning_ratio must match counts")
    if result.raw_memory_replay_score_bps != _normalize_nonnegative_decimal(
        "raw_memory_replay_score_bps",
        result.replay_coverage_ratio * HUNDRED + result.replay_match_ratio * HUNDRED,
    ):
        raise ValueError("raw_memory_replay_score_bps must match ratios")
    if result.stale_replay_penalty_bps != _normalize_nonnegative_decimal(
        "stale_replay_penalty_bps",
        result.stale_replay_ratio * HUNDRED,
    ):
        raise ValueError("stale_replay_penalty_bps must match stale_replay_ratio")
    if result.recent_learning_boost_bps != _normalize_nonnegative_decimal(
        "recent_learning_boost_bps",
        result.recent_learning_ratio * FIFTY,
    ):
        raise ValueError("recent_learning_boost_bps must match recent_learning_ratio")
    if result.paper_score_bps != _normalize_decimal(
        "paper_score_bps",
        result.raw_memory_replay_score_bps
        - result.stale_replay_penalty_bps
        + result.recent_learning_boost_bps,
    ):
        raise ValueError("paper_score_bps must match score parts")
    if result.score_status != _score_status(
        result.paper_score_bps,
        result.minimum_actionable_score,
    ):
        raise ValueError("score_status must match paper_score_bps")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _derived_validation_digest(
    result: TeamSpecialistDecisionMemoryReplayScoreV2Result,
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


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


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
    "TeamSpecialistDecisionMemoryReplayScoreV2Input",
    "TeamSpecialistDecisionMemoryReplayScoreV2Result",
    "estimate_team_specialist_decision_memory_replay_score_v2",
    "team_specialist_decision_memory_replay_score_v2_payload",
    "reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload",
)
