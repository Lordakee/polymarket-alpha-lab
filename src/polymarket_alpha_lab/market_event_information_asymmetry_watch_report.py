"""Readonly market event information asymmetry watch report reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MOVE_WATCH_PROBABILITY = Decimal("0.050000")
MOVE_BLOCK_PROBABILITY = Decimal("0.150000")
OFFICIAL_STALE_HOURS = Decimal("6.000000")
INDEPENDENT_FRESH_HOURS = Decimal("1.000000")
SPREAD_WATCH_PROBABILITY = Decimal("0.050000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

PASS_REASON = "information_asymmetry_within_limit"
MOVE_HIGH_REASON = "market_move_probability_high"
OFFICIAL_STALE_REASON = "official_source_stale"
INDEPENDENT_FRESH_REASON = "independent_source_fresh"
CONFLICTS_PRESENT_REASON = "source_conflicts_present"
SPREAD_WIDE_REASON = "spread_probability_wide"
REASON_CODES = (
    MOVE_HIGH_REASON,
    OFFICIAL_STALE_REASON,
    INDEPENDENT_FRESH_REASON,
    CONFLICTS_PRESENT_REASON,
    SPREAD_WIDE_REASON,
    PASS_REASON,
)

STEP_CONTINUE = "continue_manual_information_monitoring"
STEP_COMPARE = "manually_compare_public_information_sources"
STEP_PAUSE = "pause_probability_interpretation_for_manual_source_review"
MANUAL_STEPS = (STEP_CONTINUE, STEP_COMPARE, STEP_PAUSE)

__all__ = (
    "MarketEventInformationAsymmetryWatchReport",
    "build_market_event_information_asymmetry_watch_report",
    "market_event_information_asymmetry_watch_report_digest",
    "market_event_information_asymmetry_watch_report_to_public_payload",
    "validate_market_event_information_asymmetry_watch_report_payload",
)


@dataclass(frozen=True)
class MarketEventInformationAsymmetryWatchReport:
    market_move_probability: Decimal
    official_source_age_hours: Decimal
    independent_source_age_hours: Decimal
    source_conflict_count: Decimal
    spread_probability: Decimal
    asymmetry_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventInformationAsymmetryWatchReport:
            raise TypeError(
                "MarketEventInformationAsymmetryWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketEventInformationAsymmetryWatchReport, "report")
        object.__setattr__(
            self,
            "market_move_probability",
            _require_ratio_decimal(
                "market_move_probability",
                self.market_move_probability,
            ),
        )
        for name in ("official_source_age_hours", "independent_source_age_hours"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "source_conflict_count",
            _require_whole_nonnegative_decimal(
                "source_conflict_count",
                self.source_conflict_count,
            ),
        )
        object.__setattr__(
            self,
            "spread_probability",
            _require_ratio_decimal("spread_probability", self.spread_probability),
        )
        _require_status("asymmetry_status", self.asymmetry_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.payload_digest == "":
            object.__setattr__(
                self,
                "payload_digest",
                _payload_digest(_payload_value(self, include_digest=False)),
            )
        else:
            _require_sha256("payload_digest", self.payload_digest)
            _require_matching_digest(_payload_value(self, include_digest=True))

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_event_information_asymmetry_watch_report_to_public_payload(self)


def build_market_event_information_asymmetry_watch_report(
    *,
    market_move_probability: Decimal,
    official_source_age_hours: Decimal,
    independent_source_age_hours: Decimal,
    source_conflict_count: Decimal,
    spread_probability: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketEventInformationAsymmetryWatchReport:
    values = {
        "market_move_probability": _require_ratio_decimal(
            "market_move_probability",
            market_move_probability,
        ),
        "official_source_age_hours": _require_nonnegative_decimal(
            "official_source_age_hours",
            official_source_age_hours,
        ),
        "independent_source_age_hours": _require_nonnegative_decimal(
            "independent_source_age_hours",
            independent_source_age_hours,
        ),
        "source_conflict_count": _require_whole_nonnegative_decimal(
            "source_conflict_count",
            source_conflict_count,
        ),
        "spread_probability": _require_ratio_decimal(
            "spread_probability",
            spread_probability,
        ),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    _require_hard_flags("input", _FlagView(paper_only, report_only, readonly))
    reasons = _reason_codes(
        market_move_probability=values["market_move_probability"],
        official_source_age_hours=values["official_source_age_hours"],
        independent_source_age_hours=values["independent_source_age_hours"],
        source_conflict_count=values["source_conflict_count"],
        spread_probability=values["spread_probability"],
    )
    status = _asymmetry_status(reasons)
    return MarketEventInformationAsymmetryWatchReport(
        **values,
        asymmetry_status=status,
        reason_codes=reasons,
        manual_next_step=_manual_next_step(status),
        payload_digest="",
    )


def market_event_information_asymmetry_watch_report_digest(
    report: MarketEventInformationAsymmetryWatchReport,
) -> str:
    _require_exact_type(report, MarketEventInformationAsymmetryWatchReport, "report")
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return report.payload_digest


def market_event_information_asymmetry_watch_report_to_public_payload(
    report: MarketEventInformationAsymmetryWatchReport,
) -> dict[str, Any]:
    _require_exact_type(report, MarketEventInformationAsymmetryWatchReport, "report")
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return payload


def validate_market_event_information_asymmetry_watch_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_payload_numeric_objects(payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    _require_payload_report_shape(payload)
    return True


@dataclass(frozen=True)
class _FlagView:
    paper_only: bool
    report_only: bool
    readonly: bool


def _reason_codes(
    *,
    market_move_probability: Decimal,
    official_source_age_hours: Decimal,
    independent_source_age_hours: Decimal,
    source_conflict_count: Decimal,
    spread_probability: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if market_move_probability >= MOVE_WATCH_PROBABILITY:
        reasons.append(MOVE_HIGH_REASON)
    if official_source_age_hours >= OFFICIAL_STALE_HOURS:
        reasons.append(OFFICIAL_STALE_REASON)
    if independent_source_age_hours <= INDEPENDENT_FRESH_HOURS:
        reasons.append(INDEPENDENT_FRESH_REASON)
    if source_conflict_count > ZERO:
        reasons.append(CONFLICTS_PRESENT_REASON)
    if spread_probability >= SPREAD_WATCH_PROBABILITY:
        reasons.append(SPREAD_WIDE_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reasons)


def _asymmetry_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if (
        MOVE_HIGH_REASON in reason_codes
        and OFFICIAL_STALE_REASON in reason_codes
        and INDEPENDENT_FRESH_REASON in reason_codes
    ):
        return STATUS_BLOCK
    if (
        MOVE_HIGH_REASON in reason_codes
        and CONFLICTS_PRESENT_REASON in reason_codes
        and market_pressure_reasons(reason_codes)
    ):
        return STATUS_BLOCK
    if OFFICIAL_STALE_REASON in reason_codes and CONFLICTS_PRESENT_REASON in reason_codes:
        return STATUS_BLOCK
    return STATUS_WATCH


def market_pressure_reasons(reason_codes: tuple[str, ...]) -> bool:
    return SPREAD_WIDE_REASON in reason_codes


def _manual_next_step(status: str) -> str:
    if status == STATUS_PASS:
        return STEP_CONTINUE
    if status == STATUS_WATCH:
        return STEP_COMPARE
    if status == STATUS_BLOCK:
        return STEP_PAUSE
    raise ValueError("asymmetry_status must be supported")


def _validate_report(report: MarketEventInformationAsymmetryWatchReport) -> None:
    expected_reasons = _reason_codes(
        market_move_probability=report.market_move_probability,
        official_source_age_hours=report.official_source_age_hours,
        independent_source_age_hours=report.independent_source_age_hours,
        source_conflict_count=report.source_conflict_count,
        spread_probability=report.spread_probability,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report inputs")
    expected_status = _asymmetry_status(expected_reasons)
    if report.asymmetry_status != expected_status:
        raise ValueError("asymmetry_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match asymmetry_status")


def _payload_value(
    value: Any,
    *,
    include_digest: bool,
) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(
            {
                field.name: getattr(value, field.name)
                for field in fields(value)
                if include_digest or field.name != "payload_digest"
            },
            include_digest=include_digest,
        )
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is str:
        if not value:
            raise ValueError("public payload strings must be non-empty")
        return value
    if type(value) is bool or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("public payload names must be strings")
            payload[name] = _payload_value(item, include_digest=include_digest)
        return payload
    raise ValueError("public payload contains unsupported value")


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(_canonical_payload(payload), separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _canonical_payload(value: Any) -> Any:
    if type(value) is dict:
        return {name: _canonical_payload(value[name]) for name in sorted(value)}
    if type(value) is list:
        return [_canonical_payload(item) for item in value]
    return value


def _require_matching_digest(payload: Any) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    if "payload_digest" not in payload:
        raise ValueError("payload_digest is required")
    _require_sha256("payload_digest", payload["payload_digest"])
    material = {name: item for name, item in payload.items() if name != "payload_digest"}
    if payload["payload_digest"] != _payload_digest(material):
        raise ValueError("payload_digest does not match public payload")


def _require_payload_report_shape(payload: dict[str, Any]) -> None:
    required_names = (
        "market_move_probability",
        "official_source_age_hours",
        "independent_source_age_hours",
        "source_conflict_count",
        "spread_probability",
        "asymmetry_status",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    for name in required_names:
        if name not in payload:
            raise ValueError(f"public payload missing {name}")
    _require_status("asymmetry_status", payload["asymmetry_status"])
    _require_reason_code_list("reason_codes", payload["reason_codes"])
    _require_manual_step("manual_next_step", payload["manual_next_step"])


def _reject_payload_numeric_objects(value: Any) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_payload_numeric_objects(item)
        return
    if type(value) is list:
        for item in value:
            _reject_payload_numeric_objects(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if payload.get(name) is not True:
            raise ValueError(f"payload {name} must be True")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_whole_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of {STATUSES}")


def _require_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must be nonempty")
    for value in values:
        if type(value) is not str or value not in REASON_CODES:
            raise ValueError(f"{name} contains an unknown reason code")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    return values


def _require_reason_code_list(name: str, values: object) -> None:
    if type(values) is not list:
        raise ValueError(f"{name} must be a list")
    _require_reason_codes(name, tuple(values))


def _require_manual_step(name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_STEPS:
        raise ValueError(f"{name} must be supported")


def _require_sha256(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 digest string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a sha256 digest string") from exc


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX)
