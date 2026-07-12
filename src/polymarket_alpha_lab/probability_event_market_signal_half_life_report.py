"""Read-only probability event market signal half-life report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re


PROBABILITY_EVENT_MARKET_SIGNAL_HALF_LIFE_REPORT_VERSION = (
    "probability-event-market-signal-half-life-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
DIVERGENCE_THRESHOLD = Decimal("0.050000")
CURRENT_SOURCE_REFRESH_HOURS = Decimal("6.000000")
STALE_SOURCE_REFRESH_HOURS = Decimal("24.000000")
WATCH_SIGNAL_AGE_MULTIPLE = Decimal("0.500000")
BLOCK_SIGNAL_AGE_MULTIPLE = Decimal("3.000000")

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

SIGNAL_HALF_LIFE_STATUSES = ("pass", "watch", "block")
MANUAL_NEXT_STEPS = (
    "continue_monitoring_market_signal",
    "refresh_source_and_compare_market_move",
    "manual_research_review_required",
)
REASON_CODES = (
    "market_move_aligned_with_decayed_signal",
    "market_move_diverged_from_decayed_signal",
    "signal_half_life_pass",
    "signal_half_life_watch",
    "signal_half_life_block",
    "source_refresh_current",
    "source_refresh_attention",
    "source_refresh_stale",
)
PAYLOAD_KEYS = (
    "config_version",
    "signal_half_life_status",
    "decayed_signal_probability",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "key",
    "signing",
    "execution",
    "order",
    "trade",
    "network",
    "database",
    "persist",
    "secret",
    "token",
    "password",
    "dsn",
    "http://",
    "https://",
)

__all__ = (
    "PROBABILITY_EVENT_MARKET_SIGNAL_HALF_LIFE_REPORT_VERSION",
    "ProbabilityEventMarketSignalHalfLifeInput",
    "ProbabilityEventMarketSignalHalfLifePublicPayload",
    "ProbabilityEventMarketSignalHalfLifeReport",
    "build_probability_event_market_signal_half_life_report",
    "probability_event_market_signal_half_life_report_digest",
    "probability_event_market_signal_half_life_report_payload",
)


class ProbabilityEventMarketSignalHalfLifePublicPayload(dict[str, object]):
    """Immutable public payload for this read-only signal report."""

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
class ProbabilityEventMarketSignalHalfLifeInput:
    initial_signal_probability: Decimal
    signal_age_hours: Decimal
    market_move_probability: Decimal
    source_refresh_age_hours: Decimal
    half_life_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventMarketSignalHalfLifeInput:
            raise TypeError(
                "ProbabilityEventMarketSignalHalfLifeInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventMarketSignalHalfLifeInput:
            raise ValueError(
                "input must be exactly ProbabilityEventMarketSignalHalfLifeInput",
            )
        object.__setattr__(
            self,
            "initial_signal_probability",
            _require_probability_decimal(
                "initial_signal_probability",
                self.initial_signal_probability,
            ),
        )
        object.__setattr__(
            self,
            "signal_age_hours",
            _require_nonnegative_decimal("signal_age_hours", self.signal_age_hours),
        )
        object.__setattr__(
            self,
            "market_move_probability",
            _require_probability_decimal(
                "market_move_probability",
                self.market_move_probability,
            ),
        )
        object.__setattr__(
            self,
            "source_refresh_age_hours",
            _require_nonnegative_decimal(
                "source_refresh_age_hours",
                self.source_refresh_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "half_life_hours",
            _require_positive_decimal("half_life_hours", self.half_life_hours),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventMarketSignalHalfLifeReport:
    config_version: str
    signal_half_life_status: str
    decayed_signal_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventMarketSignalHalfLifeReport:
            raise TypeError(
                "ProbabilityEventMarketSignalHalfLifeReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventMarketSignalHalfLifeReport:
            raise ValueError(
                "report must be exactly ProbabilityEventMarketSignalHalfLifeReport",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != PROBABILITY_EVENT_MARKET_SIGNAL_HALF_LIFE_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        object.__setattr__(
            self,
            "signal_half_life_status",
            _require_member(
                "signal_half_life_status",
                self.signal_half_life_status,
                SIGNAL_HALF_LIFE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "decayed_signal_probability",
            _require_probability_decimal(
                "decayed_signal_probability",
                self.decayed_signal_probability,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_member("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS),
        )
        _require_digest("payload_digest", self.payload_digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> ProbabilityEventMarketSignalHalfLifePublicPayload:
        payload = ProbabilityEventMarketSignalHalfLifePublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_market_signal_half_life_report(
    signal: ProbabilityEventMarketSignalHalfLifeInput,
) -> ProbabilityEventMarketSignalHalfLifeReport:
    """Build a deterministic report-only probability signal half-life report."""

    if type(signal) is not ProbabilityEventMarketSignalHalfLifeInput:
        raise ValueError("signal must be a ProbabilityEventMarketSignalHalfLifeInput")
    _require_hard_flags(signal)
    decayed_probability = _decayed_probability(
        initial_signal_probability=signal.initial_signal_probability,
        signal_age_hours=signal.signal_age_hours,
        half_life_hours=signal.half_life_hours,
    )
    status = _signal_half_life_status(signal)
    reason_codes = _reason_codes(
        signal_half_life_status=status,
        decayed_signal_probability=decayed_probability,
        market_move_probability=signal.market_move_probability,
        source_refresh_age_hours=signal.source_refresh_age_hours,
    )
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_MARKET_SIGNAL_HALF_LIFE_REPORT_VERSION,
        "signal_half_life_status": status,
        "decayed_signal_probability": decayed_probability,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventMarketSignalHalfLifeReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_market_signal_half_life_report_payload(
    report: ProbabilityEventMarketSignalHalfLifeReport,
) -> ProbabilityEventMarketSignalHalfLifePublicPayload:
    if type(report) is not ProbabilityEventMarketSignalHalfLifeReport:
        raise ValueError(
            "report must be a ProbabilityEventMarketSignalHalfLifeReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    expected_digest = probability_event_market_signal_half_life_report_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match report payload")
    return report.public_payload


def probability_event_market_signal_half_life_report_digest(
    report: ProbabilityEventMarketSignalHalfLifeReport,
) -> str:
    if type(report) is not ProbabilityEventMarketSignalHalfLifeReport:
        raise ValueError(
            "report must be a ProbabilityEventMarketSignalHalfLifeReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return _payload_digest(_payload_items(report, payload_digest=""))


def _decayed_probability(
    *,
    initial_signal_probability: Decimal,
    signal_age_hours: Decimal,
    half_life_hours: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 48
        age_ratio = signal_age_hours / half_life_hours
        decay_factor = ((-TWO.ln()) * age_ratio).exp()
        result = initial_signal_probability * decay_factor
    return _require_probability_decimal("decayed_signal_probability", result)


def _signal_half_life_status(
    signal: ProbabilityEventMarketSignalHalfLifeInput,
) -> str:
    if signal.signal_age_hours >= signal.half_life_hours * BLOCK_SIGNAL_AGE_MULTIPLE:
        return "block"
    if signal.signal_age_hours >= signal.half_life_hours * WATCH_SIGNAL_AGE_MULTIPLE:
        return "watch"
    if signal.source_refresh_age_hours >= STALE_SOURCE_REFRESH_HOURS:
        return "watch"
    return "pass"


def _reason_codes(
    *,
    signal_half_life_status: str,
    decayed_signal_probability: Decimal,
    market_move_probability: Decimal,
    source_refresh_age_hours: Decimal,
) -> tuple[str, ...]:
    divergence = abs(market_move_probability - decayed_signal_probability)
    market_reason = (
        "market_move_diverged_from_decayed_signal"
        if divergence > DIVERGENCE_THRESHOLD
        else "market_move_aligned_with_decayed_signal"
    )
    if source_refresh_age_hours >= STALE_SOURCE_REFRESH_HOURS:
        source_reason = "source_refresh_stale"
    elif source_refresh_age_hours > CURRENT_SOURCE_REFRESH_HOURS:
        source_reason = "source_refresh_attention"
    else:
        source_reason = "source_refresh_current"
    return tuple(
        sorted(
            (
                market_reason,
                f"signal_half_life_{signal_half_life_status}",
                source_reason,
            ),
        ),
    )


def _manual_next_step(signal_half_life_status: str) -> str:
    if signal_half_life_status == "block":
        return "manual_research_review_required"
    if signal_half_life_status == "watch":
        return "refresh_source_and_compare_market_move"
    return "continue_monitoring_market_signal"


def _validate_report(report: ProbabilityEventMarketSignalHalfLifeReport) -> None:
    status_reason = f"signal_half_life_{report.signal_half_life_status}"
    if status_reason not in report.reason_codes:
        raise ValueError("reason_codes must include matching signal_half_life_status")
    if report.manual_next_step != _manual_next_step(report.signal_half_life_status):
        raise ValueError("manual_next_step must match signal_half_life_status")


def _payload_items(
    report: ProbabilityEventMarketSignalHalfLifeReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(_report_values_without_digest(report), payload_digest=payload_digest)


def _report_values_without_digest(
    report: ProbabilityEventMarketSignalHalfLifeReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "signal_half_life_status": report.signal_half_life_status,
        "decayed_signal_probability": report.decayed_signal_probability,
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
        "signal_half_life_status": values["signal_half_life_status"],
        "decayed_signal_probability": _decimal_text(values["decayed_signal_probability"]),
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": payload_digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("public payload keys must match report contract")
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != PROBABILITY_EVENT_MARKET_SIGNAL_HALF_LIFE_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    _require_member(
        "signal_half_life_status",
        payload["signal_half_life_status"],
        SIGNAL_HALF_LIFE_STATUSES,
    )
    _parse_decimal_string(
        "decayed_signal_probability",
        payload["decayed_signal_probability"],
    )
    _normalize_reason_codes(_tuple_from_payload("reason_codes", payload["reason_codes"]))
    _require_member("manual_next_step", payload["manual_next_step"], MANUAL_NEXT_STEPS)
    _require_hard_flags(payload)
    _require_digest("payload_digest", payload["payload_digest"])
    _reject_unsafe_public_payload(payload)
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    if payload["payload_digest"] != _payload_digest(unsigned):
        raise ValueError("payload_digest must match public payload")


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError("reason_codes must be sorted")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes contain unsupported reason code")
    return reason_codes


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = value[field_name] if isinstance(value, Mapping) else getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_member(field_name: str, value: object, values: tuple[str, ...]) -> str:
    if type(value) is not str or value not in values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public numeric value must be Decimal")
    return format(_quantize(value), "f")


def _parse_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    parsed = Decimal(value)
    normalized = _require_probability_decimal(field_name, parsed)
    if _decimal_text(normalized) != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return normalized


def _tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list in public payload")
    if not all(type(item) is str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(value)


def _payload_digest(payload: Mapping[str, object]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True, default=str).lower()
    for term in UNSAFE_PUBLIC_TERMS:
        if term in serialized:
            raise ValueError("public payload must not expose restricted runtime surfaces")
