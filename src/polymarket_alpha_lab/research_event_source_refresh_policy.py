"""Pure report-only event source refresh policy reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "ResearchEventSourceRefreshPolicyInput",
    "ResearchEventSourceRefreshPolicyResult",
    "evaluate_research_event_source_refresh_policy",
    "research_event_source_refresh_policy_payload",
)


REFRESH_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
HALF = Decimal("0.500000")
IMMINENT_SETTLEMENT_MINUTES = Decimal("60.000000")
NEAR_SETTLEMENT_MINUTES = Decimal("240.000000")
WATCH_CONFLICT_SCORE = Decimal("0.350000")
HIGH_CONFLICT_SCORE = Decimal("0.700000")
LOW_SOURCE_RELIABILITY = Decimal("0.600000")
HIGH_STALE_EVIDENCE_SENSITIVITY = Decimal("0.700000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DOMAIN_REFRESH_INTERVALS = {
    "crypto": Decimal("15.000000"),
    "sports": Decimal("30.000000"),
    "macro": Decimal("45.000000"),
    "politics": Decimal("60.000000"),
    "corporate": Decimal("120.000000"),
    "legal": Decimal("240.000000"),
}
EVENT_DOMAINS = tuple(DOMAIN_REFRESH_INTERVALS.keys())
POLICY_STATUSES = ("pass", "watch", "block")
REFRESH_ACTIONS = (
    "keep_domain_cadence",
    "refresh_before_research_use",
    "pause_until_source_refresh",
)
SENSITIVE_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "bearer ",
    "://",
    "@",
)


@dataclass(frozen=True)
class ResearchEventSourceRefreshPolicyInput:
    event_domain: str
    time_to_settlement_minutes: Decimal
    evidence_age_minutes: Decimal
    source_conflict_score: Decimal
    source_reliability: Decimal
    stale_evidence_sensitivity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_event_domain(self.event_domain)
        for field_name in ("time_to_settlement_minutes", "evidence_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_conflict_score",
            "source_reliability",
            "stale_evidence_sensitivity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class ResearchEventSourceRefreshPolicyResult:
    event_domain: str
    time_to_settlement_minutes: Decimal
    evidence_age_minutes: Decimal
    source_conflict_score: Decimal
    source_reliability: Decimal
    stale_evidence_sensitivity: Decimal
    domain_refresh_interval_minutes: Decimal
    settlement_refresh_interval_minutes: Decimal
    required_refresh_interval_minutes: Decimal
    evidence_stale_ratio: Decimal
    policy_status: str
    refresh_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_event_domain(self.event_domain)
        for field_name in (
            "time_to_settlement_minutes",
            "evidence_age_minutes",
            "domain_refresh_interval_minutes",
            "settlement_refresh_interval_minutes",
            "required_refresh_interval_minutes",
            "evidence_stale_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_conflict_score",
            "source_reliability",
            "stale_evidence_sensitivity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.domain_refresh_interval_minutes <= ZERO:
            raise ValueError("domain_refresh_interval_minutes must be positive")
        if self.settlement_refresh_interval_minutes <= ZERO:
            raise ValueError("settlement_refresh_interval_minutes must be positive")
        if self.required_refresh_interval_minutes <= ZERO:
            raise ValueError("required_refresh_interval_minutes must be positive")
        _require_member("policy_status", self.policy_status, POLICY_STATUSES)
        _require_member("refresh_action", self.refresh_action, REFRESH_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_source_refresh_policy_payload(self)


def evaluate_research_event_source_refresh_policy(
    event_source: ResearchEventSourceRefreshPolicyInput,
) -> ResearchEventSourceRefreshPolicyResult:
    if type(event_source) is not ResearchEventSourceRefreshPolicyInput:
        raise ValueError(
            "event_source must be a ResearchEventSourceRefreshPolicyInput",
        )
    _require_safety_flags("event_source", event_source)

    domain_refresh_interval = DOMAIN_REFRESH_INTERVALS[event_source.event_domain]
    settlement_refresh_interval = _settlement_refresh_interval(
        event_source,
        domain_refresh_interval=domain_refresh_interval,
    )
    conflict_accelerated = event_source.source_conflict_score >= WATCH_CONFLICT_SCORE
    required_refresh_interval = settlement_refresh_interval
    if conflict_accelerated:
        required_refresh_interval = _quantize_decimal(
            "required_refresh_interval_minutes",
            settlement_refresh_interval * HALF,
        )
    evidence_stale_ratio = _evidence_stale_ratio(
        event_source.evidence_age_minutes,
        settlement_refresh_interval,
    )
    policy_status = _policy_status(
        event_source,
        evidence_stale_ratio=evidence_stale_ratio,
    )

    return ResearchEventSourceRefreshPolicyResult(
        event_domain=event_source.event_domain,
        time_to_settlement_minutes=event_source.time_to_settlement_minutes,
        evidence_age_minutes=event_source.evidence_age_minutes,
        source_conflict_score=event_source.source_conflict_score,
        source_reliability=event_source.source_reliability,
        stale_evidence_sensitivity=event_source.stale_evidence_sensitivity,
        domain_refresh_interval_minutes=domain_refresh_interval,
        settlement_refresh_interval_minutes=settlement_refresh_interval,
        required_refresh_interval_minutes=required_refresh_interval,
        evidence_stale_ratio=evidence_stale_ratio,
        policy_status=policy_status,
        refresh_action=_refresh_action(policy_status),
        reason_codes=_reason_codes(
            event_source,
            evidence_stale_ratio=evidence_stale_ratio,
            policy_status=policy_status,
        ),
    )


def research_event_source_refresh_policy_payload(
    result: ResearchEventSourceRefreshPolicyResult,
) -> dict[str, Any]:
    if type(result) is not ResearchEventSourceRefreshPolicyResult:
        raise ValueError("result must be a ResearchEventSourceRefreshPolicyResult")
    _require_safety_flags("result", result)
    return {
        "event_domain": result.event_domain,
        "time_to_settlement_minutes": _decimal_payload(
            result.time_to_settlement_minutes,
        ),
        "evidence_age_minutes": _decimal_payload(result.evidence_age_minutes),
        "source_conflict_score": _decimal_payload(result.source_conflict_score),
        "source_reliability": _decimal_payload(result.source_reliability),
        "stale_evidence_sensitivity": _decimal_payload(
            result.stale_evidence_sensitivity,
        ),
        "domain_refresh_interval_minutes": _decimal_payload(
            result.domain_refresh_interval_minutes,
        ),
        "settlement_refresh_interval_minutes": _decimal_payload(
            result.settlement_refresh_interval_minutes,
        ),
        "required_refresh_interval_minutes": _decimal_payload(
            result.required_refresh_interval_minutes,
        ),
        "evidence_stale_ratio": _decimal_payload(result.evidence_stale_ratio),
        "policy_status": result.policy_status,
        "refresh_action": result.refresh_action,
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _settlement_refresh_interval(
    event_source: ResearchEventSourceRefreshPolicyInput,
    *,
    domain_refresh_interval: Decimal,
) -> Decimal:
    if event_source.time_to_settlement_minutes <= IMMINENT_SETTLEMENT_MINUTES:
        with localcontext(DECIMAL_CONTEXT):
            return _quantize_decimal(
                "settlement_refresh_interval_minutes",
                domain_refresh_interval / Decimal("4.000000"),
            )
    if event_source.time_to_settlement_minutes <= NEAR_SETTLEMENT_MINUTES:
        with localcontext(DECIMAL_CONTEXT):
            return _quantize_decimal(
                "settlement_refresh_interval_minutes",
                domain_refresh_interval / TWO,
            )
    return domain_refresh_interval


def _evidence_stale_ratio(
    evidence_age_minutes: Decimal,
    settlement_refresh_interval: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            "evidence_stale_ratio",
            evidence_age_minutes / settlement_refresh_interval,
        )


def _policy_status(
    event_source: ResearchEventSourceRefreshPolicyInput,
    *,
    evidence_stale_ratio: Decimal,
) -> str:
    if _conflict_near_settlement_block(event_source):
        return "block"
    if (
        evidence_stale_ratio >= TWO
        and event_source.stale_evidence_sensitivity
        >= HIGH_STALE_EVIDENCE_SENSITIVITY
    ):
        return "block"
    if event_source.source_conflict_score >= WATCH_CONFLICT_SCORE:
        return "watch"
    if evidence_stale_ratio > ONE:
        return "watch"
    return "pass"


def _refresh_action(policy_status: str) -> str:
    if policy_status == "block":
        return "pause_until_source_refresh"
    if policy_status == "watch":
        return "refresh_before_research_use"
    return "keep_domain_cadence"


def _reason_codes(
    event_source: ResearchEventSourceRefreshPolicyInput,
    *,
    evidence_stale_ratio: Decimal,
    policy_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = [
        f"refresh_policy_{policy_status}",
        f"domain_{event_source.event_domain}_cadence",
    ]
    if event_source.time_to_settlement_minutes <= IMMINENT_SETTLEMENT_MINUTES:
        reason_codes.append("settlement_imminent")
    elif event_source.time_to_settlement_minutes <= NEAR_SETTLEMENT_MINUTES:
        reason_codes.append("settlement_near")
    if event_source.source_conflict_score >= HIGH_CONFLICT_SCORE:
        reason_codes.append("conflict_signal_high")
    elif event_source.source_conflict_score >= WATCH_CONFLICT_SCORE:
        reason_codes.append("conflict_signal_watch")
    if _conflict_near_settlement_block(event_source):
        reason_codes.append("conflict_near_settlement_block")
    if (
        evidence_stale_ratio >= TWO
        and event_source.stale_evidence_sensitivity
        >= HIGH_STALE_EVIDENCE_SENSITIVITY
    ):
        reason_codes.append("evidence_stale_block")
    elif evidence_stale_ratio > ONE:
        reason_codes.append("evidence_stale_watch")
    elif (
        policy_status == "pass"
        and event_source.source_conflict_score < WATCH_CONFLICT_SCORE
    ):
        reason_codes.append("evidence_within_refresh_window")
    if event_source.source_reliability <= LOW_SOURCE_RELIABILITY:
        reason_codes.append("source_reliability_low")
    if (
        event_source.stale_evidence_sensitivity
        >= HIGH_STALE_EVIDENCE_SENSITIVITY
    ):
        reason_codes.append("stale_evidence_sensitivity_high")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _conflict_near_settlement_block(
    event_source: ResearchEventSourceRefreshPolicyInput,
) -> bool:
    return (
        event_source.source_conflict_score >= HIGH_CONFLICT_SCORE
        and event_source.time_to_settlement_minutes <= IMMINENT_SETTLEMENT_MINUTES
    )


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(REFRESH_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(REFRESH_QUANTUM)


def _require_event_domain(value: object) -> None:
    _require_canonical_string("event_domain", value)
    if value not in EVENT_DOMAINS:
        raise ValueError("event_domain must be a known value")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")
