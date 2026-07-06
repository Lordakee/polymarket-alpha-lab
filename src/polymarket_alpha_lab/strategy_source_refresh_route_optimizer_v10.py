"""Pure read-only source refresh route optimizer v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import string
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


SOURCE_REFRESH_ROUTE_OPTIMIZER_V10_CONFIG_VERSION = (
    "strategy-source-refresh-route-optimizer-v10"
)

REFRESH_ROUTES = (
    "defer_refresh",
    "standard_refresh",
    "specialist_backlog_refresh",
    "specialist_expedited_refresh",
)
REFRESH_QUEUES = (
    "source_refresh_monitor_queue",
    "source_refresh_stale_source_queue",
    "source_refresh_reliability_queue",
    "source_refresh_resolution_urgency_queue",
    "source_refresh_disagreement_queue",
    "source_refresh_specialist_queue",
)
VALIDATION_DIGEST_FIELD = "validation_digest"

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE = Decimal("1.000000")
MAX_PRIORITY = Decimal("100.000000")
LOW_PRIORITY_THRESHOLD = Decimal("30.000000")
SPECIALIST_BACKLOG_PRESSURE = Decimal("0.900000")
SPECIALIST_EXPEDITE_PRIORITY = Decimal("85.000000")
LOW_RELIABILITY_THRESHOLD = Decimal("0.500000")
HIGH_RELIABILITY_THRESHOLD = Decimal("0.900000")
HIGH_URGENCY_THRESHOLD = Decimal("0.800000")
HIGH_DISAGREEMENT_THRESHOLD = Decimal("0.600000")
HIGH_STALE_SOURCE_COUNT = Decimal("3")
MODERATE_SPECIALIST_PRESSURE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class StrategySourceRefreshRouteOptimizerV10Candidate:
    market_id: str
    category: str
    source_family: str
    stale_source_count: Decimal
    source_reliability: Decimal
    resolution_urgency: Decimal
    disagreement_rate: Decimal
    specialist_queue_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "stale_source_count",
            _normalize_nonnegative_count("stale_source_count", self.stale_source_count),
        )
        object.__setattr__(
            self,
            "source_reliability",
            _normalize_ratio("source_reliability", self.source_reliability),
        )
        object.__setattr__(
            self,
            "resolution_urgency",
            _normalize_ratio("resolution_urgency", self.resolution_urgency),
        )
        object.__setattr__(
            self,
            "disagreement_rate",
            _normalize_ratio("disagreement_rate", self.disagreement_rate),
        )
        object.__setattr__(
            self,
            "specialist_queue_pressure",
            _normalize_ratio(
                "specialist_queue_pressure",
                self.specialist_queue_pressure,
            ),
        )
        require_paper_only_flags(
            "strategy source refresh route optimizer v10 candidate",
            self,
        )


@dataclass(frozen=True)
class StrategySourceRefreshRouteOptimizerV10Decision:
    market_id: str
    category: str
    source_family: str
    stale_source_count: Decimal
    source_reliability: Decimal
    resolution_urgency: Decimal
    disagreement_rate: Decimal
    specialist_queue_pressure: Decimal
    refresh_route: str
    target_refresh_queues: tuple[str, ...]
    priority_score: Decimal
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("category", self.category)
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "stale_source_count",
            _normalize_nonnegative_count("stale_source_count", self.stale_source_count),
        )
        object.__setattr__(
            self,
            "source_reliability",
            _normalize_ratio("source_reliability", self.source_reliability),
        )
        object.__setattr__(
            self,
            "resolution_urgency",
            _normalize_ratio("resolution_urgency", self.resolution_urgency),
        )
        object.__setattr__(
            self,
            "disagreement_rate",
            _normalize_ratio("disagreement_rate", self.disagreement_rate),
        )
        object.__setattr__(
            self,
            "specialist_queue_pressure",
            _normalize_ratio(
                "specialist_queue_pressure",
                self.specialist_queue_pressure,
            ),
        )
        _require_member("refresh_route", self.refresh_route, REFRESH_ROUTES)
        object.__setattr__(
            self,
            "target_refresh_queues",
            _normalize_target_refresh_queues(self.target_refresh_queues),
        )
        object.__setattr__(
            self,
            "priority_score",
            _normalize_priority_score("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "payload", _normalize_payload("payload", self.payload))
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
            ),
        )
        _validate_decision(self)
        require_paper_only_flags(
            "strategy source refresh route optimizer v10 decision",
            self,
        )


def route_strategy_source_refresh_route_optimizer_v10(
    candidate: StrategySourceRefreshRouteOptimizerV10Candidate,
) -> StrategySourceRefreshRouteOptimizerV10Decision:
    if type(candidate) is not StrategySourceRefreshRouteOptimizerV10Candidate:
        raise ValueError(
            "candidate must be a StrategySourceRefreshRouteOptimizerV10Candidate",
        )
    require_paper_only_flags(
        "strategy source refresh route optimizer v10 candidate",
        candidate,
    )

    target_refresh_queues = _target_refresh_queues(candidate)
    priority_score, priority_was_clamped = _priority_score(candidate)
    refresh_route = _refresh_route(
        candidate,
        priority_score=priority_score,
        target_refresh_queues=target_refresh_queues,
    )
    reason_codes = _reason_codes(
        candidate,
        refresh_route=refresh_route,
        priority_was_clamped=priority_was_clamped,
    )
    payload = _decision_payload(
        candidate,
        refresh_route=refresh_route,
        target_refresh_queues=target_refresh_queues,
        priority_score=priority_score,
        reason_codes=reason_codes,
    )
    validation_digest = _payload_validation_digest(payload)
    payload = _payload_with_validation_digest(payload, validation_digest)

    return StrategySourceRefreshRouteOptimizerV10Decision(
        market_id=candidate.market_id,
        category=candidate.category,
        source_family=candidate.source_family,
        stale_source_count=candidate.stale_source_count,
        source_reliability=candidate.source_reliability,
        resolution_urgency=candidate.resolution_urgency,
        disagreement_rate=candidate.disagreement_rate,
        specialist_queue_pressure=candidate.specialist_queue_pressure,
        refresh_route=refresh_route,
        target_refresh_queues=target_refresh_queues,
        priority_score=priority_score,
        reason_codes=reason_codes,
        payload=payload,
        validation_digest=validation_digest,
    )


def strategy_source_refresh_route_optimizer_v10_payload(
    decision: StrategySourceRefreshRouteOptimizerV10Decision,
) -> dict[str, Any]:
    if type(decision) is not StrategySourceRefreshRouteOptimizerV10Decision:
        raise ValueError(
            "decision must be a StrategySourceRefreshRouteOptimizerV10Decision",
        )
    require_paper_only_flags(
        "strategy source refresh route optimizer v10 decision",
        decision,
    )
    payload = _normalize_payload("decision payload", decision.payload)
    _validate_decision(decision)
    if type(payload) is not dict:
        raise ValueError("decision payload must be a JSON object")
    require_paper_only_flags(
        "strategy source refresh route optimizer v10 payload",
        _PayloadFlags(payload),
    )
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _target_refresh_queues(
    value: StrategySourceRefreshRouteOptimizerV10Candidate
    | StrategySourceRefreshRouteOptimizerV10Decision,
) -> tuple[str, ...]:
    queues: list[str] = []
    if value.stale_source_count > ZERO_COUNT:
        queues.append("source_refresh_stale_source_queue")
    if value.source_reliability <= LOW_RELIABILITY_THRESHOLD:
        queues.append("source_refresh_reliability_queue")
    if value.resolution_urgency > ZERO:
        queues.append("source_refresh_resolution_urgency_queue")
    if value.disagreement_rate > ZERO:
        queues.append("source_refresh_disagreement_queue")
    if value.specialist_queue_pressure >= MODERATE_SPECIALIST_PRESSURE:
        queues.append("source_refresh_specialist_queue")
    if not queues:
        queues.append("source_refresh_monitor_queue")
    return tuple(queues)


def _priority_score(
    value: StrategySourceRefreshRouteOptimizerV10Candidate
    | StrategySourceRefreshRouteOptimizerV10Decision,
) -> tuple[Decimal, bool]:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = value.stale_source_count * Decimal("11.000000")
        raw_score += (ONE - value.source_reliability) * Decimal("45.000000")
        raw_score += value.resolution_urgency * Decimal("18.250000")
        raw_score += value.disagreement_rate * Decimal("32.000000")
        raw_score += value.specialist_queue_pressure * Decimal("5.000000")
    priority_score = _quantize(raw_score)
    if priority_score > MAX_PRIORITY:
        return MAX_PRIORITY, True
    if priority_score < ZERO:
        return ZERO, True
    return priority_score, False


def _refresh_route(
    value: StrategySourceRefreshRouteOptimizerV10Candidate
    | StrategySourceRefreshRouteOptimizerV10Decision,
    *,
    priority_score: Decimal,
    target_refresh_queues: tuple[str, ...],
) -> str:
    if (
        priority_score >= SPECIALIST_EXPEDITE_PRIORITY
        or value.resolution_urgency >= HIGH_URGENCY_THRESHOLD
        and value.disagreement_rate >= HIGH_DISAGREEMENT_THRESHOLD
        and value.source_reliability <= LOW_RELIABILITY_THRESHOLD
    ):
        return "specialist_expedited_refresh"
    if value.specialist_queue_pressure >= SPECIALIST_BACKLOG_PRESSURE:
        return "specialist_backlog_refresh"
    if target_refresh_queues == ("source_refresh_monitor_queue",):
        return "defer_refresh"
    if priority_score < LOW_PRIORITY_THRESHOLD:
        return "defer_refresh"
    return "standard_refresh"


def _reason_codes(
    value: StrategySourceRefreshRouteOptimizerV10Candidate
    | StrategySourceRefreshRouteOptimizerV10Decision,
    *,
    refresh_route: str,
    priority_was_clamped: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if value.stale_source_count >= HIGH_STALE_SOURCE_COUNT:
        reasons.append("stale_source_count_high")
    elif value.stale_source_count > ZERO_COUNT:
        reasons.append("stale_source_count_present")
    if value.source_reliability <= LOW_RELIABILITY_THRESHOLD:
        reasons.append("source_reliability_low")
    elif value.source_reliability >= HIGH_RELIABILITY_THRESHOLD:
        reasons.append("source_reliability_high")
    else:
        reasons.append("source_reliability_watch")
    if value.resolution_urgency >= HIGH_URGENCY_THRESHOLD:
        reasons.append("resolution_urgency_high")
    elif value.resolution_urgency > ZERO:
        reasons.append("resolution_urgency_watch")
    if value.disagreement_rate >= HIGH_DISAGREEMENT_THRESHOLD:
        reasons.append("disagreement_rate_high")
    elif value.disagreement_rate > ZERO:
        reasons.append("disagreement_rate_watch")
    if value.specialist_queue_pressure >= SPECIALIST_BACKLOG_PRESSURE:
        reasons.append("specialist_queue_pressure_high")
    elif value.specialist_queue_pressure >= MODERATE_SPECIALIST_PRESSURE:
        reasons.append("specialist_queue_pressure_moderate")
    else:
        reasons.append("specialist_queue_pressure_low")
    if priority_was_clamped:
        reasons.append("priority_score_clamped")
    reasons.append(f"refresh_route_{refresh_route}")
    return tuple(reasons)


def _decision_payload(
    value: StrategySourceRefreshRouteOptimizerV10Candidate
    | StrategySourceRefreshRouteOptimizerV10Decision,
    *,
    refresh_route: str,
    target_refresh_queues: tuple[str, ...],
    priority_score: Decimal,
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "config_version": SOURCE_REFRESH_ROUTE_OPTIMIZER_V10_CONFIG_VERSION,
        "market_id": value.market_id,
        "category": value.category,
        "source_family": value.source_family,
        "stale_source_count": str(value.stale_source_count),
        "source_reliability": str(value.source_reliability),
        "resolution_urgency": str(value.resolution_urgency),
        "disagreement_rate": str(value.disagreement_rate),
        "specialist_queue_pressure": str(value.specialist_queue_pressure),
        "refresh_route": refresh_route,
        "target_refresh_queues": list(target_refresh_queues),
        "priority_score": str(priority_score),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_decision(decision: StrategySourceRefreshRouteOptimizerV10Decision) -> None:
    expected_queues = _target_refresh_queues(decision)
    if decision.target_refresh_queues != expected_queues:
        raise ValueError("target_refresh_queues must match routed candidate inputs")
    expected_priority, priority_was_clamped = _priority_score(decision)
    if decision.priority_score != expected_priority:
        raise ValueError("priority_score must match routed candidate inputs")
    expected_route = _refresh_route(
        decision,
        priority_score=expected_priority,
        target_refresh_queues=expected_queues,
    )
    if decision.refresh_route != expected_route:
        raise ValueError("refresh_route must match routed candidate inputs")
    expected_reasons = _reason_codes(
        decision,
        refresh_route=expected_route,
        priority_was_clamped=priority_was_clamped,
    )
    if decision.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match routed candidate inputs")
    expected_payload = _decision_payload(
        decision,
        refresh_route=expected_route,
        target_refresh_queues=expected_queues,
        priority_score=expected_priority,
        reason_codes=expected_reasons,
    )
    expected_validation_digest = _payload_validation_digest(expected_payload)
    expected_payload = _payload_with_validation_digest(
        expected_payload,
        expected_validation_digest,
    )
    if decision.validation_digest != expected_validation_digest:
        raise ValueError("validation_digest must match routed candidate inputs")
    if decision.payload != expected_payload:
        raise ValueError("payload must match routed candidate inputs")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_priority_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > MAX_PRIORITY:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _normalize_target_refresh_queues(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("target_refresh_queues must contain known queue names")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("target_refresh_queues must contain known queue names") from exc
    if not items:
        raise ValueError("target_refresh_queues must contain at least one queue")
    seen: set[str] = set()
    for item in items:
        _require_member("target_refresh_queues", item, REFRESH_QUEUES)
        if item in seen:
            raise ValueError("target_refresh_queues must contain unique values")
        seen.add(item)
    return items


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    seen: set[str] = set()
    for item in items:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must contain unique values")
        seen.add(item)
    return items


def _normalize_payload(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    payload = json_ready_no_floats(value)
    if type(payload) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    _reject_unsafe_public_payload(field_name, payload)
    require_paper_only_flags(
        "strategy source refresh route optimizer v10 payload",
        _PayloadFlags(payload),
    )
    return payload


def _payload_with_validation_digest(
    payload: dict[str, Any],
    validation_digest: str,
) -> dict[str, Any]:
    return {**payload, VALIDATION_DIGEST_FIELD: validation_digest}


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value
        for key, value in payload.items()
        if key != VALIDATION_DIGEST_FIELD
    }
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64 or any(character not in string.hexdigits for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    reject_unsafe_surface_fields(label, payload)
    _reject_unsafe_public_values(label, payload)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if type(value) is bool or value is None:
        return
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_values(label, item)
        return


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must contain a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "SOURCE_REFRESH_ROUTE_OPTIMIZER_V10_CONFIG_VERSION",
    "StrategySourceRefreshRouteOptimizerV10Candidate",
    "StrategySourceRefreshRouteOptimizerV10Decision",
    "route_strategy_source_refresh_route_optimizer_v10",
    "strategy_source_refresh_route_optimizer_v10_payload",
)
