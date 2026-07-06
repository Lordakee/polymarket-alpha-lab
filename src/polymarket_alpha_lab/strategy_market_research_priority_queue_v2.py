"""Pure typed market research priority queue v2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable


DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_V2_CONFIG_VERSION = (
    "strategy-market-research-priority-queue-v2-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

QUEUE_STATUSES = frozenset(("clear", "research_required"))
NEXT_RESEARCH_ACTIONS = frozenset(
    (
        "collect_missing_evidence",
        "monitor_liquidity_before_research",
        "monitor_until_new_signal",
        "refresh_sources",
        "route_to_domain_researcher",
    ),
)
EMPTY_REASON_CODE = "strategy_market_research_priority_queue_v2_clear"
REASON_CODE_PRIORITY = (
    "expected_value_high",
    "information_gap_high",
    "settlement_near",
    "liquidity_ready",
    "liquidity_thin",
    "team_expertise_available",
    "team_expertise_gap",
    "source_fresh",
    "source_stale",
    EMPTY_REASON_CODE,
)
REASON_CODE_SET = frozenset(REASON_CODE_PRIORITY)

EXPECTED_VALUE_WEIGHT = Decimal("0.250000000000000000")
INFORMATION_GAP_WEIGHT = Decimal("0.313524395035765200")
SETTLEMENT_URGENCY_WEIGHT = Decimal("0.273701193187321000")
LIQUIDITY_WEIGHT = Decimal("0.100000000000000000")
TEAM_EXPERTISE_WEIGHT = Decimal("0.005847734549026661")
SOURCE_FRESHNESS_WEIGHT = Decimal("0.056926677227887156")


@dataclass(frozen=True)
class StrategyMarketResearchPriorityQueueV2Config:
    config_version: str = DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_V2_CONFIG_VERSION
    high_expected_value: Decimal = Decimal("0.060000")
    high_information_gap_score: Decimal = Decimal("0.500000")
    urgent_settlement_seconds: Decimal = Decimal("86400.000000")
    max_priority_settlement_seconds: Decimal = Decimal("604800.000000")
    min_research_liquidity: Decimal = Decimal("250.000000")
    high_team_expertise_score: Decimal = Decimal("0.600000")
    low_team_expertise_score: Decimal = Decimal("0.300000")
    max_source_age_seconds: Decimal = Decimal("43200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "high_expected_value",
            "urgent_settlement_seconds",
            "max_priority_settlement_seconds",
            "min_research_liquidity",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_information_gap_score",
            "high_team_expertise_score",
            "low_team_expertise_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.high_expected_value <= ZERO:
            raise ValueError("high_expected_value must be positive")
        if self.urgent_settlement_seconds > self.max_priority_settlement_seconds:
            raise ValueError(
                "urgent_settlement_seconds must be <= max_priority_settlement_seconds",
            )
        if self.min_research_liquidity <= ZERO:
            raise ValueError("min_research_liquidity must be positive")
        if self.low_team_expertise_score > self.high_team_expertise_score:
            raise ValueError(
                "low_team_expertise_score must be <= high_team_expertise_score",
            )
        if self.max_source_age_seconds <= ZERO:
            raise ValueError("max_source_age_seconds must be positive")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyMarketResearchPriorityQueueV2Candidate:
    candidate_id: str
    expected_value: Decimal
    information_gap_score: Decimal
    seconds_to_settlement: Decimal
    available_liquidity: Decimal
    team_expertise_score: Decimal
    source_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "expected_value",
            _normalize_decimal("expected_value", self.expected_value),
        )
        object.__setattr__(
            self,
            "information_gap_score",
            _normalize_ratio("information_gap_score", self.information_gap_score),
        )
        for field_name in (
            "seconds_to_settlement",
            "available_liquidity",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_expertise_score",
            _normalize_ratio("team_expertise_score", self.team_expertise_score),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyMarketResearchPriorityQueueV2Item:
    candidate_id: str
    expected_value: Decimal
    information_gap_score: Decimal
    seconds_to_settlement: Decimal
    available_liquidity: Decimal
    team_expertise_score: Decimal
    source_age_seconds: Decimal
    priority_score: Decimal
    research_priority_rank: Decimal
    next_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(
            self,
            "expected_value",
            _normalize_decimal("expected_value", self.expected_value),
        )
        object.__setattr__(
            self,
            "information_gap_score",
            _normalize_ratio("information_gap_score", self.information_gap_score),
        )
        for field_name in (
            "seconds_to_settlement",
            "available_liquidity",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_expertise_score",
            _normalize_ratio("team_expertise_score", self.team_expertise_score),
        )
        object.__setattr__(
            self,
            "priority_score",
            _normalize_ratio("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "research_priority_rank",
            _normalize_positive_count("research_priority_rank", self.research_priority_rank),
        )
        _require_next_research_action("next_research_action", self.next_research_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyMarketResearchPriorityQueueV2Report:
    generated_at: datetime
    config_version: str
    queue_status: str
    input_count: Decimal
    queued_count: Decimal
    highest_priority_score: Decimal
    queue_items: tuple[StrategyMarketResearchPriorityQueueV2Item, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_queue_status("queue_status", self.queue_status)
        for field_name in ("input_count", "queued_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _normalize_ratio("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "queue_items", _normalize_queue_items(self.queue_items))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_strategy_market_research_priority_queue_v2(
    candidates: Iterable[StrategyMarketResearchPriorityQueueV2Candidate],
    *,
    config: StrategyMarketResearchPriorityQueueV2Config,
    generated_at: datetime,
) -> StrategyMarketResearchPriorityQueueV2Report:
    """Rank paper market research candidates for readonly human investigation."""

    if type(config) is not StrategyMarketResearchPriorityQueueV2Config:
        raise ValueError("config must be a StrategyMarketResearchPriorityQueueV2Config")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    scored_items = tuple(
        _item_from_candidate(candidate, config) for candidate in source_candidates
    )
    queue_items = tuple(
        StrategyMarketResearchPriorityQueueV2Item(
            candidate_id=item.candidate_id,
            expected_value=item.expected_value,
            information_gap_score=item.information_gap_score,
            seconds_to_settlement=item.seconds_to_settlement,
            available_liquidity=item.available_liquidity,
            team_expertise_score=item.team_expertise_score,
            source_age_seconds=item.source_age_seconds,
            priority_score=item.priority_score,
            research_priority_rank=_count_decimal(index),
            next_research_action=item.next_research_action,
            reason_codes=item.reason_codes,
        )
        for index, item in enumerate(sorted(scored_items, key=_queue_item_sort_key), start=1)
    )
    reason_codes = _combined_report_reason_codes(queue_items)
    return StrategyMarketResearchPriorityQueueV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        queue_status="research_required" if queue_items else "clear",
        input_count=_count_decimal(len(source_candidates)),
        queued_count=_count_decimal(len(queue_items)),
        highest_priority_score=queue_items[0].priority_score if queue_items else ZERO,
        queue_items=queue_items,
        reason_codes=reason_codes,
    )


def strategy_market_research_priority_queue_v2_payload(
    report: StrategyMarketResearchPriorityQueueV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketResearchPriorityQueueV2Report:
        raise ValueError("report must be a StrategyMarketResearchPriorityQueueV2Report")
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "queue_status": report.queue_status,
        "input_count": _decimal_string(report.input_count),
        "queued_count": _decimal_string(report.queued_count),
        "highest_priority_score": _decimal_string(report.highest_priority_score),
        "queue_items": [
            {
                "candidate_id": item.candidate_id,
                "expected_value": _decimal_string(item.expected_value),
                "information_gap_score": _decimal_string(item.information_gap_score),
                "seconds_to_settlement": _decimal_string(item.seconds_to_settlement),
                "available_liquidity": _decimal_string(item.available_liquidity),
                "team_expertise_score": _decimal_string(item.team_expertise_score),
                "source_age_seconds": _decimal_string(item.source_age_seconds),
                "priority_score": _decimal_string(item.priority_score),
                "research_priority_rank": _decimal_string(item.research_priority_rank),
                "next_research_action": item.next_research_action,
                "reason_codes": list(item.reason_codes),
                "paper_only": item.paper_only,
                "report_only": item.report_only,
                "readonly": item.readonly,
            }
            for item in report.queue_items
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _item_from_candidate(
    candidate: StrategyMarketResearchPriorityQueueV2Candidate,
    config: StrategyMarketResearchPriorityQueueV2Config,
) -> StrategyMarketResearchPriorityQueueV2Item:
    reason_codes = _candidate_reason_codes(candidate, config)
    return StrategyMarketResearchPriorityQueueV2Item(
        candidate_id=candidate.candidate_id,
        expected_value=candidate.expected_value,
        information_gap_score=candidate.information_gap_score,
        seconds_to_settlement=candidate.seconds_to_settlement,
        available_liquidity=candidate.available_liquidity,
        team_expertise_score=candidate.team_expertise_score,
        source_age_seconds=candidate.source_age_seconds,
        priority_score=_priority_score(candidate, config),
        research_priority_rank=ONE,
        next_research_action=_next_research_action(reason_codes),
        reason_codes=reason_codes,
    )


def _priority_score(
    candidate: StrategyMarketResearchPriorityQueueV2Candidate,
    config: StrategyMarketResearchPriorityQueueV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            EXPECTED_VALUE_WEIGHT
            * _expected_value_factor(candidate.expected_value, config.high_expected_value)
            + INFORMATION_GAP_WEIGHT * candidate.information_gap_score
            + SETTLEMENT_URGENCY_WEIGHT
            * _settlement_urgency_factor(
                candidate.seconds_to_settlement,
                config.max_priority_settlement_seconds,
            )
            + LIQUIDITY_WEIGHT
            * _liquidity_factor(candidate.available_liquidity, config.min_research_liquidity)
            + TEAM_EXPERTISE_WEIGHT * _team_research_factor(candidate, config)
            + SOURCE_FRESHNESS_WEIGHT
            * _source_freshness_factor(
                candidate.source_age_seconds,
                config.max_source_age_seconds,
            )
        )
    return _quantize_ratio("priority_score", _clamp_ratio(score))


def _expected_value_factor(expected_value: Decimal, high_expected_value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(expected_value / high_expected_value)


def _settlement_urgency_factor(
    seconds_to_settlement: Decimal,
    max_priority_settlement_seconds: Decimal,
) -> Decimal:
    if max_priority_settlement_seconds <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - (seconds_to_settlement / max_priority_settlement_seconds))


def _liquidity_factor(available_liquidity: Decimal, min_research_liquidity: Decimal) -> Decimal:
    if min_research_liquidity <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(available_liquidity / min_research_liquidity)


def _team_research_factor(
    candidate: StrategyMarketResearchPriorityQueueV2Candidate,
    config: StrategyMarketResearchPriorityQueueV2Config,
) -> Decimal:
    if candidate.team_expertise_score <= config.low_team_expertise_score:
        with localcontext(DECIMAL_CONTEXT):
            return _clamp_ratio(ONE - candidate.team_expertise_score)
    return candidate.team_expertise_score


def _source_freshness_factor(source_age_seconds: Decimal, max_source_age_seconds: Decimal) -> Decimal:
    if source_age_seconds <= max_source_age_seconds:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(max_source_age_seconds / source_age_seconds)


def _candidate_reason_codes(
    candidate: StrategyMarketResearchPriorityQueueV2Candidate,
    config: StrategyMarketResearchPriorityQueueV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.expected_value >= config.high_expected_value:
        reason_codes.append("expected_value_high")
    if candidate.information_gap_score >= config.high_information_gap_score:
        reason_codes.append("information_gap_high")
    if candidate.seconds_to_settlement <= config.urgent_settlement_seconds:
        reason_codes.append("settlement_near")
    if candidate.available_liquidity >= config.min_research_liquidity:
        reason_codes.append("liquidity_ready")
    else:
        reason_codes.append("liquidity_thin")
    if candidate.team_expertise_score >= config.high_team_expertise_score:
        reason_codes.append("team_expertise_available")
    if candidate.team_expertise_score <= config.low_team_expertise_score:
        reason_codes.append("team_expertise_gap")
    if candidate.source_age_seconds <= config.max_source_age_seconds:
        reason_codes.append("source_fresh")
    else:
        reason_codes.append("source_stale")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _next_research_action(reason_codes: tuple[str, ...]) -> str:
    if "liquidity_thin" in reason_codes:
        return "monitor_liquidity_before_research"
    if "source_stale" in reason_codes:
        return "refresh_sources"
    if "information_gap_high" in reason_codes:
        return "collect_missing_evidence"
    if "team_expertise_gap" in reason_codes:
        return "route_to_domain_researcher"
    return "monitor_until_new_signal"


def _combined_report_reason_codes(
    queue_items: tuple[StrategyMarketResearchPriorityQueueV2Item, ...],
) -> tuple[str, ...]:
    if not queue_items:
        return (EMPTY_REASON_CODE,)
    found = {reason_code for item in queue_items for reason_code in item.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in found)


def _queue_item_sort_key(
    item: StrategyMarketResearchPriorityQueueV2Item,
) -> tuple[Decimal, str]:
    return (-item.priority_score, item.candidate_id)


def _normalize_candidates(
    candidates: Iterable[StrategyMarketResearchPriorityQueueV2Candidate],
) -> tuple[StrategyMarketResearchPriorityQueueV2Candidate, ...]:
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyMarketResearchPriorityQueueV2Candidate:
            raise ValueError(
                "candidates must contain StrategyMarketResearchPriorityQueueV2Candidate",
            )
        _require_hard_flags(candidate)
        if candidate.candidate_id in seen:
            raise ValueError("candidates must not contain duplicate candidate_id")
        seen.add(candidate.candidate_id)
    return normalized


def _normalize_queue_items(
    queue_items: tuple[StrategyMarketResearchPriorityQueueV2Item, ...],
) -> tuple[StrategyMarketResearchPriorityQueueV2Item, ...]:
    if type(queue_items) is not tuple:
        raise ValueError("queue_items must be a tuple")
    normalized: list[StrategyMarketResearchPriorityQueueV2Item] = []
    seen: set[str] = set()
    for item in queue_items:
        if type(item) is not StrategyMarketResearchPriorityQueueV2Item:
            raise ValueError(
                "queue_items must contain StrategyMarketResearchPriorityQueueV2Item",
            )
        _require_hard_flags(item)
        if item.candidate_id in seen:
            raise ValueError("queue_items must not contain duplicate candidate_id")
        seen.add(item.candidate_id)
        normalized.append(item)
    return tuple(normalized)


def _validate_report(report: StrategyMarketResearchPriorityQueueV2Report) -> None:
    expected_count = _count_decimal(len(report.queue_items))
    if report.queued_count != expected_count:
        raise ValueError("queued_count must match queue_items")
    if report.input_count < report.queued_count:
        raise ValueError("input_count must be >= queued_count")
    sorted_items = tuple(sorted(report.queue_items, key=_queue_item_sort_key))
    for index, item in enumerate(report.queue_items, start=1):
        if item != sorted_items[index - 1] or item.research_priority_rank != _count_decimal(index):
            raise ValueError("queue_items must follow deterministic sequence")
    if report.queue_items:
        if report.queue_status != "research_required":
            raise ValueError("queue_status must be research_required when queue_items exist")
        if report.highest_priority_score != report.queue_items[0].priority_score:
            raise ValueError("highest_priority_score must match first queue item")
    else:
        if report.queue_status != "clear":
            raise ValueError("queue_status must be clear when queue_items is empty")
        if report.highest_priority_score != ZERO:
            raise ValueError("highest_priority_score must be zero when queue_items is empty")
    expected_reason_codes = _combined_report_reason_codes(report.queue_items)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match queue_items")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _quantize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return quantized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    count = _normalize_nonnegative_count(field_name, value)
    if count <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return count


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODE_SET:
            raise ValueError("reason_codes contains unsupported reason_code")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    expected = tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in seen)
    if tuple(normalized) != expected:
        raise ValueError("reason_codes must follow deterministic order")
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_queue_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in QUEUE_STATUSES:
        raise ValueError(f"{field_name} is unsupported")


def _require_next_research_action(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in NEXT_RESEARCH_ACTIONS:
        raise ValueError(f"{field_name} is unsupported")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")
