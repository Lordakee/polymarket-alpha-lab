"""Pure paper pretrade checklist v5 for recommendation readiness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP


DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION = (
    "strategy-pretrade-checklist-v5"
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

PASS_REASON = "strategy_pretrade_checklist_v5_passed"
EVENT_FEATURES_REASON = "strategy_pretrade_event_features_not_ready"
SOURCE_QUALITY_REASON = "strategy_pretrade_source_quality_not_ready"
CONFLICT_POLICY_REASON = "strategy_pretrade_conflict_policy_not_clear"
RESOLUTION_CONTRACT_REASON = "strategy_pretrade_resolution_contract_not_ready"
COST_MODEL_REASON = "strategy_pretrade_cost_model_not_ready"
COST_ADJUSTED_EV_REASON = "strategy_pretrade_cost_adjusted_ev_below_minimum"
EV_RANK_REASON = "strategy_pretrade_ev_rank_outside_cutoff"
WATCHLIST_REASON = "strategy_pretrade_watchlist_not_eligible"
AUDIT_PACKET_REASON = "strategy_pretrade_audit_packet_not_ready"

REASON_CODES = (
    PASS_REASON,
    EVENT_FEATURES_REASON,
    SOURCE_QUALITY_REASON,
    CONFLICT_POLICY_REASON,
    RESOLUTION_CONTRACT_REASON,
    COST_MODEL_REASON,
    COST_ADJUSTED_EV_REASON,
    EV_RANK_REASON,
    WATCHLIST_REASON,
    AUDIT_PACKET_REASON,
)

CHECKLIST_STATUSES = ("pass", "blocked")
EVENT_FEATURE_STATUSES = ("complete", "partial", "missing")
SOURCE_QUALITY_STATUSES = ("verified", "weak", "missing")
CONFLICT_POLICY_STATUSES = ("clear", "unresolved")
RESOLUTION_CONTRACT_STATUSES = ("complete", "incomplete", "missing")
COST_MODEL_STATUSES = ("current", "stale", "missing")
WATCHLIST_STATUSES = ("eligible", "paused", "excluded")
AUDIT_PACKET_STATUSES = ("complete", "incomplete", "missing")

EVENT_FEATURES_BLOCKING_ITEM = "event_features"
SOURCE_QUALITY_BLOCKING_ITEM = "source_quality"
CONFLICT_POLICY_BLOCKING_ITEM = "conflict_policy"
RESOLUTION_CONTRACT_BLOCKING_ITEM = "resolution_contract"
COST_MODEL_BLOCKING_ITEM = "cost_model"
COST_ADJUSTED_EV_BLOCKING_ITEM = "cost_adjusted_ev"
EV_RANK_BLOCKING_ITEM = "ev_rank"
WATCHLIST_BLOCKING_ITEM = "watchlist_status"
AUDIT_PACKET_BLOCKING_ITEM = "audit_packet"

BLOCKING_ITEMS = (
    EVENT_FEATURES_BLOCKING_ITEM,
    SOURCE_QUALITY_BLOCKING_ITEM,
    CONFLICT_POLICY_BLOCKING_ITEM,
    RESOLUTION_CONTRACT_BLOCKING_ITEM,
    COST_MODEL_BLOCKING_ITEM,
    COST_ADJUSTED_EV_BLOCKING_ITEM,
    EV_RANK_BLOCKING_ITEM,
    WATCHLIST_BLOCKING_ITEM,
    AUDIT_PACKET_BLOCKING_ITEM,
)

__all__ = (
    "DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION",
    "StrategyPretradeChecklistV5Candidate",
    "StrategyPretradeChecklistV5Config",
    "StrategyPretradeChecklistV5Result",
    "build_strategy_pretrade_checklist_v5",
)


@dataclass(frozen=True)
class StrategyPretradeChecklistV5Config:
    config_version: str = DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION
    min_event_feature_score: Decimal = Decimal("0.800000")
    min_source_quality_score: Decimal = Decimal("0.800000")
    min_cost_adjusted_ev: Decimal = Decimal("0.010000")
    max_ev_rank: Decimal = Decimal("10.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_event_feature_score",
            _ratio("min_event_feature_score", self.min_event_feature_score),
        )
        object.__setattr__(
            self,
            "min_source_quality_score",
            _ratio("min_source_quality_score", self.min_source_quality_score),
        )
        object.__setattr__(
            self,
            "min_cost_adjusted_ev",
            _decimal("min_cost_adjusted_ev", self.min_cost_adjusted_ev),
        )
        object.__setattr__(
            self,
            "max_ev_rank",
            _positive_decimal("max_ev_rank", self.max_ev_rank),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyPretradeChecklistV5Candidate:
    candidate_id: str
    event_feature_status: str
    event_feature_score: Decimal
    source_quality_status: str
    source_quality_score: Decimal
    conflict_policy_status: str
    resolution_contract_status: str
    cost_model_status: str
    cost_adjusted_ev: Decimal
    ev_rank: Decimal
    watchlist_status: str
    audit_packet_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_member(
            "event_feature_status",
            self.event_feature_status,
            EVENT_FEATURE_STATUSES,
        )
        object.__setattr__(
            self,
            "event_feature_score",
            _ratio("event_feature_score", self.event_feature_score),
        )
        _require_member(
            "source_quality_status",
            self.source_quality_status,
            SOURCE_QUALITY_STATUSES,
        )
        object.__setattr__(
            self,
            "source_quality_score",
            _ratio("source_quality_score", self.source_quality_score),
        )
        _require_member(
            "conflict_policy_status",
            self.conflict_policy_status,
            CONFLICT_POLICY_STATUSES,
        )
        _require_member(
            "resolution_contract_status",
            self.resolution_contract_status,
            RESOLUTION_CONTRACT_STATUSES,
        )
        _require_member("cost_model_status", self.cost_model_status, COST_MODEL_STATUSES)
        object.__setattr__(
            self,
            "cost_adjusted_ev",
            _decimal("cost_adjusted_ev", self.cost_adjusted_ev),
        )
        object.__setattr__(self, "ev_rank", _positive_decimal("ev_rank", self.ev_rank))
        _require_member("watchlist_status", self.watchlist_status, WATCHLIST_STATUSES)
        _require_member(
            "audit_packet_status",
            self.audit_packet_status,
            AUDIT_PACKET_STATUSES,
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyPretradeChecklistV5Result:
    generated_at: datetime
    config_version: str
    candidate_id: str
    checklist_status: str
    blocking_items: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_member("checklist_status", self.checklist_status, CHECKLIST_STATUSES)
        object.__setattr__(
            self,
            "blocking_items",
            _normalize_blocking_items(self.blocking_items),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result_shape(self)
        _require_hard_flags("result", self)


def build_strategy_pretrade_checklist_v5(
    candidate: StrategyPretradeChecklistV5Candidate,
    *,
    config: StrategyPretradeChecklistV5Config,
    generated_at: datetime,
) -> StrategyPretradeChecklistV5Result:
    if type(candidate) is not StrategyPretradeChecklistV5Candidate:
        raise ValueError("candidate must be a StrategyPretradeChecklistV5Candidate")
    if type(config) is not StrategyPretradeChecklistV5Config:
        raise ValueError("config must be a StrategyPretradeChecklistV5Config")
    _require_hard_flags("candidate", candidate)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    blocking_items, reason_codes = _checklist_findings(candidate, config)
    checklist_status = "blocked" if blocking_items else "pass"

    return StrategyPretradeChecklistV5Result(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_id=candidate.candidate_id,
        checklist_status=checklist_status,
        blocking_items=blocking_items,
        reason_codes=reason_codes,
    )


def _checklist_findings(
    candidate: StrategyPretradeChecklistV5Candidate,
    config: StrategyPretradeChecklistV5Config,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    blocking_items: list[str] = []
    reason_codes: list[str] = []

    if (
        candidate.event_feature_status != "complete"
        or candidate.event_feature_score < config.min_event_feature_score
    ):
        blocking_items.append(EVENT_FEATURES_BLOCKING_ITEM)
        reason_codes.append(EVENT_FEATURES_REASON)
    if (
        candidate.source_quality_status != "verified"
        or candidate.source_quality_score < config.min_source_quality_score
    ):
        blocking_items.append(SOURCE_QUALITY_BLOCKING_ITEM)
        reason_codes.append(SOURCE_QUALITY_REASON)
    if candidate.conflict_policy_status != "clear":
        blocking_items.append(CONFLICT_POLICY_BLOCKING_ITEM)
        reason_codes.append(CONFLICT_POLICY_REASON)
    if candidate.resolution_contract_status != "complete":
        blocking_items.append(RESOLUTION_CONTRACT_BLOCKING_ITEM)
        reason_codes.append(RESOLUTION_CONTRACT_REASON)
    if candidate.cost_model_status != "current":
        blocking_items.append(COST_MODEL_BLOCKING_ITEM)
        reason_codes.append(COST_MODEL_REASON)
    if candidate.cost_adjusted_ev < config.min_cost_adjusted_ev:
        blocking_items.append(COST_ADJUSTED_EV_BLOCKING_ITEM)
        reason_codes.append(COST_ADJUSTED_EV_REASON)
    if candidate.ev_rank > config.max_ev_rank:
        blocking_items.append(EV_RANK_BLOCKING_ITEM)
        reason_codes.append(EV_RANK_REASON)
    if candidate.watchlist_status != "eligible":
        blocking_items.append(WATCHLIST_BLOCKING_ITEM)
        reason_codes.append(WATCHLIST_REASON)
    if candidate.audit_packet_status != "complete":
        blocking_items.append(AUDIT_PACKET_BLOCKING_ITEM)
        reason_codes.append(AUDIT_PACKET_REASON)

    if not blocking_items:
        reason_codes.append(PASS_REASON)

    return tuple(blocking_items), tuple(reason_codes)


def _validate_result_shape(result: StrategyPretradeChecklistV5Result) -> None:
    if result.checklist_status == "pass":
        if result.blocking_items:
            raise ValueError("blocking_items must be empty when checklist_status is pass")
        if result.reason_codes != (PASS_REASON,):
            raise ValueError("reason_codes must match checklist_status")
        return
    if not result.blocking_items:
        raise ValueError("checklist_status must match blocking_items")
    if result.reason_codes == (PASS_REASON,):
        raise ValueError("reason_codes must match checklist_status")
    if len(result.blocking_items) != len(result.reason_codes):
        raise ValueError("reason_codes must match blocking_items")


def _normalize_blocking_items(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("blocking_items must be a list or tuple")
    normalized = tuple(value)
    seen_items: set[str] = set()
    for item in normalized:
        _require_canonical_string("blocking_items", item)
        if item not in BLOCKING_ITEMS:
            raise ValueError("blocking_items must contain known blocking items")
        if item in seen_items:
            raise ValueError("blocking_items must be unique")
        seen_items.add(item)
    if normalized != tuple(item for item in BLOCKING_ITEMS if item in seen_items):
        raise ValueError("blocking_items must follow checklist order")
    return normalized


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _ratio(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return decimal


def _positive_decimal(name: str, value: object) -> Decimal:
    decimal = _decimal(name, value)
    if decimal <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _require_member(name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        joined_values = ", ".join(allowed_values)
        raise ValueError(f"{name} must be one of: {joined_values}")


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
