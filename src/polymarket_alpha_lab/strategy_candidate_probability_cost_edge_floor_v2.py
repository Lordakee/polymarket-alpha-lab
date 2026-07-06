"""Phase 1 paper scoring gate for probability cost edge floors.

The module is intentionally pure and in-memory: callers provide candidates and
receive immutable scores, reports, and JSON-ready payloads.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
DECISIONS = ("accepted", "rejected")
DECISION_PRIORITY = {"accepted": 0, "rejected": 1}
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "muta" "tion",
    "b" "uy",
    "se" "ll",
    "tr" "ade",
)


@dataclass(frozen=True)
class StrategyCandidateProbabilityCostEdgeFloorV2Config:
    config_version: str
    min_cost_adjusted_probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_cost_adjusted_probability_edge",
            _normalize_nonnegative_decimal(
                "min_cost_adjusted_probability_edge",
                self.min_cost_adjusted_probability_edge,
            ),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyCandidateProbabilityCostEdgeFloorV2Candidate:
    candidate_id: str
    market_slug: str
    side: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    fee_probability_floor: Decimal
    spread_probability_floor: Decimal
    settlement_probability_floor: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_floor",
            "spread_probability_floor",
            "settlement_probability_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyCandidateProbabilityCostEdgeFloorV2Score:
    candidate_id: str
    market_slug: str
    side: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    fee_probability_floor: Decimal
    spread_probability_floor: Decimal
    settlement_probability_floor: Decimal
    total_friction_probability_floor: Decimal
    min_cost_adjusted_probability_edge: Decimal
    required_probability_edge: Decimal
    cost_adjusted_probability_edge: Decimal
    edge_floor_surplus: Decimal
    age_seconds: Decimal
    decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        if self.side not in ("yes", "no"):
            raise ValueError("side must be yes or no")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_floor",
            "spread_probability_floor",
            "settlement_probability_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "cost_adjusted_probability_edge",
            "edge_floor_surplus",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_friction_probability_floor",
            "min_cost_adjusted_probability_edge",
            "required_probability_edge",
            "age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.decision not in DECISIONS:
            raise ValueError("decision must be accepted or rejected")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_score_consistency(self)


@dataclass(frozen=True)
class StrategyCandidateProbabilityCostEdgeFloorV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: int
    score_count: int
    accepted_count: int
    rejected_count: int
    first_observed_at: datetime | None
    latest_observed_at: datetime | None
    scores: tuple[StrategyCandidateProbabilityCostEdgeFloorV2Score, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "score_count",
            "accepted_count",
            "rejected_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_observed_at",
            _as_optional_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(self, "scores", _normalize_scores(self.scores))
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def score_strategy_candidate_probability_cost_edge_floor_v2(
    candidate: StrategyCandidateProbabilityCostEdgeFloorV2Candidate,
    *,
    config: StrategyCandidateProbabilityCostEdgeFloorV2Config,
    generated_at: datetime,
) -> StrategyCandidateProbabilityCostEdgeFloorV2Score:
    if type(candidate) is not StrategyCandidateProbabilityCostEdgeFloorV2Candidate:
        raise ValueError("candidate must be a StrategyCandidateProbabilityCostEdgeFloorV2Candidate")
    if type(config) is not StrategyCandidateProbabilityCostEdgeFloorV2Config:
        raise ValueError("config must be a StrategyCandidateProbabilityCostEdgeFloorV2Config")
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at = _as_utc("observed_at", candidate.observed_at)
    if observed_at > generated_at_utc:
        raise ValueError("observed_at must not be after generated_at")
    _require_safety_flags(candidate)
    _require_safety_flags(config)

    gross_probability_edge = _subtract_decimal(
        candidate.forecast_probability,
        candidate.market_probability,
    )
    total_friction_probability_floor = _sum_decimals(
        (
            candidate.fee_probability_floor,
            candidate.spread_probability_floor,
            candidate.settlement_probability_floor,
        ),
    )
    required_probability_edge = _add_decimal(
        total_friction_probability_floor,
        config.min_cost_adjusted_probability_edge,
    )
    cost_adjusted_probability_edge = _subtract_decimal(
        gross_probability_edge,
        total_friction_probability_floor,
    )
    edge_floor_surplus = _subtract_decimal(
        gross_probability_edge,
        required_probability_edge,
    )
    decision = "accepted" if edge_floor_surplus >= ZERO else "rejected"

    return StrategyCandidateProbabilityCostEdgeFloorV2Score(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        side=candidate.side,
        observed_at=observed_at,
        forecast_probability=candidate.forecast_probability,
        market_probability=candidate.market_probability,
        gross_probability_edge=gross_probability_edge,
        fee_probability_floor=candidate.fee_probability_floor,
        spread_probability_floor=candidate.spread_probability_floor,
        settlement_probability_floor=candidate.settlement_probability_floor,
        total_friction_probability_floor=total_friction_probability_floor,
        min_cost_adjusted_probability_edge=config.min_cost_adjusted_probability_edge,
        required_probability_edge=required_probability_edge,
        cost_adjusted_probability_edge=cost_adjusted_probability_edge,
        edge_floor_surplus=edge_floor_surplus,
        age_seconds=_seconds_between(generated_at_utc, observed_at),
        decision=decision,
        reason_codes=_reason_codes_for(
            source_reason_codes=candidate.reason_codes,
            gross_probability_edge=gross_probability_edge,
            fee_probability_floor=candidate.fee_probability_floor,
            spread_probability_floor=candidate.spread_probability_floor,
            settlement_probability_floor=candidate.settlement_probability_floor,
            cost_adjusted_probability_edge=cost_adjusted_probability_edge,
            min_cost_adjusted_probability_edge=config.min_cost_adjusted_probability_edge,
            decision=decision,
        ),
    )


def build_strategy_candidate_probability_cost_edge_floor_v2_report(
    candidates: Iterable[StrategyCandidateProbabilityCostEdgeFloorV2Candidate],
    *,
    config: StrategyCandidateProbabilityCostEdgeFloorV2Config,
    generated_at: datetime,
) -> StrategyCandidateProbabilityCostEdgeFloorV2Report:
    if type(config) is not StrategyCandidateProbabilityCostEdgeFloorV2Config:
        raise ValueError("config must be a StrategyCandidateProbabilityCostEdgeFloorV2Config")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_safety_flags(config)
    normalized_candidates = _normalize_candidates(candidates)
    scores = tuple(
        sorted(
            (
                score_strategy_candidate_probability_cost_edge_floor_v2(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_candidates
            ),
            key=_score_sort_key,
        ),
    )
    observed_times = tuple(score.observed_at for score in scores)
    return StrategyCandidateProbabilityCostEdgeFloorV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=len(normalized_candidates),
        score_count=len(scores),
        accepted_count=_decision_count(scores, "accepted"),
        rejected_count=_decision_count(scores, "rejected"),
        first_observed_at=min(observed_times) if observed_times else None,
        latest_observed_at=max(observed_times) if observed_times else None,
        scores=scores,
    )


def strategy_candidate_probability_cost_edge_floor_v2_payload(
    report: StrategyCandidateProbabilityCostEdgeFloorV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateProbabilityCostEdgeFloorV2Report:
        raise ValueError("report must be a StrategyCandidateProbabilityCostEdgeFloorV2Report")
    _require_safety_flags(report)
    _verify_report_integrity(report)
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload(payload)
    return payload


def _reason_codes_for(
    *,
    source_reason_codes: tuple[str, ...],
    gross_probability_edge: Decimal,
    fee_probability_floor: Decimal,
    spread_probability_floor: Decimal,
    settlement_probability_floor: Decimal,
    cost_adjusted_probability_edge: Decimal,
    min_cost_adjusted_probability_edge: Decimal,
    decision: str,
) -> tuple[str, ...]:
    remaining_after_fee = _subtract_decimal(gross_probability_edge, fee_probability_floor)
    remaining_after_spread = _subtract_decimal(remaining_after_fee, spread_probability_floor)
    codes = list(source_reason_codes)
    if gross_probability_edge < fee_probability_floor:
        codes.append("fee_floor_not_cleared")
    if remaining_after_fee < spread_probability_floor:
        codes.append("spread_floor_not_cleared")
    if remaining_after_spread < settlement_probability_floor:
        codes.append("settlement_floor_not_cleared")
    if cost_adjusted_probability_edge < min_cost_adjusted_probability_edge:
        codes.append("minimum_edge_buffer_not_cleared")
    if decision == "accepted":
        codes.append("probability_edge_floor_cleared")
    else:
        codes.append("probability_edge_floor_rejected")
    return _normalize_reason_codes(tuple(codes))


def _score_sort_key(
    score: StrategyCandidateProbabilityCostEdgeFloorV2Score,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        DECISION_PRIORITY[score.decision],
        -score.edge_floor_surplus,
        score.age_seconds,
        score.market_slug,
        score.candidate_id,
        score.side,
    )


def _decision_count(
    scores: tuple[StrategyCandidateProbabilityCostEdgeFloorV2Score, ...],
    decision: str,
) -> int:
    return sum(1 for score in scores if score.decision == decision)


def _normalize_candidates(
    candidates: Iterable[StrategyCandidateProbabilityCostEdgeFloorV2Candidate],
) -> tuple[StrategyCandidateProbabilityCostEdgeFloorV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError(
            "candidates must be an iterable of StrategyCandidateProbabilityCostEdgeFloorV2Candidate values",
        )
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError(
            "candidates must be an iterable of StrategyCandidateProbabilityCostEdgeFloorV2Candidate values",
        ) from exc
    for value in normalized:
        if type(value) is not StrategyCandidateProbabilityCostEdgeFloorV2Candidate:
            raise ValueError(
                "candidates must contain only StrategyCandidateProbabilityCostEdgeFloorV2Candidate values",
            )
        _require_safety_flags(value)
    return normalized


def _normalize_scores(
    scores: Iterable[StrategyCandidateProbabilityCostEdgeFloorV2Score],
) -> tuple[StrategyCandidateProbabilityCostEdgeFloorV2Score, ...]:
    if isinstance(scores, (str, bytes)):
        raise ValueError("scores must be an iterable")
    try:
        normalized = tuple(scores)
    except TypeError as exc:
        raise ValueError("scores must be an iterable") from exc
    for score in normalized:
        if type(score) is not StrategyCandidateProbabilityCostEdgeFloorV2Score:
            raise ValueError("scores must contain StrategyCandidateProbabilityCostEdgeFloorV2Score values")
        _require_safety_flags(score)
        _verify_digest(score)
    return normalized


def _validate_score_consistency(score: StrategyCandidateProbabilityCostEdgeFloorV2Score) -> None:
    expected_gross_probability_edge = _subtract_decimal(
        score.forecast_probability,
        score.market_probability,
    )
    if score.gross_probability_edge != expected_gross_probability_edge:
        raise ValueError("gross_probability_edge does not match probabilities")
    expected_total_friction_probability_floor = _sum_decimals(
        (
            score.fee_probability_floor,
            score.spread_probability_floor,
            score.settlement_probability_floor,
        ),
    )
    if score.total_friction_probability_floor != expected_total_friction_probability_floor:
        raise ValueError("total_friction_probability_floor does not match floors")
    expected_required_probability_edge = _add_decimal(
        score.total_friction_probability_floor,
        score.min_cost_adjusted_probability_edge,
    )
    if score.required_probability_edge != expected_required_probability_edge:
        raise ValueError("required_probability_edge does not match floors")
    expected_cost_adjusted_probability_edge = _subtract_decimal(
        score.gross_probability_edge,
        score.total_friction_probability_floor,
    )
    if score.cost_adjusted_probability_edge != expected_cost_adjusted_probability_edge:
        raise ValueError("cost_adjusted_probability_edge does not match edge and floors")
    expected_edge_floor_surplus = _subtract_decimal(
        score.gross_probability_edge,
        score.required_probability_edge,
    )
    if score.edge_floor_surplus != expected_edge_floor_surplus:
        raise ValueError("edge_floor_surplus does not match edge and required floor")
    expected_decision = "accepted" if score.edge_floor_surplus >= ZERO else "rejected"
    if score.decision != expected_decision:
        raise ValueError("decision does not match edge_floor_surplus")


def _validate_report_consistency(report: StrategyCandidateProbabilityCostEdgeFloorV2Report) -> None:
    if report.score_count != len(report.scores):
        raise ValueError("score_count must match scores")
    if report.candidate_count != len(report.scores):
        raise ValueError("candidate_count must match scores")
    if report.accepted_count != _decision_count(report.scores, "accepted"):
        raise ValueError("accepted_count must match scores")
    if report.rejected_count != _decision_count(report.scores, "rejected"):
        raise ValueError("rejected_count must match scores")
    if tuple(sorted(report.scores, key=_score_sort_key)) != report.scores:
        raise ValueError("scores must be sorted by decision and surplus")
    observed_times = tuple(score.observed_at for score in report.scores)
    expected_first = min(observed_times) if observed_times else None
    expected_latest = max(observed_times) if observed_times else None
    if report.first_observed_at != expected_first:
        raise ValueError("first_observed_at must match scores")
    if report.latest_observed_at != expected_latest:
        raise ValueError("latest_observed_at must match scores")
    for score in report.scores:
        _verify_digest(score)


def _verify_report_integrity(report: StrategyCandidateProbabilityCostEdgeFloorV2Report) -> None:
    _validate_report_consistency(report)
    _verify_digest(report)
    for score in report.scores:
        _verify_digest(score)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_public_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_canonical_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _apply_or_verify_digest(
    value: (
        StrategyCandidateProbabilityCostEdgeFloorV2Score
        | StrategyCandidateProbabilityCostEdgeFloorV2Report
    ),
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: (
        StrategyCandidateProbabilityCostEdgeFloorV2Score
        | StrategyCandidateProbabilityCostEdgeFloorV2Report
    ),
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: (
        StrategyCandidateProbabilityCostEdgeFloorV2Score
        | StrategyCandidateProbabilityCostEdgeFloorV2Report
    ),
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_canonical_public_string("public_payload_key", key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str) and _has_unsafe_public_fragment(value):
        raise ValueError("public payload contains unsafe public content")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "StrategyCandidateProbabilityCostEdgeFloorV2Candidate",
    "StrategyCandidateProbabilityCostEdgeFloorV2Config",
    "StrategyCandidateProbabilityCostEdgeFloorV2Report",
    "StrategyCandidateProbabilityCostEdgeFloorV2Score",
    "build_strategy_candidate_probability_cost_edge_floor_v2_report",
    "score_strategy_candidate_probability_cost_edge_floor_v2",
    "strategy_candidate_probability_cost_edge_floor_v2_payload",
)
