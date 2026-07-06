"""Readonly Decimal guard for Phase 1 probability-market selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_STRATEGY_PROBABILITY_MARKET_SELECTION_GUARD_V2_CONFIG_VERSION = (
    "strategy-probability-market-selection-guard-v2"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_SCORE_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_DECISION_STATUSES = ("pass", "blocked")
_DECISION_REASON_CODES = (
    "market_selection_guard_candidate_pass",
    "weak_research_readiness_block",
    "thin_cost_adjusted_edge_block",
    "high_resolution_ambiguity_block",
    "low_liquidity_exit_feasibility_block",
    "portfolio_concentration_block",
    "insufficient_specialist_quorum_block",
)
_REPORT_REASON_CODES = (
    "market_selection_guard_candidates_passed",
    "market_selection_guard_candidates_blocked",
    "market_selection_guard_no_candidates_block",
    "weak_research_readiness_block",
    "thin_cost_adjusted_edge_block",
    "high_resolution_ambiguity_block",
    "low_liquidity_exit_feasibility_block",
    "portfolio_concentration_block",
    "insufficient_specialist_quorum_block",
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_MARKET_SELECTION_GUARD_V2_CONFIG_VERSION",
    "StrategyProbabilityMarketSelectionGuardV2Config",
    "StrategyProbabilityMarketSelectionCandidate",
    "StrategyProbabilityMarketSelectionDecision",
    "StrategyProbabilityMarketSelectionGuardV2Report",
    "build_strategy_probability_market_selection_guard_v2",
    "strategy_probability_market_selection_guard_v2_payload",
)


@dataclass(frozen=True)
class StrategyProbabilityMarketSelectionGuardV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_MARKET_SELECTION_GUARD_V2_CONFIG_VERSION
    )
    minimum_research_readiness_score: Decimal = Decimal("0.700000")
    minimum_cost_adjusted_edge: Decimal = Decimal("0.030000")
    maximum_resolution_ambiguity_score: Decimal = Decimal("0.250000")
    minimum_liquidity_exit_feasibility_score: Decimal = Decimal("0.600000")
    maximum_portfolio_concentration_ratio: Decimal = Decimal("0.150000")
    minimum_specialist_quorum_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyProbabilityMarketSelectionGuardV2Config", self)
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "minimum_research_readiness_score",
            "maximum_resolution_ambiguity_score",
            "minimum_liquidity_exit_feasibility_score",
            "maximum_portfolio_concentration_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_cost_adjusted_edge",
            _normalize_probability_delta(
                "minimum_cost_adjusted_edge",
                self.minimum_cost_adjusted_edge,
            ),
        )
        object.__setattr__(
            self,
            "minimum_specialist_quorum_count",
            _normalize_positive_integral_decimal(
                "minimum_specialist_quorum_count",
                self.minimum_specialist_quorum_count,
            ),
        )
        _reject_unsafe_public_payload(
            "StrategyProbabilityMarketSelectionGuardV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyProbabilityMarketSelectionCandidate:
    candidate_id: str
    market_slug: str
    event_id: str
    research_source_id: str
    research_readiness_score: Decimal
    gross_probability_edge: Decimal
    estimated_fee_ratio: Decimal
    estimated_slippage_ratio: Decimal
    resolution_ambiguity_score: Decimal
    liquidity_exit_feasibility_score: Decimal
    projected_portfolio_concentration_ratio: Decimal
    specialist_quorum_count: Decimal
    captured_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyProbabilityMarketSelectionCandidate", self)
        for field_name in (
            "candidate_id",
            "market_slug",
            "event_id",
            "research_source_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "research_readiness_score",
            "gross_probability_edge",
            "estimated_fee_ratio",
            "estimated_slippage_ratio",
            "resolution_ambiguity_score",
            "liquidity_exit_feasibility_score",
            "projected_portfolio_concentration_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "specialist_quorum_count",
            _normalize_nonnegative_integral_decimal(
                "specialist_quorum_count",
                self.specialist_quorum_count,
            ),
        )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        _reject_unsafe_public_payload(
            "StrategyProbabilityMarketSelectionCandidate",
            self.payload,
        )

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyProbabilityMarketSelectionCandidate.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


@dataclass(frozen=True)
class StrategyProbabilityMarketSelectionDecision:
    candidate_id: str
    market_slug: str
    event_id: str
    research_source_id: str
    research_readiness_score: Decimal
    gross_probability_edge: Decimal
    estimated_fee_ratio: Decimal
    estimated_slippage_ratio: Decimal
    cost_adjusted_edge: Decimal
    resolution_ambiguity_score: Decimal
    liquidity_exit_feasibility_score: Decimal
    projected_portfolio_concentration_ratio: Decimal
    specialist_quorum_count: Decimal
    decision_status: str
    reason_codes: tuple[str, ...]
    captured_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyProbabilityMarketSelectionDecision", self)
        for field_name in (
            "candidate_id",
            "market_slug",
            "event_id",
            "research_source_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "research_readiness_score",
            "gross_probability_edge",
            "estimated_fee_ratio",
            "estimated_slippage_ratio",
            "resolution_ambiguity_score",
            "liquidity_exit_feasibility_score",
            "projected_portfolio_concentration_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_probability_delta("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "specialist_quorum_count",
            _normalize_nonnegative_integral_decimal(
                "specialist_quorum_count",
                self.specialist_quorum_count,
            ),
        )
        _require_decision_status("decision_status", self.decision_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _DECISION_REASON_CODES,
            ),
        )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        _validate_decision_consistency(self)
        _reject_unsafe_public_payload(
            "StrategyProbabilityMarketSelectionDecision",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyProbabilityMarketSelectionGuardV2Report:
    generated_at: datetime
    config_version: str
    decision_status: str
    candidate_count: Decimal
    pass_candidate_count: Decimal
    blocked_candidate_count: Decimal
    average_cost_adjusted_edge: Decimal
    minimum_cost_adjusted_edge_seen: Decimal
    maximum_resolution_ambiguity_seen: Decimal
    maximum_portfolio_concentration_seen: Decimal
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_hard_flags("StrategyProbabilityMarketSelectionGuardV2Report", self)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_decision_status("decision_status", self.decision_status)
        for field_name in (
            "candidate_count",
            "pass_candidate_count",
            "blocked_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_cost_adjusted_edge",
            "minimum_cost_adjusted_edge_seen",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_delta(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_resolution_ambiguity_seen",
            "maximum_portfolio_concentration_seen",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "decisions", _normalize_decisions(self.decisions))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload(
            "StrategyProbabilityMarketSelectionGuardV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_digest(self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyProbabilityMarketSelectionGuardV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_probability_market_selection_guard_v2(
    candidates: object,
    *,
    config: StrategyProbabilityMarketSelectionGuardV2Config | None = None,
    generated_at: datetime,
) -> StrategyProbabilityMarketSelectionGuardV2Report:
    if config is None:
        config = StrategyProbabilityMarketSelectionGuardV2Config()
    if type(config) is not StrategyProbabilityMarketSelectionGuardV2Config:
        raise ValueError(
            "config must be a StrategyProbabilityMarketSelectionGuardV2Config",
        )
    _require_hard_flags("StrategyProbabilityMarketSelectionGuardV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    decisions = _sorted_decisions(
        tuple(_decision_for_candidate(item, config) for item in normalized_candidates),
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "decision_status": _report_status(decisions),
        "candidate_count": Decimal(len(decisions)).quantize(_COUNT_QUANT),
        "pass_candidate_count": _decision_status_count(decisions, "pass"),
        "blocked_candidate_count": _decision_status_count(decisions, "blocked"),
        "average_cost_adjusted_edge": _average_cost_adjusted_edge(decisions),
        "minimum_cost_adjusted_edge_seen": _minimum_cost_adjusted_edge_seen(decisions),
        "maximum_resolution_ambiguity_seen": _maximum_resolution_ambiguity_seen(decisions),
        "maximum_portfolio_concentration_seen": (
            _maximum_portfolio_concentration_seen(decisions)
        ),
        "decisions": decisions,
        "reason_codes": _report_reason_codes(decisions),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return StrategyProbabilityMarketSelectionGuardV2Report(**values)


def strategy_probability_market_selection_guard_v2_payload(
    report: object,
) -> dict[str, object]:
    if type(report) is not StrategyProbabilityMarketSelectionGuardV2Report:
        raise ValueError("report must be StrategyProbabilityMarketSelectionGuardV2Report")
    return report.payload


def _decision_for_candidate(
    candidate: StrategyProbabilityMarketSelectionCandidate,
    config: StrategyProbabilityMarketSelectionGuardV2Config,
) -> StrategyProbabilityMarketSelectionDecision:
    cost_adjusted_edge = _cost_adjusted_edge(candidate)
    reason_codes = _decision_reason_codes(candidate, cost_adjusted_edge, config)
    status = "blocked" if reason_codes else "pass"
    return StrategyProbabilityMarketSelectionDecision(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        event_id=candidate.event_id,
        research_source_id=candidate.research_source_id,
        research_readiness_score=candidate.research_readiness_score,
        gross_probability_edge=candidate.gross_probability_edge,
        estimated_fee_ratio=candidate.estimated_fee_ratio,
        estimated_slippage_ratio=candidate.estimated_slippage_ratio,
        cost_adjusted_edge=cost_adjusted_edge,
        resolution_ambiguity_score=candidate.resolution_ambiguity_score,
        liquidity_exit_feasibility_score=candidate.liquidity_exit_feasibility_score,
        projected_portfolio_concentration_ratio=(
            candidate.projected_portfolio_concentration_ratio
        ),
        specialist_quorum_count=candidate.specialist_quorum_count,
        decision_status=status,
        reason_codes=reason_codes or ("market_selection_guard_candidate_pass",),
        captured_at=candidate.captured_at,
    )


def _decision_reason_codes(
    candidate: StrategyProbabilityMarketSelectionCandidate,
    cost_adjusted_edge: Decimal,
    config: StrategyProbabilityMarketSelectionGuardV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.research_readiness_score < config.minimum_research_readiness_score:
        reasons.append("weak_research_readiness_block")
    if cost_adjusted_edge < config.minimum_cost_adjusted_edge:
        reasons.append("thin_cost_adjusted_edge_block")
    if candidate.resolution_ambiguity_score > config.maximum_resolution_ambiguity_score:
        reasons.append("high_resolution_ambiguity_block")
    if (
        candidate.liquidity_exit_feasibility_score
        < config.minimum_liquidity_exit_feasibility_score
    ):
        reasons.append("low_liquidity_exit_feasibility_block")
    if (
        candidate.projected_portfolio_concentration_ratio
        > config.maximum_portfolio_concentration_ratio
    ):
        reasons.append("portfolio_concentration_block")
    if candidate.specialist_quorum_count < config.minimum_specialist_quorum_count:
        reasons.append("insufficient_specialist_quorum_block")
    return tuple(reasons)


def _cost_adjusted_edge(candidate: StrategyProbabilityMarketSelectionCandidate) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (
            candidate.gross_probability_edge
            - candidate.estimated_fee_ratio
            - candidate.estimated_slippage_ratio
        ).quantize(_SCORE_QUANT)


def _sorted_decisions(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
) -> tuple[StrategyProbabilityMarketSelectionDecision, ...]:
    return tuple(
        sorted(
            decisions,
            key=lambda row: (
                0 if row.decision_status == "blocked" else 1,
                row.candidate_id,
                row.market_slug,
            ),
        ),
    )


def _report_status(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
) -> str:
    if not decisions:
        return "blocked"
    if any(row.decision_status == "blocked" for row in decisions):
        return "blocked"
    return "pass"


def _report_reason_codes(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
) -> tuple[str, ...]:
    if not decisions:
        return ("market_selection_guard_no_candidates_block",)
    blocked_reasons: list[str] = []
    for reason in _DECISION_REASON_CODES[1:]:
        if any(reason in row.reason_codes for row in decisions):
            blocked_reasons.append(reason)
    if blocked_reasons:
        return ("market_selection_guard_candidates_blocked", *blocked_reasons)
    return ("market_selection_guard_candidates_passed",)


def _decision_status_count(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in decisions if row.decision_status == status)).quantize(
        _COUNT_QUANT,
    )


def _average_cost_adjusted_edge(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
) -> Decimal:
    if not decisions:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (
            sum(row.cost_adjusted_edge for row in decisions) / Decimal(len(decisions))
        ).quantize(_SCORE_QUANT)


def _minimum_cost_adjusted_edge_seen(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
) -> Decimal:
    if not decisions:
        return _ZERO
    return min(row.cost_adjusted_edge for row in decisions)


def _maximum_resolution_ambiguity_seen(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
) -> Decimal:
    if not decisions:
        return _ZERO
    return max(row.resolution_ambiguity_score for row in decisions)


def _maximum_portfolio_concentration_seen(
    decisions: tuple[StrategyProbabilityMarketSelectionDecision, ...],
) -> Decimal:
    if not decisions:
        return _ZERO
    return max(row.projected_portfolio_concentration_ratio for row in decisions)


def _normalize_candidates(
    value: object,
) -> tuple[StrategyProbabilityMarketSelectionCandidate, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("candidates must be an iterable")
    candidates = tuple(value)
    for item in candidates:
        if type(item) is not StrategyProbabilityMarketSelectionCandidate:
            raise ValueError(
                "candidate items must be StrategyProbabilityMarketSelectionCandidate",
            )
        _require_hard_flags("StrategyProbabilityMarketSelectionCandidate", item)
    keys = tuple(item.candidate_id for item in candidates)
    if len(set(keys)) != len(keys):
        raise ValueError("candidate items must not contain duplicate candidate_id values")
    return candidates


def _normalize_decisions(
    value: object,
) -> tuple[StrategyProbabilityMarketSelectionDecision, ...]:
    if type(value) is not tuple:
        raise ValueError("decisions must be a tuple")
    for item in value:
        if type(item) is not StrategyProbabilityMarketSelectionDecision:
            raise ValueError(
                "decisions must contain StrategyProbabilityMarketSelectionDecision",
            )
    return value


def _validate_decision_consistency(
    decision: StrategyProbabilityMarketSelectionDecision,
) -> None:
    calculated_edge = (
        decision.gross_probability_edge
        - decision.estimated_fee_ratio
        - decision.estimated_slippage_ratio
    ).quantize(_SCORE_QUANT)
    if decision.cost_adjusted_edge != calculated_edge:
        raise ValueError("cost_adjusted_edge must match cost inputs")
    if decision.decision_status == "pass":
        if decision.reason_codes != ("market_selection_guard_candidate_pass",):
            raise ValueError("pass decisions must use the pass reason code")
    elif "market_selection_guard_candidate_pass" in decision.reason_codes:
        raise ValueError("blocked decisions must not use the pass reason code")


def _validate_report_digest(
    report: StrategyProbabilityMarketSelectionGuardV2Report,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest mismatch")


def _validate_report_consistency(
    report: StrategyProbabilityMarketSelectionGuardV2Report,
) -> None:
    decisions = report.decisions
    if report.candidate_count != Decimal(len(decisions)).quantize(_COUNT_QUANT):
        raise ValueError("candidate_count must match decisions")
    if report.pass_candidate_count != _decision_status_count(decisions, "pass"):
        raise ValueError("pass_candidate_count must match decisions")
    if report.blocked_candidate_count != _decision_status_count(decisions, "blocked"):
        raise ValueError("blocked_candidate_count must match decisions")
    if report.pass_candidate_count + report.blocked_candidate_count != report.candidate_count:
        raise ValueError("decision counts must sum to candidate_count")
    if report.decision_status != _report_status(decisions):
        raise ValueError("decision_status must match decisions")
    if report.reason_codes != _report_reason_codes(decisions):
        raise ValueError("reason_codes must match decisions")
    if report.average_cost_adjusted_edge != _average_cost_adjusted_edge(decisions):
        raise ValueError("average_cost_adjusted_edge must match decisions")
    if report.minimum_cost_adjusted_edge_seen != _minimum_cost_adjusted_edge_seen(decisions):
        raise ValueError("minimum_cost_adjusted_edge_seen must match decisions")
    if (
        report.maximum_resolution_ambiguity_seen
        != _maximum_resolution_ambiguity_seen(decisions)
    ):
        raise ValueError("maximum_resolution_ambiguity_seen must match decisions")
    if (
        report.maximum_portfolio_concentration_seen
        != _maximum_portfolio_concentration_seen(decisions)
    ):
        raise ValueError("maximum_portfolio_concentration_seen must match decisions")
    if decisions != _sorted_decisions(decisions):
        raise ValueError("decisions must be sorted deterministically")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < Decimal("-1.000000"):
        raise ValueError(f"{field_name} must be >= -1.000000")
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_SCORE_QUANT)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized.quantize(_COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_integral_decimal(field_name, value)
    if normalized <= Decimal("0"):
        raise ValueError(f"{field_name} must be > 0")
    return normalized


def _require_decision_status(field_name: str, value: object) -> None:
    if value not in _DECISION_STATUSES:
        raise ValueError(f"{field_name} must be one of {_DECISION_STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        code = _require_non_empty_string(field_name, item)
        if code not in allowed:
            raise ValueError(f"{field_name} contains unknown reason code: {code}")
        if code not in normalized:
            normalized.append(code)
    return tuple(normalized)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    for char in value:
        if char not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be lowercase hex")


def _derived_validation_digest(value: object) -> str:
    payload = _payload_value(_without_validation_digest(value))
    _reject_unsafe_public_payload("derived_validation_digest", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _without_validation_digest(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _without_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, tuple):
        return tuple(_without_validation_digest(item) for item in value)
    if isinstance(value, list):
        return [_without_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _mentions_unsafe_text(str(key)):
                raise ValueError(f"{label} unsafe public key: {key}")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, str) and _mentions_unsafe_text(value):
        raise ValueError(f"{label} unsafe public value")


def _mentions_unsafe_text(value: str) -> bool:
    folded = value.lower()
    return any(fragment in folded for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS)
