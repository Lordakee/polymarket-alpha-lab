"""Pure typed market research priority queue."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


__all__ = (
    "DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION",
    "StrategyMarketResearchPriorityCandidate",
    "StrategyMarketResearchPriorityQueueConfig",
    "StrategyMarketResearchPriorityQueueItem",
    "StrategyMarketResearchPriorityQueueReport",
    "build_strategy_market_research_priority_queue",
    "strategy_market_research_priority_queue_payload",
)


DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION = (
    "strategy-market-research-priority-queue-v0"
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
EMPTY_REASON_CODE = "strategy_market_research_priority_queue_clear"
REASON_CODE_PRIORITY = (
    "expected_value_high",
    "information_gap_high",
    "settlement_near",
    "liquidity_ready",
    "liquidity_thin",
    "team_expertise_available",
    "team_expertise_gap",
    "source_stale",
    EMPTY_REASON_CODE,
)
REASON_CODE_SET = frozenset(REASON_CODE_PRIORITY)

EXPECTED_VALUE_WEIGHT = Decimal("0.264795643233370231")
INFORMATION_GAP_WEIGHT = Decimal("0.288587455314633542")
SETTLEMENT_URGENCY_WEIGHT = Decimal("0.292633780502332535")
LIQUIDITY_WEIGHT = Decimal("0.100000000000000000")
TEAM_EXPERTISE_WEIGHT = Decimal("0.005847734549026661")
SOURCE_AGE_WEIGHT = Decimal("0.048135386400637031")

PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "queue_status",
        "input_count",
        "queued_count",
        "highest_priority_score",
        "queue_items",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    ),
)
PUBLIC_ITEM_KEYS = frozenset(
    (
        "candidate_id",
        "expected_value",
        "information_gap_score",
        "seconds_to_settlement",
        "available_liquidity",
        "team_expertise_score",
        "source_age_seconds",
        "priority_score",
        "research_priority_rank",
        "next_research_action",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "api_key",
        "approval",
        "auth",
        "balance",
        "cancel",
        "database",
        "dsn",
        "endpoint",
        "execute",
        "execution",
        "fill",
        "http",
        "live_trading",
        "network",
        "nonce",
        "order",
        "position",
        "private_key",
        "secret",
        "signature",
        "sql",
        "submit",
        "token",
        "trade",
        "transfer",
        "url",
        "wallet",
        "websocket",
    ),
)


@dataclass(frozen=True)
class StrategyMarketResearchPriorityQueueConfig:
    config_version: str = DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION
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
class StrategyMarketResearchPriorityCandidate:
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
class StrategyMarketResearchPriorityQueueItem:
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
class StrategyMarketResearchPriorityQueueReport:
    generated_at: datetime
    config_version: str
    queue_status: str
    input_count: Decimal
    queued_count: Decimal
    highest_priority_score: Decimal
    queue_items: tuple[StrategyMarketResearchPriorityQueueItem, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
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
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_research_priority_queue_payload(self)


def build_strategy_market_research_priority_queue(
    candidates: Iterable[StrategyMarketResearchPriorityCandidate],
    *,
    config: StrategyMarketResearchPriorityQueueConfig,
    generated_at: datetime,
) -> StrategyMarketResearchPriorityQueueReport:
    """Rank paper market research candidates for readonly human investigation."""

    if type(config) is not StrategyMarketResearchPriorityQueueConfig:
        raise ValueError("config must be a StrategyMarketResearchPriorityQueueConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_candidates = _normalize_candidates(candidates)
    scored_items = tuple(
        _item_from_candidate(candidate, config) for candidate in source_candidates
    )
    queue_items = tuple(
        StrategyMarketResearchPriorityQueueItem(
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
    return StrategyMarketResearchPriorityQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        queue_status="research_required" if queue_items else "clear",
        input_count=_count_decimal(len(source_candidates)),
        queued_count=_count_decimal(len(queue_items)),
        highest_priority_score=queue_items[0].priority_score if queue_items else ZERO,
        queue_items=queue_items,
        reason_codes=reason_codes,
    )


def strategy_market_research_priority_queue_payload(
    report: StrategyMarketResearchPriorityQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyMarketResearchPriorityQueueReport:
        return _report_payload(report, include_digest=True)
    if type(report) is dict:
        return _validated_public_payload(report)
    raise ValueError("report must be a StrategyMarketResearchPriorityQueueReport")


def _item_from_candidate(
    candidate: StrategyMarketResearchPriorityCandidate,
    config: StrategyMarketResearchPriorityQueueConfig,
) -> StrategyMarketResearchPriorityQueueItem:
    reason_codes = _candidate_reason_codes(candidate, config)
    return StrategyMarketResearchPriorityQueueItem(
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
    candidate: StrategyMarketResearchPriorityCandidate,
    config: StrategyMarketResearchPriorityQueueConfig,
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
            + SOURCE_AGE_WEIGHT
            * _source_age_factor(candidate.source_age_seconds, config.max_source_age_seconds)
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
    candidate: StrategyMarketResearchPriorityCandidate,
    config: StrategyMarketResearchPriorityQueueConfig,
) -> Decimal:
    if candidate.team_expertise_score <= config.low_team_expertise_score:
        with localcontext(DECIMAL_CONTEXT):
            return _clamp_ratio(ONE - candidate.team_expertise_score)
    return candidate.team_expertise_score


def _source_age_factor(source_age_seconds: Decimal, max_source_age_seconds: Decimal) -> Decimal:
    if max_source_age_seconds <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(source_age_seconds / max_source_age_seconds)


def _candidate_reason_codes(
    candidate: StrategyMarketResearchPriorityCandidate,
    config: StrategyMarketResearchPriorityQueueConfig,
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
    if candidate.source_age_seconds > config.max_source_age_seconds:
        reason_codes.append("source_stale")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _next_research_action(reason_codes: tuple[str, ...]) -> str:
    if "liquidity_thin" in reason_codes:
        return "monitor_liquidity_before_research"
    if "information_gap_high" in reason_codes:
        return "collect_missing_evidence"
    if "source_stale" in reason_codes:
        return "refresh_sources"
    if "team_expertise_gap" in reason_codes:
        return "route_to_domain_researcher"
    return "monitor_until_new_signal"


def _combined_report_reason_codes(
    queue_items: tuple[StrategyMarketResearchPriorityQueueItem, ...],
) -> tuple[str, ...]:
    if not queue_items:
        return (EMPTY_REASON_CODE,)
    found = {reason_code for item in queue_items for reason_code in item.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in found)


def _queue_item_sort_key(
    item: StrategyMarketResearchPriorityQueueItem,
) -> tuple[Decimal, str]:
    return (-item.priority_score, item.candidate_id)


def _normalize_candidates(
    candidates: Iterable[StrategyMarketResearchPriorityCandidate],
) -> tuple[StrategyMarketResearchPriorityCandidate, ...]:
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyMarketResearchPriorityCandidate:
            raise ValueError(
                "candidates must contain StrategyMarketResearchPriorityCandidate",
            )
        _require_hard_flags(candidate)
        if candidate.candidate_id in seen:
            raise ValueError("candidates must not contain duplicate candidate_id")
        seen.add(candidate.candidate_id)
    return normalized


def _normalize_queue_items(
    queue_items: tuple[StrategyMarketResearchPriorityQueueItem, ...],
) -> tuple[StrategyMarketResearchPriorityQueueItem, ...]:
    if type(queue_items) is not tuple:
        raise ValueError("queue_items must be a tuple")
    normalized: list[StrategyMarketResearchPriorityQueueItem] = []
    seen: set[str] = set()
    for item in queue_items:
        if type(item) is not StrategyMarketResearchPriorityQueueItem:
            raise ValueError(
                "queue_items must contain StrategyMarketResearchPriorityQueueItem",
            )
        _require_hard_flags(item)
        if item.candidate_id in seen:
            raise ValueError("queue_items must not contain duplicate candidate_id")
        seen.add(item.candidate_id)
        normalized.append(item)
    return tuple(normalized)


def _validate_report(report: StrategyMarketResearchPriorityQueueReport) -> None:
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


def _report_payload(
    report: StrategyMarketResearchPriorityQueueReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    _require_hard_flags(report)
    payload: dict[str, Any] = {
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
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _validated_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _reject_unsafe_public_payload(payload)
    _require_public_payload_keys(payload)
    digest = _public_string(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _require_digest("derived_validation_digest", digest)
    if digest != _public_payload_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")
    if type(payload["queue_items"]) is not list:
        raise ValueError("queue_items must be a list")
    queue_items = tuple(_public_payload_item(item) for item in payload["queue_items"])
    report = StrategyMarketResearchPriorityQueueReport(
        generated_at=_public_datetime(payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        queue_status=_public_string("queue_status", payload["queue_status"]),
        input_count=_public_decimal("input_count", payload["input_count"]),
        queued_count=_public_decimal("queued_count", payload["queued_count"]),
        highest_priority_score=_public_decimal(
            "highest_priority_score",
            payload["highest_priority_score"],
        ),
        queue_items=queue_items,
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        derived_validation_digest=digest,
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )
    return _report_payload(report, include_digest=True)


def _public_payload_item(payload: object) -> StrategyMarketResearchPriorityQueueItem:
    if type(payload) is not dict:
        raise ValueError("queue_items must contain dict payloads")
    _require_public_item_keys(payload)
    return StrategyMarketResearchPriorityQueueItem(
        candidate_id=_public_string("candidate_id", payload["candidate_id"]),
        expected_value=_public_decimal("expected_value", payload["expected_value"]),
        information_gap_score=_public_decimal(
            "information_gap_score",
            payload["information_gap_score"],
        ),
        seconds_to_settlement=_public_decimal(
            "seconds_to_settlement",
            payload["seconds_to_settlement"],
        ),
        available_liquidity=_public_decimal(
            "available_liquidity",
            payload["available_liquidity"],
        ),
        team_expertise_score=_public_decimal(
            "team_expertise_score",
            payload["team_expertise_score"],
        ),
        source_age_seconds=_public_decimal(
            "source_age_seconds",
            payload["source_age_seconds"],
        ),
        priority_score=_public_decimal("priority_score", payload["priority_score"]),
        research_priority_rank=_public_decimal(
            "research_priority_rank",
            payload["research_priority_rank"],
        ),
        next_research_action=_public_string(
            "next_research_action",
            payload["next_research_action"],
        ),
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _require_public_payload_keys(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    missing = PUBLIC_PAYLOAD_KEYS - payload.keys()
    if missing:
        raise ValueError("public payload is missing required fields")
    extra = payload.keys() - PUBLIC_PAYLOAD_KEYS
    if extra:
        raise ValueError("public payload contains unsupported fields")


def _require_public_item_keys(payload: dict[str, Any]) -> None:
    missing = PUBLIC_ITEM_KEYS - payload.keys()
    if missing:
        raise ValueError("queue item payload is missing required fields")
    extra = payload.keys() - PUBLIC_ITEM_KEYS
    if extra:
        raise ValueError("queue item payload contains unsupported fields")


def _derived_validation_digest(report: StrategyMarketResearchPriorityQueueReport) -> str:
    return _public_payload_digest(_report_payload(report, include_digest=False))


def _public_payload_digest(payload: dict[str, Any]) -> str:
    return sha256(repr(_canonical_payload_value(payload)).encode("utf-8")).hexdigest()


def _canonical_payload_value(value: object) -> object:
    if type(value) is dict:
        return tuple(
            (key, _canonical_payload_value(value[key]))
            for key in sorted(value)
            if key != "derived_validation_digest"
        )
    if type(value) is list:
        return tuple(_canonical_payload_value(item) for item in value)
    if type(value) in {str, bool}:
        return value
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, nested in value.items():
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is list:
        for nested in value:
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return
    if type(value) is bool:
        return
    raise ValueError("public payload numeric values must be Decimal-derived strings")


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError("unsafe public payload surface")


def _public_datetime(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError("generated_at must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("generated_at must be an ISO datetime") from exc
    return _as_utc("generated_at", parsed)


def _public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    normalized = _normalize_decimal(field_name, decimal_value)
    if _decimal_string(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _public_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return tuple(_public_string("reason_code", reason_code) for reason_code in value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a 64-character hex digest")


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
