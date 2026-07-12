"""Canonical report-only probability event screen contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


__all__ = (
    "ProbabilityEventScreen",
    "ProbabilityEventScreenPublicPayload",
    "validate_probability_event_screen_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

READY = "ready"
ATTENTION = "attention"
BLOCKER = "blocker"
STATUSES = (READY, ATTENTION, BLOCKER)
RISK_READINESS_STATUSES = (READY, ATTENTION, BLOCKER)
QUALITY_STATUSES = (READY, ATTENTION, BLOCKER)
MEMORY_POLICY_STATUSES = (READY, ATTENTION, BLOCKER)

LIQUIDITY_ATTENTION_FLOOR = Decimal("0.500000")
LIQUIDITY_BLOCKER_FLOOR = Decimal("0.100000")
DEPTH_ATTENTION_FLOOR = Decimal("0.500000")
DEPTH_BLOCKER_FLOOR = Decimal("0.100000")
SPREAD_ATTENTION_CEILING = Decimal("0.060000")
SPREAD_BLOCKER_CEILING = Decimal("0.120000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
MANUAL_NEXT_STEP_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

DECIMAL_FIELD_NAMES = (
    "yes_executable_probability",
    "yes_executable_price",
    "no_executable_probability",
    "no_executable_price",
    "forecast_probability",
    "market_probability",
    "gross_edge_probability",
    "total_cost_probability",
    "cost_adjusted_threshold_probability",
    "edge_to_threshold_probability",
    "liquidity_probability",
    "depth_probability",
    "spread_probability",
)
SIGNED_DECIMAL_FIELD_NAMES = ("edge_to_threshold_probability",)
RATIO_DECIMAL_FIELD_NAMES = tuple(
    field_name
    for field_name in DECIMAL_FIELD_NAMES
    if field_name not in SIGNED_DECIMAL_FIELD_NAMES
)


class ProbabilityEventScreenPublicPayload(dict[str, object]):
    """Small immutable dict used for the public contract payload."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ProbabilityEventScreen:
    generated_at: datetime
    event_ref: str
    market_ref: str
    yes_executable_probability: Decimal
    yes_executable_price: Decimal
    no_executable_probability: Decimal
    no_executable_price: Decimal
    forecast_probability: Decimal
    market_probability: Decimal
    gross_edge_probability: Decimal
    total_cost_probability: Decimal
    cost_adjusted_threshold_probability: Decimal
    edge_to_threshold_probability: Decimal
    liquidity_probability: Decimal
    depth_probability: Decimal
    spread_probability: Decimal
    resolution_risk_readiness: str
    settlement_risk_readiness: str
    source_quality_status: str
    specialist_team_route: str
    memory_policy_status: str
    manual_next_step: str
    direction: str = ""
    status: str = ""
    reason_codes: tuple[str, ...] = ()
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreen:
            raise ValueError("screen must be exactly ProbabilityEventScreen")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("event_ref", self.event_ref)
        _require_public_label("market_ref", self.market_ref)
        for field_name in RATIO_DECIMAL_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in SIGNED_DECIMAL_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _require_signed_decimal(field_name, getattr(self, field_name)),
            )
        _validate_probability_pair(self)
        _validate_edge_consistency(self)
        _require_known(
            "resolution_risk_readiness",
            self.resolution_risk_readiness,
            RISK_READINESS_STATUSES,
        )
        _require_known(
            "settlement_risk_readiness",
            self.settlement_risk_readiness,
            RISK_READINESS_STATUSES,
        )
        _require_known("source_quality_status", self.source_quality_status, QUALITY_STATUSES)
        _require_known("memory_policy_status", self.memory_policy_status, MEMORY_POLICY_STATUSES)
        _require_public_label("specialist_team_route", self.specialist_team_route)
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_phase_flags(self)

        derived_direction = _direction_for(self)
        derived_reason_codes = _reason_codes_for(self)
        derived_status = _status_for(derived_reason_codes)
        object.__setattr__(self, "direction", _resolve_derived("direction", self.direction, derived_direction))
        object.__setattr__(self, "reason_codes", _resolve_derived_tuple(self.reason_codes, derived_reason_codes))
        object.__setattr__(self, "status", _resolve_derived("status", self.status, derived_status))
        derived_digest = _payload_digest(_payload_items(self, digest=""))
        object.__setattr__(self, "digest", _resolve_digest(self.digest, derived_digest))

    @property
    def public_payload(self) -> ProbabilityEventScreenPublicPayload:
        return probability_event_screen_public_payload(self)


def probability_event_screen_public_payload(
    screen: ProbabilityEventScreen,
) -> ProbabilityEventScreenPublicPayload:
    if type(screen) is not ProbabilityEventScreen:
        raise ValueError("screen must be a ProbabilityEventScreen")
    _require_phase_flags(screen)
    payload = ProbabilityEventScreenPublicPayload(_payload_items(screen, digest=screen.digest))
    validate_probability_event_screen_public_payload(payload)
    return payload


