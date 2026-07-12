"""Read-only capital lockup readiness report for probability events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_CAPITAL_LOCKUP_READINESS_REPORT_VERSION",
    "ProbabilityEventCapitalLockupReadinessInput",
    "ProbabilityEventCapitalLockupReadinessReport",
    "build_probability_event_capital_lockup_readiness_report",
    "probability_event_capital_lockup_readiness_report_payload",
)


PROBABILITY_EVENT_CAPITAL_LOCKUP_READINESS_REPORT_VERSION = (
    "probability-event-capital-lockup-readiness-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
PASS_RESOLUTION_DAYS = Decimal("14.000000")
WATCH_RESOLUTION_DAYS = Decimal("30.000000")
PASS_CAPITAL_LOCKUP_PENALTY = Decimal("0.050000")
WATCH_CAPITAL_LOCKUP_PENALTY = Decimal("0.100000")
PASS_LIQUIDITY_EXIT_RISK = Decimal("0.250000")
WATCH_LIQUIDITY_EXIT_RISK = Decimal("0.500000")
PASS_SETTLEMENT_RISK = Decimal("0.100000")
WATCH_SETTLEMENT_RISK = Decimal("0.250000")
READINESS_STATUSES = ("pass", "watch", "blocked")
MANUAL_NEXT_STEPS = (
    "proceed_with_paper_review",
    "manual_review_lockup_terms_and_exit_depth",
    "do_not_allocate_capital_until_blockers_clear",
)
REASON_SEQUENCE = (
    "extended_resolution_block",
    "extended_resolution_watch",
    "negative_net_edge_after_lockup",
    "capital_lockup_penalty_block",
    "capital_lockup_penalty_watch",
    "liquidity_exit_risk_block",
    "liquidity_exit_risk_watch",
    "settlement_risk_block",
    "settlement_risk_watch",
    "capital_lockup_ready",
)
PAYLOAD_KEYS = (
    "config_version",
    "event_id",
    "market_slug",
    "readiness_status",
    "time_to_resolution_days",
    "expected_edge",
    "capital_lockup_penalty",
    "liquidity_exit_risk",
    "settlement_risk",
    "net_edge_after_lockup",
    "total_lockup_risk",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)


class ProbabilityEventCapitalLockupReadinessPublicPayload(dict[str, object]):
    """Immutable public payload for the capital lockup readiness report."""

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
class ProbabilityEventCapitalLockupReadinessInput:
    event_id: str
    market_slug: str
    time_to_resolution_days: Decimal
    expected_edge: Decimal
    capital_lockup_penalty: Decimal
    liquidity_exit_risk: Decimal
    settlement_risk: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventCapitalLockupReadinessInput:
            raise TypeError(
                "ProbabilityEventCapitalLockupReadinessInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventCapitalLockupReadinessInput:
            raise ValueError(
                "input must be exactly ProbabilityEventCapitalLockupReadinessInput",
            )
        object.__setattr__(self, "event_id", _require_public_identifier("event_id", self.event_id))
        object.__setattr__(
            self,
            "market_slug",
            _require_public_identifier("market_slug", self.market_slug),
        )
        for field_name in (
            "time_to_resolution_days",
            "capital_lockup_penalty",
            "liquidity_exit_risk",
            "settlement_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_edge",
            _require_decimal("expected_edge", self.expected_edge),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventCapitalLockupReadinessReport:
    config_version: str
    event_id: str
    market_slug: str
    readiness_status: str
    time_to_resolution_days: Decimal
    expected_edge: Decimal
    capital_lockup_penalty: Decimal
    liquidity_exit_risk: Decimal
    settlement_risk: Decimal
    net_edge_after_lockup: Decimal
    total_lockup_risk: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventCapitalLockupReadinessReport:
            raise TypeError(
                "ProbabilityEventCapitalLockupReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventCapitalLockupReadinessReport:
            raise ValueError(
                "report must be exactly ProbabilityEventCapitalLockupReadinessReport",
            )
        _require_config_version(self.config_version)
        object.__setattr__(self, "event_id", _require_public_identifier("event_id", self.event_id))
        object.__setattr__(
            self,
            "market_slug",
            _require_public_identifier("market_slug", self.market_slug),
        )
        _require_readiness_status(self.readiness_status)
        for field_name in (
            "time_to_resolution_days",
            "capital_lockup_penalty",
            "liquidity_exit_risk",
            "settlement_risk",
            "total_lockup_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("expected_edge", "net_edge_after_lockup"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags(self)
        _validate_report(self)

    @property
    def public_payload(self) -> ProbabilityEventCapitalLockupReadinessPublicPayload:
        payload = ProbabilityEventCapitalLockupReadinessPublicPayload(
            _payload_values(self),
        )
        _validate_payload(payload)
        return payload


def build_probability_event_capital_lockup_readiness_report(
    inputs: ProbabilityEventCapitalLockupReadinessInput,
) -> ProbabilityEventCapitalLockupReadinessReport:
    """Build a deterministic paper-only capital lockup readiness summary."""

    if type(inputs) is not ProbabilityEventCapitalLockupReadinessInput:
        raise ValueError(
            "inputs must be a ProbabilityEventCapitalLockupReadinessInput",
        )
    _require_hard_flags(inputs)
    net_edge_after_lockup = _quantize(inputs.expected_edge - inputs.capital_lockup_penalty)
    total_lockup_risk = _quantize(
        inputs.capital_lockup_penalty
        + inputs.liquidity_exit_risk
        + inputs.settlement_risk,
    )
    reason_codes = _reason_codes(
        time_to_resolution_days=inputs.time_to_resolution_days,
        net_edge_after_lockup=net_edge_after_lockup,
        capital_lockup_penalty=inputs.capital_lockup_penalty,
        liquidity_exit_risk=inputs.liquidity_exit_risk,
        settlement_risk=inputs.settlement_risk,
    )
    readiness_status = _readiness_status(reason_codes)
    return ProbabilityEventCapitalLockupReadinessReport(
        config_version=PROBABILITY_EVENT_CAPITAL_LOCKUP_READINESS_REPORT_VERSION,
        event_id=inputs.event_id,
        market_slug=inputs.market_slug,
        readiness_status=readiness_status,
        time_to_resolution_days=inputs.time_to_resolution_days,
        expected_edge=inputs.expected_edge,
        capital_lockup_penalty=inputs.capital_lockup_penalty,
        liquidity_exit_risk=inputs.liquidity_exit_risk,
        settlement_risk=inputs.settlement_risk,
        net_edge_after_lockup=net_edge_after_lockup,
        total_lockup_risk=total_lockup_risk,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(readiness_status),
    )


def probability_event_capital_lockup_readiness_report_payload(
    report: ProbabilityEventCapitalLockupReadinessReport,
) -> ProbabilityEventCapitalLockupReadinessPublicPayload:
    if type(report) is not ProbabilityEventCapitalLockupReadinessReport:
        raise ValueError("report must be a ProbabilityEventCapitalLockupReadinessReport")
    _require_hard_flags(report)
    _validate_report(report)
    return report.public_payload


def _validate_report(report: ProbabilityEventCapitalLockupReadinessReport) -> None:
    net_edge_after_lockup = _quantize(report.expected_edge - report.capital_lockup_penalty)
    total_lockup_risk = _quantize(
        report.capital_lockup_penalty
        + report.liquidity_exit_risk
        + report.settlement_risk,
    )
    reason_codes = _reason_codes(
        time_to_resolution_days=report.time_to_resolution_days,
        net_edge_after_lockup=net_edge_after_lockup,
        capital_lockup_penalty=report.capital_lockup_penalty,
        liquidity_exit_risk=report.liquidity_exit_risk,
        settlement_risk=report.settlement_risk,
    )
    readiness_status = _readiness_status(reason_codes)
    if report.net_edge_after_lockup != net_edge_after_lockup:
        raise ValueError("net_edge_after_lockup must match expected_edge less capital_lockup_penalty")
    if report.total_lockup_risk != total_lockup_risk:
        raise ValueError("total_lockup_risk must match canonical inputs")
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match capital lockup inputs")
    if report.readiness_status != readiness_status:
        raise ValueError("readiness_status must match reason codes")
    if report.manual_next_step != _manual_next_step(readiness_status):
        raise ValueError("manual_next_step must match readiness_status")


def _validate_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match capital lockup readiness schema")
    _require_config_version(payload["config_version"])
    _require_public_identifier("event_id", payload["event_id"])
    _require_public_identifier("market_slug", payload["market_slug"])
    _require_readiness_status(payload["readiness_status"])
    for field_name in (
        "time_to_resolution_days",
        "capital_lockup_penalty",
        "liquidity_exit_risk",
        "settlement_risk",
        "total_lockup_risk",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _require_nonnegative_decimal(field_name, Decimal(value))
    for field_name in ("expected_edge", "net_edge_after_lockup"):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _require_decimal(field_name, Decimal(value))
    _normalize_reason_codes(payload["reason_codes"])
    _require_manual_next_step(payload["manual_next_step"])
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = payload[field_name]
        if flag is not True:
            raise ValueError(f"{field_name} must be True")
    return payload


def _payload_values(
    report: ProbabilityEventCapitalLockupReadinessReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "event_id": report.event_id,
        "market_slug": report.market_slug,
        "readiness_status": report.readiness_status,
        "time_to_resolution_days": _decimal_text(report.time_to_resolution_days),
        "expected_edge": _decimal_text(report.expected_edge),
        "capital_lockup_penalty": _decimal_text(report.capital_lockup_penalty),
        "liquidity_exit_risk": _decimal_text(report.liquidity_exit_risk),
        "settlement_risk": _decimal_text(report.settlement_risk),
        "net_edge_after_lockup": _decimal_text(report.net_edge_after_lockup),
        "total_lockup_risk": _decimal_text(report.total_lockup_risk),
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _reason_codes(
    *,
    time_to_resolution_days: Decimal,
    net_edge_after_lockup: Decimal,
    capital_lockup_penalty: Decimal,
    liquidity_exit_risk: Decimal,
    settlement_risk: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if time_to_resolution_days > WATCH_RESOLUTION_DAYS:
        reasons.append("extended_resolution_block")
    elif time_to_resolution_days > PASS_RESOLUTION_DAYS:
        reasons.append("extended_resolution_watch")
    if net_edge_after_lockup <= ZERO:
        reasons.append("negative_net_edge_after_lockup")
    if capital_lockup_penalty > WATCH_CAPITAL_LOCKUP_PENALTY:
        reasons.append("capital_lockup_penalty_block")
    elif capital_lockup_penalty > PASS_CAPITAL_LOCKUP_PENALTY:
        reasons.append("capital_lockup_penalty_watch")
    if liquidity_exit_risk > WATCH_LIQUIDITY_EXIT_RISK:
        reasons.append("liquidity_exit_risk_block")
    elif liquidity_exit_risk > PASS_LIQUIDITY_EXIT_RISK:
        reasons.append("liquidity_exit_risk_watch")
    if settlement_risk > WATCH_SETTLEMENT_RISK:
        reasons.append("settlement_risk_block")
    elif settlement_risk > PASS_SETTLEMENT_RISK:
        reasons.append("settlement_risk_watch")
    if not reasons:
        reasons.append("capital_lockup_ready")
    return tuple(reason for reason in REASON_SEQUENCE if reason in reasons)


def _readiness_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "blocked"
    if "negative_net_edge_after_lockup" in reason_codes:
        return "blocked"
    if reason_codes != ("capital_lockup_ready",):
        return "watch"
    return "pass"


def _manual_next_step(readiness_status: str) -> str:
    if readiness_status == "pass":
        return "proceed_with_paper_review"
    if readiness_status == "watch":
        return "manual_review_lockup_terms_and_exit_depth"
    if readiness_status == "blocked":
        return "do_not_allocate_capital_until_blockers_clear"
    raise ValueError("readiness_status must be supported")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_CAPITAL_LOCKUP_READINESS_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be text")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if normalized != value:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _require_readiness_status(value: object) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError("readiness_status must be supported")


def _require_manual_next_step(value: object) -> None:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be supported")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_SEQUENCE:
            raise ValueError("reason_codes must be supported")
    expected = tuple(reason_code for reason_code in REASON_SEQUENCE if reason_code in set(value))
    if value != expected:
        raise ValueError("reason_codes must be sorted and unique")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


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


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(_quantize(value), "f")
