"""Read-only Kelly bound readiness report for probability event sizing."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from re import Pattern, compile
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_COST_ADJUSTED_KELLY_BOUND_READINESS_REPORT_VERSION",
    "ProbabilityEventCostAdjustedKellyBoundReadinessInput",
    "ProbabilityEventCostAdjustedKellyBoundReadinessReport",
    "build_probability_event_cost_adjusted_kelly_bound_readiness_report",
    "probability_event_cost_adjusted_kelly_bound_readiness_report_payload",
    "probability_event_cost_adjusted_kelly_bound_readiness_report_digest",
)


PROBABILITY_EVENT_COST_ADJUSTED_KELLY_BOUND_READINESS_REPORT_VERSION = (
    "probability-event-cost-adjusted-kelly-bound-readiness-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_BOUNDARY = Decimal("0.050000")
DIGEST_RE: Pattern[str] = compile(r"^[0-9a-f]{64}$")

STATUS_VALUES = ("ready", "watch", "blocked")
MANUAL_NEXT_STEPS = (
    "review_manual_position_boundary",
    "review_small_manual_boundary_before_any_paper_entry",
    "do_not_size_position_manually_until_edge_improves",
)
REASON_CODES = (
    "kelly_bound_positive_cost_adjusted_edge",
    "kelly_bound_manual_cap_applied",
    "kelly_bound_below_manual_cap",
    "kelly_bound_watch_small_boundary",
    "kelly_bound_cost_uncertainty_exhaust_edge",
    "kelly_bound_zero_fraction_boundary",
    "kelly_bound_manual_review_required",
)
PAYLOAD_KEYS = (
    "config_version",
    "kelly_bound_status",
    "win_probability",
    "market_probability",
    "net_edge_probability",
    "cost_probability",
    "uncertainty_probability",
    "manual_fraction_cap_probability",
    "cost_adjusted_fraction_probability",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class ProbabilityEventCostAdjustedKellyBoundReadinessPublicPayload(dict[str, object]):
    """Immutable public payload for the Kelly bound readiness report."""

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
class ProbabilityEventCostAdjustedKellyBoundReadinessInput:
    win_probability: Decimal
    market_probability: Decimal
    net_edge_probability: Decimal
    cost_probability: Decimal
    uncertainty_probability: Decimal
    manual_fraction_cap_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventCostAdjustedKellyBoundReadinessInput:
            raise TypeError(
                "ProbabilityEventCostAdjustedKellyBoundReadinessInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventCostAdjustedKellyBoundReadinessInput:
            raise ValueError(
                "input must be exactly ProbabilityEventCostAdjustedKellyBoundReadinessInput",
            )
        for field_name in (
            "win_probability",
            "market_probability",
            "net_edge_probability",
            "cost_probability",
            "uncertainty_probability",
            "manual_fraction_cap_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.net_edge_probability != self.win_probability - self.market_probability:
            raise ValueError("net_edge_probability must match win minus market")
        if self.manual_fraction_cap_probability == ZERO:
            raise ValueError("manual_fraction_cap_probability must be positive")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventCostAdjustedKellyBoundReadinessReport:
    config_version: str
    kelly_bound_status: str
    win_probability: Decimal
    market_probability: Decimal
    net_edge_probability: Decimal
    cost_probability: Decimal
    uncertainty_probability: Decimal
    manual_fraction_cap_probability: Decimal
    cost_adjusted_fraction_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventCostAdjustedKellyBoundReadinessReport:
            raise TypeError(
                "ProbabilityEventCostAdjustedKellyBoundReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventCostAdjustedKellyBoundReadinessReport:
            raise ValueError(
                "report must be exactly ProbabilityEventCostAdjustedKellyBoundReadinessReport",
            )
        _require_config_version(self.config_version)
        _require_status(self.kelly_bound_status)
        for field_name in (
            "win_probability",
            "market_probability",
            "net_edge_probability",
            "cost_probability",
            "uncertainty_probability",
            "manual_fraction_cap_probability",
            "cost_adjusted_fraction_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(
        self,
    ) -> ProbabilityEventCostAdjustedKellyBoundReadinessPublicPayload:
        payload = ProbabilityEventCostAdjustedKellyBoundReadinessPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_cost_adjusted_kelly_bound_readiness_report(
    inputs: ProbabilityEventCostAdjustedKellyBoundReadinessInput,
) -> ProbabilityEventCostAdjustedKellyBoundReadinessReport:
    """Build a deterministic report for manual Kelly boundary review."""

    if type(inputs) is not ProbabilityEventCostAdjustedKellyBoundReadinessInput:
        raise ValueError(
            "inputs must be a ProbabilityEventCostAdjustedKellyBoundReadinessInput",
        )
    _require_hard_flags(inputs)
    cost_adjusted_edge = _cost_adjusted_edge(inputs)
    raw_fraction = _positive_or_zero(cost_adjusted_edge)
    fraction = _min_decimal(raw_fraction, inputs.manual_fraction_cap_probability)
    status = _status(raw_fraction, fraction, inputs.manual_fraction_cap_probability)
    reason_codes = _reason_codes(
        raw_fraction,
        fraction,
        inputs.manual_fraction_cap_probability,
    )
    manual_next_step = _manual_next_step(status)
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_COST_ADJUSTED_KELLY_BOUND_READINESS_REPORT_VERSION,
        "kelly_bound_status": status,
        "win_probability": inputs.win_probability,
        "market_probability": inputs.market_probability,
        "net_edge_probability": inputs.net_edge_probability,
        "cost_probability": inputs.cost_probability,
        "uncertainty_probability": inputs.uncertainty_probability,
        "manual_fraction_cap_probability": inputs.manual_fraction_cap_probability,
        "cost_adjusted_fraction_probability": fraction,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventCostAdjustedKellyBoundReadinessReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_cost_adjusted_kelly_bound_readiness_report_payload(
    report: ProbabilityEventCostAdjustedKellyBoundReadinessReport,
) -> ProbabilityEventCostAdjustedKellyBoundReadinessPublicPayload:
    if type(report) is not ProbabilityEventCostAdjustedKellyBoundReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventCostAdjustedKellyBoundReadinessReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = (
        probability_event_cost_adjusted_kelly_bound_readiness_report_digest(report)
    )
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match report payload")
    return report.public_payload


def probability_event_cost_adjusted_kelly_bound_readiness_report_digest(
    report: ProbabilityEventCostAdjustedKellyBoundReadinessReport,
) -> str:
    if type(report) is not ProbabilityEventCostAdjustedKellyBoundReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventCostAdjustedKellyBoundReadinessReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, payload_digest=""))


def _validate_report(
    report: ProbabilityEventCostAdjustedKellyBoundReadinessReport,
) -> None:
    if report.net_edge_probability != report.win_probability - report.market_probability:
        raise ValueError("net_edge_probability must match win minus market")
    if report.manual_fraction_cap_probability == ZERO:
        raise ValueError("manual_fraction_cap_probability must be positive")
    cost_adjusted_edge = _cost_adjusted_edge(report)
    raw_fraction = _positive_or_zero(cost_adjusted_edge)
    expected_fraction = _min_decimal(raw_fraction, report.manual_fraction_cap_probability)
    expected_status = _status(
        raw_fraction,
        expected_fraction,
        report.manual_fraction_cap_probability,
    )
    if report.cost_adjusted_fraction_probability != expected_fraction:
        raise ValueError("cost_adjusted_fraction_probability must match input fields")
    if report.kelly_bound_status != expected_status:
        raise ValueError("kelly_bound_status must match boundary fields")
    if report.reason_codes != _reason_codes(
        raw_fraction,
        expected_fraction,
        report.manual_fraction_cap_probability,
    ):
        raise ValueError("reason_codes must match boundary fields")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match kelly_bound_status")


def _validate_public_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical Kelly bound schema")
    _require_config_version(payload["config_version"])
    _require_status(payload["kelly_bound_status"])
    for field_name in (
        "win_probability",
        "market_probability",
        "net_edge_probability",
        "cost_probability",
        "uncertainty_probability",
        "manual_fraction_cap_probability",
        "cost_adjusted_fraction_probability",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _require_probability(field_name, Decimal(value))
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    _normalize_reason_codes(reason_codes)
    _require_manual_next_step(payload["manual_next_step"])
    for flag_name in ("paper_only", "report_only", "readonly"):
        _require_bool(flag_name, payload[flag_name])
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    digest = payload["payload_digest"]
    _require_digest("payload_digest", digest)
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    if digest != _payload_digest(unsigned):
        raise ValueError("payload_digest must match public payload")
    return payload


def _payload_items(
    report: ProbabilityEventCostAdjustedKellyBoundReadinessReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), payload_digest=payload_digest)


def _report_values_without_digest(
    report: ProbabilityEventCostAdjustedKellyBoundReadinessReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "kelly_bound_status": report.kelly_bound_status,
        "win_probability": report.win_probability,
        "market_probability": report.market_probability,
        "net_edge_probability": report.net_edge_probability,
        "cost_probability": report.cost_probability,
        "uncertainty_probability": report.uncertainty_probability,
        "manual_fraction_cap_probability": report.manual_fraction_cap_probability,
        "cost_adjusted_fraction_probability": report.cost_adjusted_fraction_probability,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "kelly_bound_status": values["kelly_bound_status"],
        "win_probability": _decimal_text(values["win_probability"]),
        "market_probability": _decimal_text(values["market_probability"]),
        "net_edge_probability": _decimal_text(values["net_edge_probability"]),
        "cost_probability": _decimal_text(values["cost_probability"]),
        "uncertainty_probability": _decimal_text(values["uncertainty_probability"]),
        "manual_fraction_cap_probability": _decimal_text(
            values["manual_fraction_cap_probability"],
        ),
        "cost_adjusted_fraction_probability": _decimal_text(
            values["cost_adjusted_fraction_probability"],
        ),
        "reason_codes": values["reason_codes"],
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _cost_adjusted_edge(value: object) -> Decimal:
    return (
        getattr(value, "net_edge_probability")
        - getattr(value, "cost_probability")
        - getattr(value, "uncertainty_probability")
    )


def _positive_or_zero(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    return _require_probability("cost_adjusted_fraction_probability", value)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left <= right:
        return left
    return right


def _status(
    raw_fraction: Decimal,
    fraction: Decimal,
    manual_fraction_cap_probability: Decimal,
) -> str:
    if raw_fraction == ZERO:
        return "blocked"
    if raw_fraction <= WATCH_BOUNDARY and fraction < manual_fraction_cap_probability:
        return "watch"
    return "ready"


def _reason_codes(
    raw_fraction: Decimal,
    fraction: Decimal,
    manual_fraction_cap_probability: Decimal,
) -> tuple[str, ...]:
    values: list[str] = []
    if raw_fraction == ZERO:
        values.extend(
            (
                "kelly_bound_cost_uncertainty_exhaust_edge",
                "kelly_bound_zero_fraction_boundary",
            ),
        )
    else:
        values.append("kelly_bound_positive_cost_adjusted_edge")
        if raw_fraction > manual_fraction_cap_probability:
            values.append("kelly_bound_manual_cap_applied")
        elif fraction < manual_fraction_cap_probability:
            values.append("kelly_bound_below_manual_cap")
        if raw_fraction <= WATCH_BOUNDARY and fraction < manual_fraction_cap_probability:
            values.append("kelly_bound_watch_small_boundary")
    values.append("kelly_bound_manual_review_required")
    return tuple(values)


def _manual_next_step(status: str) -> str:
    if status == "blocked":
        return "do_not_size_position_manually_until_edge_improves"
    if status == "watch":
        return "review_small_manual_boundary_before_any_paper_entry"
    if status == "ready":
        return "review_manual_position_boundary"
    raise ValueError("kelly_bound_status must be supported")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_COST_ADJUSTED_KELLY_BOUND_READINESS_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError("kelly_bound_status must be supported")


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be supported")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(value.quantize(QUANTUM, rounding=ROUND_HALF_UP), "f")


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
