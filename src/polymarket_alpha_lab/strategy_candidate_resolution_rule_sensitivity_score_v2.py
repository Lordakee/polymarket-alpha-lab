"""Pure paper/report candidate resolution-rule sensitivity score v2."""

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
RULE_SPECIFICITY_WEIGHT_BPS = Decimal("300.000000")
OFFICIAL_SOURCE_HIERARCHY_WEIGHT_BPS = Decimal("200.000000")
SETTLEMENT_AMBIGUITY_WEIGHT_BPS = Decimal("250.000000")
DEADLINE_PROXIMITY_WEIGHT_BPS = Decimal("150.000000")
DISPUTE_HISTORY_WEIGHT_BPS = Decimal("100.000000")
SCORE_STATUSES = ("candidate", "watch", "blocked")
SCORE_DECISIONS = ("paper_candidate", "manual_review", "reject")
SENSITIVITY_RANKS = ("low", "moderate", "high")
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
    "rule_specificity_ratio",
    "official_source_hierarchy_ratio",
    "settlement_ambiguity_ratio",
    "seconds_until_resolution_deadline",
    "deadline_proximity_window_seconds",
    "prior_dispute_count",
    "historical_resolution_count",
    "rule_specificity_penalty_bps",
    "official_source_hierarchy_penalty_bps",
    "settlement_ambiguity_penalty_bps",
    "deadline_proximity_ratio",
    "deadline_proximity_penalty_bps",
    "dispute_history_ratio",
    "dispute_history_penalty_bps",
    "paper_score_bps",
    "watch_sensitivity_bps",
    "block_sensitivity_bps",
    "sensitivity_rank",
    "score_status",
    "score_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyCandidateResolutionRuleSensitivityScoreV2Input:
    candidate_id: str
    rule_specificity_ratio: Decimal
    official_source_hierarchy_ratio: Decimal
    settlement_ambiguity_ratio: Decimal
    seconds_until_resolution_deadline: Decimal
    deadline_proximity_window_seconds: Decimal
    prior_dispute_count: Decimal
    historical_resolution_count: Decimal
    watch_sensitivity_bps: Decimal
    block_sensitivity_bps: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        for field_name in (
            "rule_specificity_ratio",
            "official_source_hierarchy_ratio",
            "settlement_ambiguity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "seconds_until_resolution_deadline",
            "deadline_proximity_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        if self.deadline_proximity_window_seconds <= ZERO:
            raise ValueError("deadline_proximity_window_seconds must be positive")
        object.__setattr__(
            self,
            "prior_dispute_count",
            _normalize_nonnegative_count(
                "prior_dispute_count",
                self.prior_dispute_count,
            ),
        )
        object.__setattr__(
            self,
            "historical_resolution_count",
            _normalize_positive_count(
                "historical_resolution_count",
                self.historical_resolution_count,
            ),
        )
        _validate_dispute_counts(
            self.prior_dispute_count,
            self.historical_resolution_count,
        )
        for field_name in ("watch_sensitivity_bps", "block_sensitivity_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_thresholds(self.watch_sensitivity_bps, self.block_sensitivity_bps)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload(
            "candidate resolution rule sensitivity score input",
            self,
        )
        _require_paper_flags("candidate resolution rule sensitivity score input", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionRuleSensitivityScoreV2Result:
    candidate_id: str
    rule_specificity_ratio: Decimal
    official_source_hierarchy_ratio: Decimal
    settlement_ambiguity_ratio: Decimal
    seconds_until_resolution_deadline: Decimal
    deadline_proximity_window_seconds: Decimal
    prior_dispute_count: Decimal
    historical_resolution_count: Decimal
    rule_specificity_penalty_bps: Decimal
    official_source_hierarchy_penalty_bps: Decimal
    settlement_ambiguity_penalty_bps: Decimal
    deadline_proximity_ratio: Decimal
    deadline_proximity_penalty_bps: Decimal
    dispute_history_ratio: Decimal
    dispute_history_penalty_bps: Decimal
    paper_score_bps: Decimal
    watch_sensitivity_bps: Decimal
    block_sensitivity_bps: Decimal
    sensitivity_rank: str
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
            "rule_specificity_ratio",
            "official_source_hierarchy_ratio",
            "settlement_ambiguity_ratio",
            "deadline_proximity_ratio",
            "dispute_history_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "seconds_until_resolution_deadline",
            "deadline_proximity_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        if self.deadline_proximity_window_seconds <= ZERO:
            raise ValueError("deadline_proximity_window_seconds must be positive")
        object.__setattr__(
            self,
            "prior_dispute_count",
            _normalize_nonnegative_count(
                "prior_dispute_count",
                self.prior_dispute_count,
            ),
        )
        object.__setattr__(
            self,
            "historical_resolution_count",
            _normalize_positive_count(
                "historical_resolution_count",
                self.historical_resolution_count,
            ),
        )
        _validate_dispute_counts(
            self.prior_dispute_count,
            self.historical_resolution_count,
        )
        for field_name in (
            "rule_specificity_penalty_bps",
            "official_source_hierarchy_penalty_bps",
            "settlement_ambiguity_penalty_bps",
            "deadline_proximity_penalty_bps",
            "dispute_history_penalty_bps",
            "paper_score_bps",
            "watch_sensitivity_bps",
            "block_sensitivity_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_thresholds(self.watch_sensitivity_bps, self.block_sensitivity_bps)
        _require_choice("sensitivity_rank", self.sensitivity_rank, SENSITIVITY_RANKS)
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        _require_choice("score_decision", self.score_decision, SCORE_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload(
            "candidate resolution rule sensitivity score result",
            self,
        )
        _require_paper_flags("candidate resolution rule sensitivity score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_resolution_rule_sensitivity_score_v2_payload(self)


def estimate_strategy_candidate_resolution_rule_sensitivity_score_v2(
    score_input: StrategyCandidateResolutionRuleSensitivityScoreV2Input,
) -> StrategyCandidateResolutionRuleSensitivityScoreV2Result:
    if type(score_input) is not StrategyCandidateResolutionRuleSensitivityScoreV2Input:
        raise ValueError(
            "score_input must be a StrategyCandidateResolutionRuleSensitivityScoreV2Input",
        )
    reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload(
        "candidate resolution rule sensitivity score input",
        score_input,
    )
    _require_paper_flags("candidate resolution rule sensitivity score input", score_input)

    rule_specificity_penalty_bps = _inverse_ratio_penalty_bps(
        "rule_specificity_penalty_bps",
        score_input.rule_specificity_ratio,
        RULE_SPECIFICITY_WEIGHT_BPS,
    )
    official_source_hierarchy_penalty_bps = _inverse_ratio_penalty_bps(
        "official_source_hierarchy_penalty_bps",
        score_input.official_source_hierarchy_ratio,
        OFFICIAL_SOURCE_HIERARCHY_WEIGHT_BPS,
    )
    settlement_ambiguity_penalty_bps = _ratio_penalty_bps(
        "settlement_ambiguity_penalty_bps",
        score_input.settlement_ambiguity_ratio,
        SETTLEMENT_AMBIGUITY_WEIGHT_BPS,
    )
    deadline_proximity_ratio = _deadline_proximity_ratio(
        score_input.seconds_until_resolution_deadline,
        score_input.deadline_proximity_window_seconds,
    )
    deadline_proximity_penalty_bps = _ratio_penalty_bps(
        "deadline_proximity_penalty_bps",
        deadline_proximity_ratio,
        DEADLINE_PROXIMITY_WEIGHT_BPS,
    )
    dispute_history_ratio = _dispute_history_ratio(
        score_input.prior_dispute_count,
        score_input.historical_resolution_count,
    )
    dispute_history_penalty_bps = _ratio_penalty_bps(
        "dispute_history_penalty_bps",
        dispute_history_ratio,
        DISPUTE_HISTORY_WEIGHT_BPS,
    )
    paper_score_bps = _normalize_nonnegative_decimal(
        "paper_score_bps",
        rule_specificity_penalty_bps
        + official_source_hierarchy_penalty_bps
        + settlement_ambiguity_penalty_bps
        + deadline_proximity_penalty_bps
        + dispute_history_penalty_bps,
    )
    score_status = _score_status(
        paper_score_bps,
        score_input.watch_sensitivity_bps,
        score_input.block_sensitivity_bps,
    )

    return StrategyCandidateResolutionRuleSensitivityScoreV2Result(
        candidate_id=score_input.candidate_id,
        rule_specificity_ratio=score_input.rule_specificity_ratio,
        official_source_hierarchy_ratio=score_input.official_source_hierarchy_ratio,
        settlement_ambiguity_ratio=score_input.settlement_ambiguity_ratio,
        seconds_until_resolution_deadline=score_input.seconds_until_resolution_deadline,
        deadline_proximity_window_seconds=score_input.deadline_proximity_window_seconds,
        prior_dispute_count=score_input.prior_dispute_count,
        historical_resolution_count=score_input.historical_resolution_count,
        rule_specificity_penalty_bps=rule_specificity_penalty_bps,
        official_source_hierarchy_penalty_bps=official_source_hierarchy_penalty_bps,
        settlement_ambiguity_penalty_bps=settlement_ambiguity_penalty_bps,
        deadline_proximity_ratio=deadline_proximity_ratio,
        deadline_proximity_penalty_bps=deadline_proximity_penalty_bps,
        dispute_history_ratio=dispute_history_ratio,
        dispute_history_penalty_bps=dispute_history_penalty_bps,
        paper_score_bps=paper_score_bps,
        watch_sensitivity_bps=score_input.watch_sensitivity_bps,
        block_sensitivity_bps=score_input.block_sensitivity_bps,
        sensitivity_rank=_sensitivity_rank(
            paper_score_bps,
            score_input.watch_sensitivity_bps,
            score_input.block_sensitivity_bps,
        ),
        score_status=score_status,
        score_decision=_score_decision(score_status),
        reason_codes=_reason_codes(
            score_input.reason_codes,
            rule_specificity_penalty_bps=rule_specificity_penalty_bps,
            official_source_hierarchy_penalty_bps=official_source_hierarchy_penalty_bps,
            settlement_ambiguity_penalty_bps=settlement_ambiguity_penalty_bps,
            deadline_proximity_penalty_bps=deadline_proximity_penalty_bps,
            dispute_history_penalty_bps=dispute_history_penalty_bps,
            sensitivity_rank=_sensitivity_rank(
                paper_score_bps,
                score_input.watch_sensitivity_bps,
                score_input.block_sensitivity_bps,
            ),
            score_status=score_status,
        ),
    )


def strategy_candidate_resolution_rule_sensitivity_score_v2_payload(
    result: StrategyCandidateResolutionRuleSensitivityScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateResolutionRuleSensitivityScoreV2Result:
        raise ValueError(
            "result must be a StrategyCandidateResolutionRuleSensitivityScoreV2Result",
        )
    _require_paper_flags("candidate resolution rule sensitivity score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload(
        "candidate resolution rule sensitivity score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _inverse_ratio_penalty_bps(
    field_name: str,
    ratio: Decimal,
    weight_bps: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, (ONE - ratio) * weight_bps)


def _ratio_penalty_bps(
    field_name: str,
    ratio: Decimal,
    weight_bps: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, ratio * weight_bps)


def _deadline_proximity_ratio(
    seconds_until_resolution_deadline: Decimal,
    deadline_proximity_window_seconds: Decimal,
) -> Decimal:
    if seconds_until_resolution_deadline >= deadline_proximity_window_seconds:
        return ZERO
    return _normalize_ratio(
        "deadline_proximity_ratio",
        (deadline_proximity_window_seconds - seconds_until_resolution_deadline)
        / deadline_proximity_window_seconds,
    )


def _dispute_history_ratio(
    prior_dispute_count: Decimal,
    historical_resolution_count: Decimal,
) -> Decimal:
    return _normalize_ratio(
        "dispute_history_ratio",
        prior_dispute_count / historical_resolution_count,
    )


def _score_status(
    paper_score_bps: Decimal,
    watch_sensitivity_bps: Decimal,
    block_sensitivity_bps: Decimal,
) -> str:
    if paper_score_bps >= block_sensitivity_bps:
        return "blocked"
    if paper_score_bps >= watch_sensitivity_bps:
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


def _sensitivity_rank(
    paper_score_bps: Decimal,
    watch_sensitivity_bps: Decimal,
    block_sensitivity_bps: Decimal,
) -> str:
    if paper_score_bps >= block_sensitivity_bps:
        return "high"
    if paper_score_bps >= watch_sensitivity_bps:
        return "moderate"
    return "low"


def _reason_codes(
    existing: tuple[str, ...],
    *,
    rule_specificity_penalty_bps: Decimal,
    official_source_hierarchy_penalty_bps: Decimal,
    settlement_ambiguity_penalty_bps: Decimal,
    deadline_proximity_penalty_bps: Decimal,
    dispute_history_penalty_bps: Decimal,
    sensitivity_rank: str,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_resolution_rule_sensitivity_score_v2",
        f"score_{score_status}",
        f"sensitivity_{sensitivity_rank}",
        _penalty_reason_code(
            rule_specificity_penalty_bps,
            "rule_specificity_penalty_applied",
            "rule_specificity_clear",
        ),
        _penalty_reason_code(
            official_source_hierarchy_penalty_bps,
            "official_source_hierarchy_penalty_applied",
            "official_source_hierarchy_clear",
        ),
        _penalty_reason_code(
            settlement_ambiguity_penalty_bps,
            "settlement_ambiguity_penalty_applied",
            "settlement_ambiguity_clear",
        ),
        _penalty_reason_code(
            deadline_proximity_penalty_bps,
            "deadline_proximity_penalty_applied",
            "deadline_not_near",
        ),
        _penalty_reason_code(
            dispute_history_penalty_bps,
            "dispute_history_penalty_applied",
            "no_dispute_history",
        ),
        _threshold_reason_code(score_status),
    ]
    return _append_reason_codes(existing, tuple(additions))


def _penalty_reason_code(
    penalty_bps: Decimal,
    applied_reason_code: str,
    clear_reason_code: str,
) -> str:
    if penalty_bps > ZERO:
        return applied_reason_code
    return clear_reason_code


def _threshold_reason_code(score_status: str) -> str:
    if score_status == "blocked":
        return "sensitivity_exceeds_block_threshold"
    if score_status == "watch":
        return "sensitivity_requires_manual_review"
    if score_status == "candidate":
        return "sensitivity_below_watch_threshold"
    raise ValueError("score_status must be supported")


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_dispute_counts(
    prior_dispute_count: Decimal,
    historical_resolution_count: Decimal,
) -> None:
    if prior_dispute_count > historical_resolution_count:
        raise ValueError("prior_dispute_count must not exceed historical_resolution_count")


def _validate_thresholds(
    watch_sensitivity_bps: Decimal,
    block_sensitivity_bps: Decimal,
) -> None:
    if block_sensitivity_bps < watch_sensitivity_bps:
        raise ValueError("block_sensitivity_bps must be at least watch_sensitivity_bps")


def _validate_result_consistency(
    result: StrategyCandidateResolutionRuleSensitivityScoreV2Result,
) -> None:
    if result.rule_specificity_penalty_bps != _inverse_ratio_penalty_bps(
        "rule_specificity_penalty_bps",
        result.rule_specificity_ratio,
        RULE_SPECIFICITY_WEIGHT_BPS,
    ):
        raise ValueError("rule_specificity_penalty_bps must match rule specificity")
    if result.official_source_hierarchy_penalty_bps != _inverse_ratio_penalty_bps(
        "official_source_hierarchy_penalty_bps",
        result.official_source_hierarchy_ratio,
        OFFICIAL_SOURCE_HIERARCHY_WEIGHT_BPS,
    ):
        raise ValueError(
            "official_source_hierarchy_penalty_bps must match source hierarchy",
        )
    if result.settlement_ambiguity_penalty_bps != _ratio_penalty_bps(
        "settlement_ambiguity_penalty_bps",
        result.settlement_ambiguity_ratio,
        SETTLEMENT_AMBIGUITY_WEIGHT_BPS,
    ):
        raise ValueError("settlement_ambiguity_penalty_bps must match ambiguity")
    if result.deadline_proximity_ratio != _deadline_proximity_ratio(
        result.seconds_until_resolution_deadline,
        result.deadline_proximity_window_seconds,
    ):
        raise ValueError("deadline_proximity_ratio must match deadline inputs")
    if result.deadline_proximity_penalty_bps != _ratio_penalty_bps(
        "deadline_proximity_penalty_bps",
        result.deadline_proximity_ratio,
        DEADLINE_PROXIMITY_WEIGHT_BPS,
    ):
        raise ValueError("deadline_proximity_penalty_bps must match deadline proximity")
    if result.dispute_history_ratio != _dispute_history_ratio(
        result.prior_dispute_count,
        result.historical_resolution_count,
    ):
        raise ValueError("dispute_history_ratio must match dispute counts")
    if result.dispute_history_penalty_bps != _ratio_penalty_bps(
        "dispute_history_penalty_bps",
        result.dispute_history_ratio,
        DISPUTE_HISTORY_WEIGHT_BPS,
    ):
        raise ValueError("dispute_history_penalty_bps must match dispute history")
    if result.paper_score_bps != _normalize_nonnegative_decimal(
        "paper_score_bps",
        result.rule_specificity_penalty_bps
        + result.official_source_hierarchy_penalty_bps
        + result.settlement_ambiguity_penalty_bps
        + result.deadline_proximity_penalty_bps
        + result.dispute_history_penalty_bps,
    ):
        raise ValueError("paper_score_bps must match sensitivity components")
    if result.sensitivity_rank != _sensitivity_rank(
        result.paper_score_bps,
        result.watch_sensitivity_bps,
        result.block_sensitivity_bps,
    ):
        raise ValueError("sensitivity_rank must match paper_score_bps")
    if result.score_status != _score_status(
        result.paper_score_bps,
        result.watch_sensitivity_bps,
        result.block_sensitivity_bps,
    ):
        raise ValueError("score_status must match paper_score_bps")
    if result.score_decision != _score_decision(result.score_status):
        raise ValueError("score_decision must match score_status")


def _derived_validation_digest(
    result: StrategyCandidateResolutionRuleSensitivityScoreV2Result,
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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between {ZERO} and {ONE}")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    "SENSITIVITY_RANKS",
    "StrategyCandidateResolutionRuleSensitivityScoreV2Input",
    "StrategyCandidateResolutionRuleSensitivityScoreV2Result",
    "estimate_strategy_candidate_resolution_rule_sensitivity_score_v2",
    "strategy_candidate_resolution_rule_sensitivity_score_v2_payload",
    "reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload",
)
