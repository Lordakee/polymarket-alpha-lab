"""Pure Phase 1 market depth decay forecast report for supplied probabilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from re import Pattern, compile


__all__ = (
    "ProbabilityEventMarketDepthDecayForecastPayload",
    "ProbabilityEventMarketDepthDecayForecastReport",
    "build_probability_event_market_depth_decay_forecast_report",
    "probability_event_market_depth_decay_forecast_payload_digest",
)


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

STABLE = "stable"
WATCH = "watch"
BLOCKED = "blocked"
STATUS_VALUES = (STABLE, WATCH, BLOCKED)

DEPTH_GAP_WATCH = Decimal("0.100000")
DEPTH_GAP_BLOCK = Decimal("0.300000")
DECAY_WATCH = Decimal("0.100000")
DECAY_BLOCK = Decimal("0.250000")
SPREAD_WATCH = Decimal("0.050000")
SPREAD_BLOCK = Decimal("0.150000")
CLOSE_HOURS_WATCH = Decimal("24.000000")
CLOSE_HOURS_BLOCK = Decimal("6.000000")

PAYLOAD_KEYS = (
    "current_depth_probability",
    "historical_depth_probability",
    "depth_decay_probability",
    "spread_probability",
    "market_close_hours",
    "depth_decay_status",
    "forecast_depth_probability",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
REASON_CODES = (
    "current_depth_below_historical_watch",
    "current_depth_below_historical_block",
    "depth_decay_probability_watch",
    "depth_decay_probability_block",
    "spread_probability_watch",
    "spread_probability_block",
    "market_close_hours_watch",
    "market_close_hours_block",
    "depth_decay_forecast_stable",
)
NEXT_STEPS = {
    STABLE: "continue_manual_market_depth_monitoring",
    WATCH: "review_market_depth_decay_forecast_manually",
    BLOCKED: "pause_and_escalate_market_depth_review",
}


class ProbabilityEventMarketDepthDecayForecastPayload(dict[str, object]):
    """Immutable public payload dict."""

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
class ProbabilityEventMarketDepthDecayForecastReport:
    current_depth_probability: Decimal
    historical_depth_probability: Decimal
    depth_decay_probability: Decimal
    spread_probability: Decimal
    market_close_hours: Decimal
    depth_decay_status: str = ""
    forecast_depth_probability: Decimal = Decimal("-1.000000")
    reason_codes: tuple[str, ...] = ()
    manual_next_step: str = ""
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventMarketDepthDecayForecastReport:
            raise TypeError(
                "ProbabilityEventMarketDepthDecayForecastReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventMarketDepthDecayForecastReport:
            raise ValueError(
                "report must be exactly "
                "ProbabilityEventMarketDepthDecayForecastReport",
            )
        object.__setattr__(
            self,
            "current_depth_probability",
            _require_probability_decimal(
                "current_depth_probability",
                self.current_depth_probability,
            ),
        )
        object.__setattr__(
            self,
            "historical_depth_probability",
            _require_probability_decimal(
                "historical_depth_probability",
                self.historical_depth_probability,
            ),
        )
        object.__setattr__(
            self,
            "depth_decay_probability",
            _require_probability_decimal(
                "depth_decay_probability",
                self.depth_decay_probability,
            ),
        )
        object.__setattr__(
            self,
            "spread_probability",
            _require_probability_decimal("spread_probability", self.spread_probability),
        )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_nonnegative_decimal("market_close_hours", self.market_close_hours),
        )
        _require_hard_flags(self)

        forecast_depth_probability = _forecast_depth_probability(self)
        if self.forecast_depth_probability == Decimal("-1.000000"):
            object.__setattr__(
                self,
                "forecast_depth_probability",
                forecast_depth_probability,
            )
        else:
            object.__setattr__(
                self,
                "forecast_depth_probability",
                _require_probability_decimal(
                    "forecast_depth_probability",
                    self.forecast_depth_probability,
                ),
            )
            if self.forecast_depth_probability != forecast_depth_probability:
                raise ValueError("forecast_depth_probability must match inputs")

        reason_codes = _reason_codes(self)
        if self.reason_codes == ():
            object.__setattr__(self, "reason_codes", reason_codes)
        else:
            normalized_reasons = _normalize_reason_codes(self.reason_codes)
            if normalized_reasons != reason_codes:
                raise ValueError("reason_codes must match inputs")
            object.__setattr__(self, "reason_codes", normalized_reasons)

        depth_decay_status = _depth_decay_status(self.reason_codes)
        if self.depth_decay_status == "":
            object.__setattr__(self, "depth_decay_status", depth_decay_status)
        elif self.depth_decay_status != depth_decay_status:
            raise ValueError("depth_decay_status must match inputs")
        elif self.depth_decay_status not in STATUS_VALUES:
            raise ValueError("depth_decay_status must be stable, watch, or blocked")

        manual_next_step = NEXT_STEPS[self.depth_decay_status]
        if self.manual_next_step == "":
            object.__setattr__(self, "manual_next_step", manual_next_step)
        elif self.manual_next_step != manual_next_step:
            raise ValueError("manual_next_step must match status")
        else:
            _require_public_code("manual_next_step", self.manual_next_step)

        payload_digest = _payload_digest(_payload_items(self, digest=""))
        if self.payload_digest == "":
            object.__setattr__(self, "payload_digest", payload_digest)
        elif self.payload_digest != payload_digest:
            raise ValueError("payload_digest must match public payload")
        else:
            _require_digest("payload_digest", self.payload_digest)

    @property
    def public_payload(self) -> ProbabilityEventMarketDepthDecayForecastPayload:
        payload = ProbabilityEventMarketDepthDecayForecastPayload(
            _payload_items(self, digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_market_depth_decay_forecast_report(
    *,
    current_depth_probability: Decimal,
    historical_depth_probability: Decimal,
    depth_decay_probability: Decimal,
    spread_probability: Decimal,
    market_close_hours: Decimal,
) -> ProbabilityEventMarketDepthDecayForecastReport:
    return ProbabilityEventMarketDepthDecayForecastReport(
        current_depth_probability=current_depth_probability,
        historical_depth_probability=historical_depth_probability,
        depth_decay_probability=depth_decay_probability,
        spread_probability=spread_probability,
        market_close_hours=market_close_hours,
    )


def probability_event_market_depth_decay_forecast_payload_digest(
    payload: ProbabilityEventMarketDepthDecayForecastReport | Mapping[str, object],
) -> str:
    if type(payload) is ProbabilityEventMarketDepthDecayForecastReport:
        public_payload = payload.public_payload
    elif isinstance(payload, Mapping):
        public_payload = dict(payload)
    else:
        raise ValueError("payload must be a report or mapping")
    _validate_public_payload(public_payload)
    without_payload_digest = dict(public_payload)
    without_payload_digest["payload_digest"] = ""
    digest = _payload_digest(without_payload_digest)
    if public_payload["payload_digest"] != digest:
        raise ValueError("payload_digest must match public payload")
    return digest


def _forecast_depth_probability(
    report: ProbabilityEventMarketDepthDecayForecastReport,
) -> Decimal:
    decay_adjustment = (
        report.depth_decay_probability
        if report.depth_decay_probability >= DECAY_WATCH
        else ZERO
    )
    return _clamp_probability(
        report.current_depth_probability
        - decay_adjustment
        - (report.spread_probability / Decimal("2.000000")),
    )


def _reason_codes(
    report: ProbabilityEventMarketDepthDecayForecastReport,
) -> tuple[str, ...]:
    depth_gap = _quantize(
        report.historical_depth_probability - report.current_depth_probability,
    )
    reasons: list[str] = []
    if depth_gap >= DEPTH_GAP_BLOCK:
        reasons.append("current_depth_below_historical_block")
    elif depth_gap >= DEPTH_GAP_WATCH:
        reasons.append("current_depth_below_historical_watch")
    if report.depth_decay_probability >= DECAY_BLOCK:
        reasons.append("depth_decay_probability_block")
    elif report.depth_decay_probability >= DECAY_WATCH:
        reasons.append("depth_decay_probability_watch")
    if report.spread_probability >= SPREAD_BLOCK:
        reasons.append("spread_probability_block")
    elif report.spread_probability >= SPREAD_WATCH:
        reasons.append("spread_probability_watch")
    if report.market_close_hours <= CLOSE_HOURS_BLOCK:
        reasons.append("market_close_hours_block")
    elif report.market_close_hours <= CLOSE_HOURS_WATCH:
        reasons.append("market_close_hours_watch")
    if not reasons:
        reasons.append("depth_decay_forecast_stable")
    return tuple(reasons)


def _depth_decay_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCKED
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH
    return STABLE


def _payload_items(
    report: ProbabilityEventMarketDepthDecayForecastReport,
    *,
    digest: str,
) -> dict[str, object]:
    return {
        "current_depth_probability": _decimal_text(report.current_depth_probability),
        "historical_depth_probability": _decimal_text(report.historical_depth_probability),
        "depth_decay_probability": _decimal_text(report.depth_decay_probability),
        "spread_probability": _decimal_text(report.spread_probability),
        "market_close_hours": _decimal_text(report.market_close_hours),
        "depth_decay_status": report.depth_decay_status,
        "forecast_depth_probability": _decimal_text(report.forecast_depth_probability),
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "payload_digest": digest,
    }


def _validate_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical depth decay forecast schema")
    for field_name in (
        "current_depth_probability",
        "historical_depth_probability",
        "depth_decay_probability",
        "spread_probability",
        "market_close_hours",
        "forecast_depth_probability",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if field_name == "market_close_hours":
            _require_nonnegative_decimal(field_name, Decimal(value))
        else:
            _require_probability_decimal(field_name, Decimal(value))
    _require_status(payload["depth_decay_status"])
    _normalize_reason_codes(payload["reason_codes"])
    _require_public_code("manual_next_step", payload["manual_next_step"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    digest = payload["payload_digest"]
    _require_digest("payload_digest", digest)
    digest_input = dict(payload)
    digest_input["payload_digest"] = ""
    if digest != _payload_digest(digest_input):
        raise ValueError("payload_digest must match public payload")
    return payload


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError("depth_decay_status must be supported")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(_quantize(value), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if type(value) is tuple:
        return list(value)
    raise TypeError(f"unsupported public payload value: {value!r}")
