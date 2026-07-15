"""Read-only unresolved blocker aging report for probability events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping


__all__ = (
    "PROBABILITY_EVENT_UNRESOLVED_BLOCKER_AGING_REPORT_VERSION",
    "ProbabilityEventUnresolvedBlockerAgingInput",
    "ProbabilityEventUnresolvedBlockerAgingReport",
    "build_probability_event_unresolved_blocker_aging_report",
    "probability_event_unresolved_blocker_aging_report_payload",
)


PROBABILITY_EVENT_UNRESOLVED_BLOCKER_AGING_REPORT_VERSION = (
    "probability-event-unresolved-blocker-aging-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
BLOCKER_AGE_WATCH_HOURS = Decimal("12.000000")
BLOCKER_AGE_BLOCK_HOURS = Decimal("24.000000")
MARKET_CLOSE_WATCH_HOURS = Decimal("24.000000")
MARKET_CLOSE_BLOCK_HOURS = Decimal("6.000000")
RETRY_COUNT_WATCH = Decimal("1.000000")
RETRY_COUNT_BLOCK = Decimal("4.000000")
AGING_STATUSES = ("clear", "watch", "blocked")
MANUAL_NEXT_STEPS = (
    "continue_paper_monitoring",
    "refresh_blocker_owner_and_retry_plan",
    "escalate_unresolved_blockers_before_paper_review",
)
REASON_SEQUENCE = (
    "blocker_age_block",
    "blocker_age_watch",
    "market_close_block_window",
    "market_close_watch_window",
    "owner_unassigned_block",
    "retry_count_block",
    "retry_count_watch",
    "no_unresolved_blockers",
)
PAYLOAD_KEYS = (
    "config_version",
    "blocker_aging_status",
    "blocker_count",
    "oldest_blocker_age_hours",
    "market_close_hours",
    "owner_assigned",
    "retry_count",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)


class ProbabilityEventUnresolvedBlockerAgingPublicPayload(dict[str, object]):
    """Immutable public payload for the unresolved blocker aging report."""

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
class ProbabilityEventUnresolvedBlockerAgingInput:
    blocker_count: Decimal
    oldest_blocker_age_hours: Decimal
    market_close_hours: Decimal
    owner_assigned: bool
    retry_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventUnresolvedBlockerAgingInput:
            raise TypeError(
                "ProbabilityEventUnresolvedBlockerAgingInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventUnresolvedBlockerAgingInput:
            raise ValueError(
                "input must be exactly ProbabilityEventUnresolvedBlockerAgingInput",
            )
        object.__setattr__(
            self,
            "blocker_count",
            _require_nonnegative_integral_decimal(
                "blocker_count",
                self.blocker_count,
            ),
        )
        for field_name in ("oldest_blocker_age_hours", "market_close_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("owner_assigned", self.owner_assigned)
        object.__setattr__(
            self,
            "retry_count",
            _require_nonnegative_integral_decimal("retry_count", self.retry_count),
        )
        _require_hard_flags(self)
        _validate_input_shape(self)


@dataclass(frozen=True)
class ProbabilityEventUnresolvedBlockerAgingReport:
    config_version: str
    blocker_aging_status: str
    blocker_count: Decimal
    oldest_blocker_age_hours: Decimal
    market_close_hours: Decimal
    owner_assigned: bool
    retry_count: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventUnresolvedBlockerAgingReport:
            raise TypeError(
                "ProbabilityEventUnresolvedBlockerAgingReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventUnresolvedBlockerAgingReport:
            raise ValueError(
                "report must be exactly ProbabilityEventUnresolvedBlockerAgingReport",
            )
        _require_config_version(self.config_version)
        _require_aging_status(self.blocker_aging_status)
        object.__setattr__(
            self,
            "blocker_count",
            _require_nonnegative_integral_decimal(
                "blocker_count",
                self.blocker_count,
            ),
        )
        for field_name in ("oldest_blocker_age_hours", "market_close_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("owner_assigned", self.owner_assigned)
        object.__setattr__(
            self,
            "retry_count",
            _require_nonnegative_integral_decimal("retry_count", self.retry_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step(self.manual_next_step)
        _require_hard_flags(self)
        _validate_report(self)

    @property
    def public_payload(self) -> ProbabilityEventUnresolvedBlockerAgingPublicPayload:
        payload = ProbabilityEventUnresolvedBlockerAgingPublicPayload(
            _payload_values(self),
        )
        _validate_payload(payload)
        return payload


def build_probability_event_unresolved_blocker_aging_report(
    inputs: ProbabilityEventUnresolvedBlockerAgingInput,
) -> ProbabilityEventUnresolvedBlockerAgingReport:
    """Build a deterministic paper-only unresolved blocker aging summary."""

    if type(inputs) is not ProbabilityEventUnresolvedBlockerAgingInput:
        raise ValueError(
            "inputs must be a ProbabilityEventUnresolvedBlockerAgingInput",
        )
    _require_hard_flags(inputs)
    reason_codes = _reason_codes(
        blocker_count=inputs.blocker_count,
        oldest_blocker_age_hours=inputs.oldest_blocker_age_hours,
        market_close_hours=inputs.market_close_hours,
        owner_assigned=inputs.owner_assigned,
        retry_count=inputs.retry_count,
    )
    blocker_aging_status = _blocker_aging_status(reason_codes)
    return ProbabilityEventUnresolvedBlockerAgingReport(
        config_version=PROBABILITY_EVENT_UNRESOLVED_BLOCKER_AGING_REPORT_VERSION,
        blocker_aging_status=blocker_aging_status,
        blocker_count=inputs.blocker_count,
        oldest_blocker_age_hours=inputs.oldest_blocker_age_hours,
        market_close_hours=inputs.market_close_hours,
        owner_assigned=inputs.owner_assigned,
        retry_count=inputs.retry_count,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(blocker_aging_status),
    )


def probability_event_unresolved_blocker_aging_report_payload(
    report: ProbabilityEventUnresolvedBlockerAgingReport,
) -> ProbabilityEventUnresolvedBlockerAgingPublicPayload:
    if type(report) is not ProbabilityEventUnresolvedBlockerAgingReport:
        raise ValueError("report must be a ProbabilityEventUnresolvedBlockerAgingReport")
    _require_hard_flags(report)
    _validate_report(report)
    return report.public_payload


def _validate_input_shape(
    inputs: ProbabilityEventUnresolvedBlockerAgingInput,
) -> None:
    if inputs.blocker_count == ZERO and inputs.oldest_blocker_age_hours != ZERO:
        raise ValueError("oldest_blocker_age_hours must be zero without blockers")
    if inputs.blocker_count == ZERO and inputs.retry_count != ZERO:
        raise ValueError("retry_count must be zero without blockers")


def _validate_report(report: ProbabilityEventUnresolvedBlockerAgingReport) -> None:
    _validate_report_shape(report)
    reason_codes = _reason_codes(
        blocker_count=report.blocker_count,
        oldest_blocker_age_hours=report.oldest_blocker_age_hours,
        market_close_hours=report.market_close_hours,
        owner_assigned=report.owner_assigned,
        retry_count=report.retry_count,
    )
    blocker_aging_status = _blocker_aging_status(reason_codes)
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match blocker aging inputs")
    if report.blocker_aging_status != blocker_aging_status:
        raise ValueError("blocker_aging_status must match reason codes")
    if report.manual_next_step != _manual_next_step(blocker_aging_status):
        raise ValueError("manual_next_step must match blocker_aging_status")


def _validate_report_shape(
    report: ProbabilityEventUnresolvedBlockerAgingReport,
) -> None:
    if report.blocker_count == ZERO and report.oldest_blocker_age_hours != ZERO:
        raise ValueError("oldest_blocker_age_hours must be zero without blockers")
    if report.blocker_count == ZERO and report.retry_count != ZERO:
        raise ValueError("retry_count must be zero without blockers")


def _validate_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match unresolved blocker aging schema")
    _require_config_version(payload["config_version"])
    _require_aging_status(payload["blocker_aging_status"])
    for field_name in (
        "blocker_count",
        "oldest_blocker_age_hours",
        "market_close_hours",
        "retry_count",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if field_name in {"blocker_count", "retry_count"}:
            _require_nonnegative_integral_decimal(field_name, Decimal(value))
        else:
            _require_nonnegative_decimal(field_name, Decimal(value))
    _require_bool("owner_assigned", payload["owner_assigned"])
    _normalize_reason_codes(payload["reason_codes"])
    _require_manual_next_step(payload["manual_next_step"])
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = payload[field_name]
        if flag is not True:
            raise ValueError(f"{field_name} must be True")
    return payload


def _payload_values(
    report: ProbabilityEventUnresolvedBlockerAgingReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "blocker_aging_status": report.blocker_aging_status,
        "blocker_count": _decimal_text(report.blocker_count),
        "oldest_blocker_age_hours": _decimal_text(report.oldest_blocker_age_hours),
        "market_close_hours": _decimal_text(report.market_close_hours),
        "owner_assigned": report.owner_assigned,
        "retry_count": _decimal_text(report.retry_count),
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _reason_codes(
    *,
    blocker_count: Decimal,
    oldest_blocker_age_hours: Decimal,
    market_close_hours: Decimal,
    owner_assigned: bool,
    retry_count: Decimal,
) -> tuple[str, ...]:
    if blocker_count == ZERO:
        return ("no_unresolved_blockers",)

    reasons: list[str] = []
    if oldest_blocker_age_hours > BLOCKER_AGE_BLOCK_HOURS:
        reasons.append("blocker_age_block")
    elif oldest_blocker_age_hours > BLOCKER_AGE_WATCH_HOURS:
        reasons.append("blocker_age_watch")
    if market_close_hours <= MARKET_CLOSE_BLOCK_HOURS:
        reasons.append("market_close_block_window")
    elif market_close_hours <= MARKET_CLOSE_WATCH_HOURS:
        reasons.append("market_close_watch_window")
    if not owner_assigned:
        reasons.append("owner_unassigned_block")
    if retry_count > RETRY_COUNT_BLOCK:
        reasons.append("retry_count_block")
    elif retry_count > RETRY_COUNT_WATCH:
        reasons.append("retry_count_watch")
    if not reasons:
        reasons.append("no_unresolved_blockers")
    return tuple(reason for reason in REASON_SEQUENCE if reason in reasons)


def _blocker_aging_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "blocked"
    if "market_close_block_window" in reason_codes:
        return "blocked"
    if reason_codes == ("no_unresolved_blockers",):
        return "clear"
    return "watch"


def _manual_next_step(blocker_aging_status: str) -> str:
    if blocker_aging_status == "clear":
        return "continue_paper_monitoring"
    if blocker_aging_status == "watch":
        return "refresh_blocker_owner_and_retry_plan"
    if blocker_aging_status == "blocked":
        return "escalate_unresolved_blockers_before_paper_review"
    raise ValueError("blocker_aging_status must be supported")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_UNRESOLVED_BLOCKER_AGING_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_aging_status(value: object) -> None:
    if type(value) is not str or value not in AGING_STATUSES:
        raise ValueError("blocker_aging_status must be supported")


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


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
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


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(_quantize(value), "f")