def validate_probability_event_screen_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    expected_keys = set(_payload_keys())
    actual_keys = set(payload.keys())
    if actual_keys != expected_keys:
        raise ValueError("payload must match the canonical ProbabilityEventScreen schema")
    for key in ("generated_at", "event_ref", "market_ref", "specialist_team_route", "manual_next_step"):
        if type(payload[key]) is not str:
            raise ValueError(f"{key} must be a string")
    for key in RATIO_DECIMAL_FIELD_NAMES:
        value = payload[key]
        if type(value) is not str:
            raise ValueError(f"{key} must be serialized as a string")
        _require_probability_decimal(key, Decimal(value))
    for key in SIGNED_DECIMAL_FIELD_NAMES:
        value = payload[key]
        if type(value) is not str:
            raise ValueError(f"{key} must be serialized as a string")
        _require_signed_decimal(key, Decimal(value))
    for key in (
        "resolution_risk_readiness",
        "settlement_risk_readiness",
        "source_quality_status",
        "memory_policy_status",
        "status",
    ):
        if payload[key] not in STATUSES:
            raise ValueError(f"{key} must be a known status")
    if payload["direction"] not in ("yes", "no"):
        raise ValueError("direction must be yes or no")
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in reason_codes:
        _require_manual_next_step("reason_code", reason_code)
    for key in ("paper_only", "report_only", "readonly"):
        if payload[key] is not True:
            raise ValueError(f"{key} must be True")
    digest = payload["digest"]
    if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
        raise ValueError("digest must be a sha256 hex string")
    without_digest = dict(payload)
    without_digest["digest"] = ""
    if digest != _payload_digest(without_digest):
        raise ValueError("digest must match public payload")
    return payload


def _payload_keys() -> tuple[str, ...]:
    return (
        "generated_at",
        "event_ref",
        "market_ref",
        "yes_executable_probability",
        "yes_executable_price",
        "no_executable_probability",
        "no_executable_price",
        "forecast_probability",
        "market_probability",
        "gross_edge_probability",
        "total_cost_probability",
        "cost_adjusted_threshold_probability",
        "edge_to_threshold_probability",
        "liquidity_probability",
        "depth_probability",
        "spread_probability",
        "resolution_risk_readiness",
        "settlement_risk_readiness",
        "source_quality_status",
        "specialist_team_route",
        "memory_policy_status",
        "manual_next_step",
        "direction",
        "status",
        "reason_codes",
        "digest",
        "paper_only",
        "report_only",
        "readonly",
    )


def _payload_items(screen: ProbabilityEventScreen, *, digest: str) -> dict[str, object]:
    return {
        "generated_at": screen.generated_at.isoformat(),
        "event_ref": screen.event_ref,
        "market_ref": screen.market_ref,
        "yes_executable_probability": _decimal_text(screen.yes_executable_probability),
        "yes_executable_price": _decimal_text(screen.yes_executable_price),
        "no_executable_probability": _decimal_text(screen.no_executable_probability),
        "no_executable_price": _decimal_text(screen.no_executable_price),
        "forecast_probability": _decimal_text(screen.forecast_probability),
        "market_probability": _decimal_text(screen.market_probability),
        "gross_edge_probability": _decimal_text(screen.gross_edge_probability),
        "total_cost_probability": _decimal_text(screen.total_cost_probability),
        "cost_adjusted_threshold_probability": _decimal_text(
            screen.cost_adjusted_threshold_probability,
        ),
        "edge_to_threshold_probability": _decimal_text(screen.edge_to_threshold_probability),
        "liquidity_probability": _decimal_text(screen.liquidity_probability),
        "depth_probability": _decimal_text(screen.depth_probability),
        "spread_probability": _decimal_text(screen.spread_probability),
        "resolution_risk_readiness": screen.resolution_risk_readiness,
        "settlement_risk_readiness": screen.settlement_risk_readiness,
        "source_quality_status": screen.source_quality_status,
        "specialist_team_route": screen.specialist_team_route,
        "memory_policy_status": screen.memory_policy_status,
        "manual_next_step": screen.manual_next_step,
        "direction": screen.direction,
        "status": screen.status,
        "reason_codes": screen.reason_codes,
        "digest": digest,
        "paper_only": screen.paper_only,
        "report_only": screen.report_only,
        "readonly": screen.readonly,
    }


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_label(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or not MANUAL_NEXT_STEP_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical snake_case label")


def _require_known(field_name: str, value: str, values: tuple[str, ...]) -> None:
    if value not in values:
        raise ValueError(f"{field_name} must be ready, attention, or blocker")


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    quantized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _require_signed_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    quantized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if quantized < -ONE or quantized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return quantized


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(QUANTUM, rounding=ROUND_HALF_UP), "f")


