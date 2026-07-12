"""Pure exit penalty stress report for probability event liquidity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json


STATUS_CLEAR = "clear"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
EXIT_PENALTY_STATUSES = (STATUS_CLEAR, STATUS_WATCH, STATUS_BLOCKED)

CLEAR_REASON = "exit_penalty_stress_clear"
DEPTH_WATCH_REASON = "exit_depth_probability_watch"
DEPTH_BLOCKED_REASON = "exit_depth_probability_blocked"
TIME_WATCH_REASON = "time_to_resolution_compressed"
TIME_BLOCKED_REASON = "time_to_resolution_blocked"
STRESSED_COST_WATCH_REASON = "stressed_exit_cost_probability_watch"
STRESSED_COST_BLOCKED_REASON = "stressed_exit_cost_probability_blocked"
REASON_CODES = (
    CLEAR_REASON,
    DEPTH_WATCH_REASON,
    DEPTH_BLOCKED_REASON,
    TIME_WATCH_REASON,
    TIME_BLOCKED_REASON,
    STRESSED_COST_WATCH_REASON,
    STRESSED_COST_BLOCKED_REASON,
)

CLEAR_MANUAL_NEXT_STEP = "monitor_exit_penalty_stress"
WATCH_MANUAL_NEXT_STEP = "manual_review_exit_penalty_stress"
BLOCKED_MANUAL_NEXT_STEP = "block_until_manual_exit_cost_review"
MANUAL_NEXT_STEPS = (
    CLEAR_MANUAL_NEXT_STEP,
    WATCH_MANUAL_NEXT_STEP,
    BLOCKED_MANUAL_NEXT_STEP,
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MIN_CLEAR_DEPTH_PROBABILITY = Decimal("0.800000")
MIN_CLEAR_TIME_TO_RESOLUTION_HOURS = Decimal("48.000000")
MAX_CLEAR_STRESSED_EXIT_COST_PROBABILITY = Decimal("0.030000")
MIN_WATCH_DEPTH_PROBABILITY = Decimal("0.400000")
MIN_WATCH_TIME_TO_RESOLUTION_HOURS = Decimal("12.000000")
MAX_WATCH_STRESSED_EXIT_COST_PROBABILITY = Decimal("0.080000")

INPUT_FIELDS = (
    "entry_cost_probability",
    "exit_cost_probability",
    "exit_depth_probability",
    "time_to_resolution_hours",
    "stress_penalty_probability",
)
INPUT_PROBABILITY_FIELDS = (
    "entry_cost_probability",
    "exit_cost_probability",
    "exit_depth_probability",
    "stress_penalty_probability",
)
REPORT_DECIMAL_FIELDS = (
    *INPUT_FIELDS,
    "stressed_exit_cost_probability",
)
PAYLOAD_KEYS = (
    *INPUT_FIELDS,
    "stressed_exit_cost_probability",
    "exit_penalty_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "EXIT_PENALTY_STATUSES",
    "ProbabilityEventLiquidityExitPenaltyStressReport",
    "build_probability_event_liquidity_exit_penalty_stress_report",
    "probability_event_liquidity_exit_penalty_stress_report_digest",
    "probability_event_liquidity_exit_penalty_stress_report_to_payload",
    "validate_probability_event_liquidity_exit_penalty_stress_public_payload",
)


@dataclass(frozen=True)
class ProbabilityEventLiquidityExitPenaltyStressReport:
    entry_cost_probability: Decimal
    exit_cost_probability: Decimal
    exit_depth_probability: Decimal
    time_to_resolution_hours: Decimal
    stress_penalty_probability: Decimal
    stressed_exit_cost_probability: Decimal
    exit_penalty_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventLiquidityExitPenaltyStressReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventLiquidityExitPenaltyStressReport,
            "report",
        )
        for field_name in (
            "entry_cost_probability",
            "exit_cost_probability",
            "exit_depth_probability",
            "stress_penalty_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_hours",
            _require_nonnegative_decimal(
                "time_to_resolution_hours",
                self.time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "stressed_exit_cost_probability",
            _require_nonnegative_decimal(
                "stressed_exit_cost_probability",
                self.stressed_exit_cost_probability,
            ),
        )
        object.__setattr__(
            self,
            "exit_penalty_status",
            _require_exit_penalty_status(
                "exit_penalty_status",
                self.exit_penalty_status,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step("manual_next_step", self.manual_next_step),
        )
        _require_sha256_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _digest_payload(_payload_from_report(self))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_liquidity_exit_penalty_stress_report_to_payload(self)


def build_probability_event_liquidity_exit_penalty_stress_report(
    *,
    entry_cost_probability: Decimal,
    exit_cost_probability: Decimal,
    exit_depth_probability: Decimal,
    time_to_resolution_hours: Decimal,
    stress_penalty_probability: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventLiquidityExitPenaltyStressReport:
    values: dict[str, object] = {
        "entry_cost_probability": _require_probability_decimal(
            "entry_cost_probability",
            entry_cost_probability,
        ),
        "exit_cost_probability": _require_probability_decimal(
            "exit_cost_probability",
            exit_cost_probability,
        ),
        "exit_depth_probability": _require_probability_decimal(
            "exit_depth_probability",
            exit_depth_probability,
        ),
        "time_to_resolution_hours": _require_nonnegative_decimal(
            "time_to_resolution_hours",
            time_to_resolution_hours,
        ),
        "stress_penalty_probability": _require_probability_decimal(
            "stress_penalty_probability",
            stress_penalty_probability,
        ),
    }
    values.update(_derived_values(**values))  # type: ignore[arg-type]
    digest = _digest_payload(_payload_from_values(values))
    return ProbabilityEventLiquidityExitPenaltyStressReport(
        **values,
        payload_digest=digest,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_liquidity_exit_penalty_stress_report_to_payload(
    report: ProbabilityEventLiquidityExitPenaltyStressReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventLiquidityExitPenaltyStressReport:
        raise ValueError(
            "report must be a ProbabilityEventLiquidityExitPenaltyStressReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    expected_digest = _digest_payload(_payload_from_report(report))
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")
    payload = _payload_from_report(report)
    validate_probability_event_liquidity_exit_penalty_stress_public_payload(payload)
    return payload


def probability_event_liquidity_exit_penalty_stress_report_digest(
    report: ProbabilityEventLiquidityExitPenaltyStressReport,
) -> str:
    payload = probability_event_liquidity_exit_penalty_stress_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_liquidity_exit_penalty_stress_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical schema")
    inputs = {
        field_name: _require_payload_decimal(field_name, payload[field_name])
        for field_name in INPUT_FIELDS
    }
    expected = _derived_values(**inputs)
    parsed_stressed_cost = _require_payload_decimal(
        "stressed_exit_cost_probability",
        payload["stressed_exit_cost_probability"],
    )
    if parsed_stressed_cost != expected["stressed_exit_cost_probability"]:
        raise ValueError(
            "stressed_exit_cost_probability must match exit stress inputs",
        )
    if payload["exit_penalty_status"] != expected["exit_penalty_status"]:
        raise ValueError("exit_penalty_status must match exit stress inputs")
    reason_codes = _normalize_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
    )
    if reason_codes != expected["reason_codes"]:
        raise ValueError("reason_codes must match exit stress inputs")
    if payload["manual_next_step"] != expected["manual_next_step"]:
        raise ValueError("manual_next_step must match exit stress inputs")
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    return payload


def _derived_values(
    *,
    entry_cost_probability: Decimal,
    exit_cost_probability: Decimal,
    exit_depth_probability: Decimal,
    time_to_resolution_hours: Decimal,
    stress_penalty_probability: Decimal,
) -> dict[str, object]:
    del entry_cost_probability
    stressed_exit_cost_probability = _require_nonnegative_decimal(
        "stressed_exit_cost_probability",
        exit_cost_probability + stress_penalty_probability,
    )
    blocked_reasons: list[str] = []
    if exit_depth_probability < MIN_WATCH_DEPTH_PROBABILITY:
        blocked_reasons.append(DEPTH_BLOCKED_REASON)
    if time_to_resolution_hours < MIN_WATCH_TIME_TO_RESOLUTION_HOURS:
        blocked_reasons.append(TIME_BLOCKED_REASON)
    if stressed_exit_cost_probability > MAX_WATCH_STRESSED_EXIT_COST_PROBABILITY:
        blocked_reasons.append(STRESSED_COST_BLOCKED_REASON)
    if blocked_reasons:
        return {
            "stressed_exit_cost_probability": stressed_exit_cost_probability,
            "exit_penalty_status": STATUS_BLOCKED,
            "reason_codes": tuple(blocked_reasons),
            "manual_next_step": BLOCKED_MANUAL_NEXT_STEP,
        }

    watch_reasons: list[str] = []
    if exit_depth_probability < MIN_CLEAR_DEPTH_PROBABILITY:
        watch_reasons.append(DEPTH_WATCH_REASON)
    if time_to_resolution_hours < MIN_CLEAR_TIME_TO_RESOLUTION_HOURS:
        watch_reasons.append(TIME_WATCH_REASON)
    if stressed_exit_cost_probability > MAX_CLEAR_STRESSED_EXIT_COST_PROBABILITY:
        watch_reasons.append(STRESSED_COST_WATCH_REASON)
    if watch_reasons:
        return {
            "stressed_exit_cost_probability": stressed_exit_cost_probability,
            "exit_penalty_status": STATUS_WATCH,
            "reason_codes": tuple(watch_reasons),
            "manual_next_step": WATCH_MANUAL_NEXT_STEP,
        }
    return {
        "stressed_exit_cost_probability": stressed_exit_cost_probability,
        "exit_penalty_status": STATUS_CLEAR,
        "reason_codes": (CLEAR_REASON,),
        "manual_next_step": CLEAR_MANUAL_NEXT_STEP,
    }


def _validate_report(
    report: ProbabilityEventLiquidityExitPenaltyStressReport,
) -> None:
    expected = _derived_values(
        entry_cost_probability=report.entry_cost_probability,
        exit_cost_probability=report.exit_cost_probability,
        exit_depth_probability=report.exit_depth_probability,
        time_to_resolution_hours=report.time_to_resolution_hours,
        stress_penalty_probability=report.stress_penalty_probability,
    )
    for field_name in (
        "stressed_exit_cost_probability",
        "exit_penalty_status",
        "reason_codes",
        "manual_next_step",
    ):
        if getattr(report, field_name) != expected[field_name]:
            raise ValueError(f"{field_name} must match exit stress inputs")


def _payload_from_report(
    report: ProbabilityEventLiquidityExitPenaltyStressReport,
) -> dict[str, object]:
    return _payload_from_values(
        {
            field_name: getattr(report, field_name)
            for field_name in PAYLOAD_KEYS
            if field_name not in ("paper_only", "report_only", "readonly")
        },
    )


def _payload_from_values(values: Mapping[str, object]) -> dict[str, object]:
    return {
        "entry_cost_probability": _decimal_text(values["entry_cost_probability"]),
        "exit_cost_probability": _decimal_text(values["exit_cost_probability"]),
        "exit_depth_probability": _decimal_text(values["exit_depth_probability"]),
        "time_to_resolution_hours": _decimal_text(values["time_to_resolution_hours"]),
        "stress_penalty_probability": _decimal_text(
            values["stress_penalty_probability"],
        ),
        "stressed_exit_cost_probability": _decimal_text(
            values["stressed_exit_cost_probability"],
        ),
        "exit_penalty_status": values["exit_penalty_status"],
        "reason_codes": list(values["reason_codes"]),  # type: ignore[arg-type]
        "manual_next_step": values["manual_next_step"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_code_items(field_name, tuple(value))


def _normalize_reason_code_items(
    field_name: str,
    value: tuple[object, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for item in value:
        if type(item) is not str or item not in REASON_CODES:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
    canonical = tuple(item for item in REASON_CODES if item in seen)
    if value != canonical:
        raise ValueError(f"{field_name} must use canonical sequence")
    return canonical


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_exit_penalty_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in EXIT_PENALTY_STATUSES:
        raise ValueError(f"{field_name} must be a supported exit penalty status")
    return value


def _require_manual_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual next step")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _require_payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if parsed != _require_nonnegative_decimal(field_name, parsed):
        raise ValueError(f"{field_name} must be quantized to six places")
    if field_name in INPUT_PROBABILITY_FIELDS and parsed > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return parsed


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    allowed = set("0123456789abcdef")
    if any(item not in allowed for item in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload Decimal value must be a Decimal")
    return format(_require_decimal("payload Decimal value", value), "f")


def _digest_payload(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
