"""Pure public-safe dependency memory routing report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


CONFIG_VERSION = "research-event-outcome-dependency-memory-router-v0"
ROUTE_STATUSES = ("pass", "watch", "block")
ROUTED_TEAMS = (
    "dependency_memory_monitor",
    "dependency_mapping",
    "conflict_review",
    "freshness_review",
    "calibration_review",
    "lag_review",
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "status",
    "routed_team",
    "aggregate_dependency_strength",
    "freshness_score",
    "conflict_score",
    "calibration_score",
    "resolution_lag_score",
    "dependency_risk_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_THRESHOLD = Decimal("0.250000")
BLOCK_RISK_THRESHOLD = Decimal("0.500000")
ELEVATED_DEPENDENCY_THRESHOLD = Decimal("0.600000")
WATCH_FRESHNESS_THRESHOLD = Decimal("0.650000")
BLOCK_FRESHNESS_THRESHOLD = Decimal("0.200000")
WATCH_CONFLICT_THRESHOLD = Decimal("0.350000")
BLOCK_CONFLICT_THRESHOLD = Decimal("0.850000")
WATCH_CALIBRATION_THRESHOLD = Decimal("0.750000")
WATCH_LAG_THRESHOLD = Decimal("0.600000")
DEPENDENCY_WEIGHT = Decimal("0.300000")
FRESHNESS_DECAY_WEIGHT = Decimal("0.200000")
CONFLICT_WEIGHT = Decimal("0.250000")
CALIBRATION_GAP_WEIGHT = Decimal("0.150000")
RESOLUTION_LAG_WEIGHT = Decimal("0.100000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class ResearchEventOutcomeDependencyMemoryMetrics:
    aggregate_dependency_strength: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    calibration_score: Decimal
    resolution_lag_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeDependencyMemoryMetrics:
            raise TypeError(
                "ResearchEventOutcomeDependencyMemoryMetrics does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeDependencyMemoryMetrics:
            raise ValueError(
                "metrics must be exactly ResearchEventOutcomeDependencyMemoryMetrics",
            )
        for field_name in (
            "aggregate_dependency_strength",
            "freshness_score",
            "conflict_score",
            "calibration_score",
            "resolution_lag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("dependency memory metrics", self)


@dataclass(frozen=True)
class ResearchEventOutcomeDependencyMemoryRoute:
    config_version: str
    status: str
    routed_team: str
    aggregate_dependency_strength: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    calibration_score: Decimal
    resolution_lag_score: Decimal
    dependency_risk_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeDependencyMemoryRoute:
            raise TypeError(
                "ResearchEventOutcomeDependencyMemoryRoute does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeDependencyMemoryRoute:
            raise ValueError(
                "route must be exactly ResearchEventOutcomeDependencyMemoryRoute",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, ROUTE_STATUSES)
        _require_member("routed_team", self.routed_team, ROUTED_TEAMS)
        for field_name in (
            "aggregate_dependency_strength",
            "freshness_score",
            "conflict_score",
            "calibration_score",
            "resolution_lag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dependency_risk_score",
            _normalize_ratio("dependency_risk_score", self.dependency_risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("dependency memory route", self)
        _validate_route_consistency(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _route_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_route_derived_validation_digest(self)


def route_research_event_outcome_dependency_memory(
    metrics: ResearchEventOutcomeDependencyMemoryMetrics,
) -> ResearchEventOutcomeDependencyMemoryRoute:
    if type(metrics) is not ResearchEventOutcomeDependencyMemoryMetrics:
        raise ValueError(
            "metrics must be a ResearchEventOutcomeDependencyMemoryMetrics",
        )
    require_paper_only_flags("dependency memory metrics", metrics)
    risk_score = _dependency_risk_score(metrics)
    status = _route_status(metrics, risk_score)
    routed_team = _routed_team(metrics, status)
    reason_codes = _reason_codes(metrics, status=status, routed_team=routed_team)

    return ResearchEventOutcomeDependencyMemoryRoute(
        config_version=CONFIG_VERSION,
        status=status,
        routed_team=routed_team,
        aggregate_dependency_strength=metrics.aggregate_dependency_strength,
        freshness_score=metrics.freshness_score,
        conflict_score=metrics.conflict_score,
        calibration_score=metrics.calibration_score,
        resolution_lag_score=metrics.resolution_lag_score,
        dependency_risk_score=risk_score,
        reason_codes=reason_codes,
    )


def research_event_outcome_dependency_memory_router_payload(
    route: ResearchEventOutcomeDependencyMemoryRoute,
) -> dict[str, object]:
    if type(route) is not ResearchEventOutcomeDependencyMemoryRoute:
        raise ValueError("route must be a ResearchEventOutcomeDependencyMemoryRoute")
    require_paper_only_flags("dependency memory route", route)
    _validate_route_consistency(route)
    _validate_route_derived_validation_digest(route)
    payload = _route_public_payload_values(route)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = route.derived_validation_digest
    ready_payload = json_ready_no_floats(payload)
    if type(ready_payload) is not dict:
        raise ValueError("route payload must be a JSON object")
    return ready_payload


def _dependency_risk_score(
    value: ResearchEventOutcomeDependencyMemoryMetrics
    | ResearchEventOutcomeDependencyMemoryRoute,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        freshness_decay = ONE - value.freshness_score
        calibration_gap = ONE - value.calibration_score
        score = (
            value.aggregate_dependency_strength * DEPENDENCY_WEIGHT
            + freshness_decay * FRESHNESS_DECAY_WEIGHT
            + value.conflict_score * CONFLICT_WEIGHT
            + calibration_gap * CALIBRATION_GAP_WEIGHT
            + value.resolution_lag_score * RESOLUTION_LAG_WEIGHT
        )
    return _quantize(score)


def _route_status(
    value: ResearchEventOutcomeDependencyMemoryMetrics
    | ResearchEventOutcomeDependencyMemoryRoute,
    risk_score: Decimal,
) -> str:
    if (
        risk_score >= BLOCK_RISK_THRESHOLD
        or value.conflict_score >= BLOCK_CONFLICT_THRESHOLD
        or value.freshness_score <= BLOCK_FRESHNESS_THRESHOLD
    ):
        return "block"
    if (
        risk_score >= WATCH_RISK_THRESHOLD
        or value.aggregate_dependency_strength >= ELEVATED_DEPENDENCY_THRESHOLD
        or value.freshness_score <= WATCH_FRESHNESS_THRESHOLD
        or value.conflict_score >= WATCH_CONFLICT_THRESHOLD
        or value.calibration_score <= WATCH_CALIBRATION_THRESHOLD
        or value.resolution_lag_score >= WATCH_LAG_THRESHOLD
    ):
        return "watch"
    return "pass"


def _routed_team(
    value: ResearchEventOutcomeDependencyMemoryMetrics
    | ResearchEventOutcomeDependencyMemoryRoute,
    status: str,
) -> str:
    if status == "pass":
        return "dependency_memory_monitor"
    if value.conflict_score >= BLOCK_CONFLICT_THRESHOLD:
        return "conflict_review"
    if value.freshness_score <= BLOCK_FRESHNESS_THRESHOLD:
        return "freshness_review"
    if (
        value.calibration_score <= WATCH_CALIBRATION_THRESHOLD
        and value.conflict_score < BLOCK_CONFLICT_THRESHOLD
    ):
        return "calibration_review"
    if value.resolution_lag_score >= WATCH_LAG_THRESHOLD:
        return "lag_review"
    return "dependency_mapping"


def _reason_codes(
    value: ResearchEventOutcomeDependencyMemoryMetrics
    | ResearchEventOutcomeDependencyMemoryRoute,
    *,
    status: str,
    routed_team: str,
) -> tuple[str, ...]:
    reasons = [f"dependency_memory_router_{status}"]
    if value.aggregate_dependency_strength >= ELEVATED_DEPENDENCY_THRESHOLD:
        reasons.append("aggregate_dependency_strength_elevated")
    if value.freshness_score <= BLOCK_FRESHNESS_THRESHOLD:
        reasons.append("freshness_decay_blocking")
    elif value.freshness_score <= WATCH_FRESHNESS_THRESHOLD:
        reasons.append("freshness_decay_elevated")
    if value.conflict_score >= BLOCK_CONFLICT_THRESHOLD:
        reasons.append("conflict_pressure_blocking")
    elif value.conflict_score >= WATCH_CONFLICT_THRESHOLD:
        reasons.append("conflict_pressure_elevated")
    if (
        value.calibration_score <= WATCH_CALIBRATION_THRESHOLD
        and value.conflict_score < BLOCK_CONFLICT_THRESHOLD
    ):
        reasons.append("calibration_gap_elevated")
    if value.resolution_lag_score >= WATCH_LAG_THRESHOLD:
        reasons.append("resolution_lag_elevated")
    reasons.append(f"routed_team_{routed_team}")
    return tuple(dict.fromkeys(reasons))


def _validate_route_consistency(
    route: ResearchEventOutcomeDependencyMemoryRoute,
) -> None:
    expected_risk_score = _dependency_risk_score(route)
    if route.dependency_risk_score != expected_risk_score:
        raise ValueError("dependency_risk_score must match aggregate metrics")
    expected_status = _route_status(route, expected_risk_score)
    if route.status != expected_status:
        raise ValueError("status must match aggregate metrics")
    expected_team = _routed_team(route, expected_status)
    if route.routed_team != expected_team:
        raise ValueError("routed_team must match aggregate metrics")
    expected_reasons = _reason_codes(
        route,
        status=expected_status,
        routed_team=expected_team,
    )
    if route.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match aggregate metrics")


def _route_public_payload_values(
    route: ResearchEventOutcomeDependencyMemoryRoute,
) -> dict[str, object]:
    return {
        "config_version": route.config_version,
        "status": route.status,
        "routed_team": route.routed_team,
        "aggregate_dependency_strength": str(route.aggregate_dependency_strength),
        "freshness_score": str(route.freshness_score),
        "conflict_score": str(route.conflict_score),
        "calibration_score": str(route.calibration_score),
        "resolution_lag_score": str(route.resolution_lag_score),
        "dependency_risk_score": str(route.dependency_risk_score),
        "reason_codes": list(route.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _route_derived_validation_digest(
    route: ResearchEventOutcomeDependencyMemoryRoute,
) -> str:
    return _derived_validation_digest(_route_public_payload_values(route))


def _validate_route_derived_validation_digest(
    route: ResearchEventOutcomeDependencyMemoryRoute,
) -> None:
    if route.derived_validation_digest != _route_derived_validation_digest(route):
        raise ValueError("derived_validation_digest must match route fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    return _sha256("research_event_outcome_dependency_memory_router", values)


def _digest_payload_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ",".join(_digest_payload_value(item) for item in value)
    return str(value)


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


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


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must contain a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 hex string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex string")
    return value


__all__ = (
    "CONFIG_VERSION",
    "ROUTE_STATUSES",
    "ResearchEventOutcomeDependencyMemoryMetrics",
    "ResearchEventOutcomeDependencyMemoryRoute",
    "route_research_event_outcome_dependency_memory",
    "research_event_outcome_dependency_memory_router_payload",
)