def _validate_probability_pair(screen: ProbabilityEventScreen) -> None:
    if screen.no_executable_probability != ONE - screen.yes_executable_probability:
        raise ValueError(
            "no_executable_probability must equal 1 - yes_executable_probability",
        )
    if screen.no_executable_price != ONE - screen.yes_executable_price:
        raise ValueError("no_executable_price must equal 1 - yes_executable_price")
    if screen.yes_executable_price != screen.yes_executable_probability:
        raise ValueError("yes_executable_price must equal yes_executable_probability")
    if screen.no_executable_price != screen.no_executable_probability:
        raise ValueError("no_executable_price must equal no_executable_probability")
    if screen.market_probability != screen.yes_executable_probability:
        raise ValueError("market_probability must equal yes_executable_probability")


def _direction_for(screen: ProbabilityEventScreen) -> str:
    return "yes" if screen.forecast_probability >= screen.market_probability else "no"


def _selected_edge(screen: ProbabilityEventScreen) -> Decimal:
    if _direction_for(screen) == "yes":
        return screen.forecast_probability - screen.market_probability
    return screen.market_probability - screen.forecast_probability


def _validate_edge_consistency(screen: ProbabilityEventScreen) -> None:
    if screen.gross_edge_probability != _selected_edge(screen):
        raise ValueError("gross_edge_probability must match the selected direction")
    if screen.edge_to_threshold_probability != (
        screen.forecast_probability - screen.cost_adjusted_threshold_probability
    ).copy_abs():
        expected = (
            screen.forecast_probability - screen.cost_adjusted_threshold_probability
            if _direction_for(screen) == "yes"
            else screen.cost_adjusted_threshold_probability - screen.forecast_probability
        )
        if screen.edge_to_threshold_probability != expected:
            raise ValueError(
                "edge_to_threshold_probability must match the selected direction",
            )


def _reason_codes_for(screen: ProbabilityEventScreen) -> tuple[str, ...]:
    reasons: list[str] = []
    if screen.gross_edge_probability < screen.total_cost_probability:
        reasons.append("gross_edge_does_not_cover_total_cost")
    if screen.edge_to_threshold_probability < ZERO:
        reasons.append("edge_below_cost_adjusted_threshold")
    if screen.liquidity_probability <= LIQUIDITY_BLOCKER_FLOOR:
        reasons.append("liquidity_blocker")
    elif screen.liquidity_probability < LIQUIDITY_ATTENTION_FLOOR:
        reasons.append("liquidity_depth_attention")
    if screen.depth_probability <= DEPTH_BLOCKER_FLOOR:
        reasons.append("depth_blocker")
    elif screen.depth_probability < DEPTH_ATTENTION_FLOOR and "liquidity_depth_attention" not in reasons:
        reasons.append("liquidity_depth_attention")
    if screen.spread_probability >= SPREAD_BLOCKER_CEILING:
        reasons.append("spread_blocker")
    elif screen.spread_probability > SPREAD_ATTENTION_CEILING:
        reasons.append("spread_attention")
    _append_status_reason(
        reasons,
        screen.resolution_risk_readiness,
        "resolution_risk",
    )
    _append_status_reason(
        reasons,
        screen.settlement_risk_readiness,
        "settlement_risk",
    )
    _append_status_reason(reasons, screen.source_quality_status, "source_quality")
    _append_status_reason(reasons, screen.memory_policy_status, "memory_policy")
    return tuple(sorted(reasons)) if reasons else ("ready_probability_event_screen",)


def _append_status_reason(reasons: list[str], status: str, prefix: str) -> None:
    if status == BLOCKER:
        reasons.append(f"{prefix}_blocker")
    elif status == ATTENTION:
        reasons.append(f"{prefix}_attention")


def _status_for(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_blocker") or reason in {"edge_below_cost_adjusted_threshold", "gross_edge_does_not_cover_total_cost", "spread_blocker", "depth_blocker", "liquidity_blocker"} for reason in reason_codes):
        return BLOCKER
    if reason_codes != ("ready_probability_event_screen",):
        return ATTENTION
    return READY


def _resolve_derived(field_name: str, provided: str, derived: str) -> str:
    if provided == "":
        return derived
    if provided != derived:
        raise ValueError(f"{field_name} must match derived value")
    return provided


def _resolve_derived_tuple(
    provided: tuple[str, ...],
    derived: tuple[str, ...],
) -> tuple[str, ...]:
    if provided == ():
        return derived
    normalized = tuple(sorted(provided))
    if normalized != derived:
        raise ValueError("reason_codes must match derived value")
    return normalized


def _resolve_digest(provided: str, derived: str) -> str:
    if provided == "":
        return derived
    if not DIGEST_RE.fullmatch(provided):
        raise ValueError("digest must be a sha256 hex string")
    if provided != derived:
        raise ValueError("digest must match public payload")
    return provided


def _require_phase_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"unsupported public payload value: {value!r}")
