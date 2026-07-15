"""Readonly source/liquidity alignment report for probability events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ProbabilityEventLiquiditySourceAlignmentReport",
    "build_probability_event_liquidity_source_alignment_report",
    "probability_event_liquidity_source_alignment_report_payload",
    "validate_probability_event_liquidity_source_alignment_public_payload",
)


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
ALIGNMENT_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "source_liquidity_alignment_ready"
SOURCE_CONFIDENCE_WATCH_REASON = "source_confidence_probability_watch"
SOURCE_CONFIDENCE_BLOCKED_REASON = "source_confidence_probability_blocked"
MARKET_DEPTH_WATCH_REASON = "market_depth_probability_watch"
MARKET_DEPTH_BLOCKED_REASON = "market_depth_probability_blocked"
SPREAD_WATCH_REASON = "spread_probability_watch"
SPREAD_BLOCKED_REASON = "spread_probability_blocked"
PRICE_MOVE_WATCH_REASON = "recent_price_move_probability_watch"
PRICE_MOVE_BLOCKED_REASON = "recent_price_move_probability_blocked"
FRESHNESS_WATCH_REASON = "source_freshness_age_hours_watch"
FRESHNESS_BLOCKED_REASON = "source_freshness_age_hours_blocked"
REASON_CODES = (
    READY_REASON,
    SOURCE_CONFIDENCE_WATCH_REASON,
    SOURCE_CONFIDENCE_BLOCKED_REASON,
    MARKET_DEPTH_WATCH_REASON,
    MARKET_DEPTH_BLOCKED_REASON,
    SPREAD_WATCH_REASON,
    SPREAD_BLOCKED_REASON,
    PRICE_MOVE_WATCH_REASON,
    PRICE_MOVE_BLOCKED_REASON,
    FRESHNESS_WATCH_REASON,
    FRESHNESS_BLOCKED_REASON,
)

READY_NEXT_STEP = "continue_readonly_probability_review"
WATCH_NEXT_STEP = "manually_review_source_liquidity_alignment"
BLOCKED_NEXT_STEP = "pause_and_refresh_sources_before_manual_review"
MANUAL_NEXT_STEPS = (READY_NEXT_STEP, WATCH_NEXT_STEP, BLOCKED_NEXT_STEP)

MIN_READY_SOURCE_CONFIDENCE = Decimal("0.700000")
MIN_BLOCKED_SOURCE_CONFIDENCE = Decimal("0.500000")
MIN_READY_MARKET_DEPTH = Decimal("0.800000")
MIN_BLOCKED_MARKET_DEPTH = Decimal("0.400000")
MAX_READY_SPREAD = Decimal("0.020000")
MAX_BLOCKED_SPREAD = Decimal("0.080000")
MAX_READY_RECENT_PRICE_MOVE = Decimal("0.050000")
MAX_BLOCKED_RECENT_PRICE_MOVE = Decimal("0.150000")
MAX_READY_SOURCE_FRESHNESS_HOURS = Decimal("6.000000")
MAX_BLOCKED_SOURCE_FRESHNESS_HOURS = Decimal("24.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    _join_parts("auth"),
    _join_parts("candidate", "_", "id"),
    _join_parts("execute"),
    _join_parts("key"),
    _join_parts("live"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("market", "_", "question"),
    _join_parts("private"),
    _join_parts("ques", "tion"),
    _join_parts("sign"),
    _join_parts("source", "_", "id"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "ref"),
    _join_parts("source", "_", "reference"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wallet"),
)


class _NoPublicSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoPublicSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventLiquiditySourceAlignmentReport(_NoPublicSubclass):
    source_confidence_probability: Decimal
    market_depth_probability: Decimal
    spread_probability: Decimal
    recent_price_move_probability: Decimal
    source_freshness_age_hours: Decimal
    liquidity_aligned_confidence_probability: Decimal
    alignment_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventLiquiditySourceAlignmentReport,
            "report",
        )
        for field_name in (
            "source_confidence_probability",
            "market_depth_probability",
            "spread_probability",
            "recent_price_move_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_freshness_age_hours",
            _require_nonnegative_decimal(
                "source_freshness_age_hours",
                self.source_freshness_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "liquidity_aligned_confidence_probability",
            _require_ratio(
                "liquidity_aligned_confidence_probability",
                self.liquidity_aligned_confidence_probability,
            ),
        )
        _require_choice("alignment_status", self.alignment_status, ALIGNMENT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_choice("manual_next_step", self.manual_next_step, MANUAL_NEXT_STEPS)
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def payload_digest(self) -> str:
        return _canonical_digest(_base_public_payload(self))

    @property
    def public_payload(self) -> dict[str, Any]:
        return _public_payload(self)


def build_probability_event_liquidity_source_alignment_report(
    *,
    source_confidence_probability: Decimal,
    market_depth_probability: Decimal,
    spread_probability: Decimal,
    recent_price_move_probability: Decimal,
    source_freshness_age_hours: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventLiquiditySourceAlignmentReport:
    source_confidence = _require_ratio(
        "source_confidence_probability",
        source_confidence_probability,
    )
    market_depth = _require_ratio("market_depth_probability", market_depth_probability)
    spread = _require_ratio("spread_probability", spread_probability)
    recent_price_move = _require_ratio(
        "recent_price_move_probability",
        recent_price_move_probability,
    )
    source_freshness = _require_nonnegative_decimal(
        "source_freshness_age_hours",
        source_freshness_age_hours,
    )
    evaluated = _evaluate(
        source_confidence_probability=source_confidence,
        market_depth_probability=market_depth,
        spread_probability=spread,
        recent_price_move_probability=recent_price_move,
        source_freshness_age_hours=source_freshness,
    )
    return ProbabilityEventLiquiditySourceAlignmentReport(
        source_confidence_probability=source_confidence,
        market_depth_probability=market_depth,
        spread_probability=spread,
        recent_price_move_probability=recent_price_move,
        source_freshness_age_hours=source_freshness,
        liquidity_aligned_confidence_probability=evaluated[
            "liquidity_aligned_confidence_probability"
        ],
        alignment_status=evaluated["alignment_status"],
        reason_codes=evaluated["reason_codes"],
        manual_next_step=evaluated["manual_next_step"],
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_liquidity_source_alignment_report_payload(
    report: ProbabilityEventLiquiditySourceAlignmentReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventLiquiditySourceAlignmentReport:
        raise ValueError(
            "report must be a ProbabilityEventLiquiditySourceAlignmentReport",
        )
    return _public_payload(report)


def validate_probability_event_liquidity_source_alignment_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    _require_payload_hard_flags(payload)
    digest = payload.get("payload_digest")
    if type(digest) is not str:
        raise ValueError("payload_digest must be a string")
    if len(digest) != 64:
        raise ValueError("payload_digest must be a sha256 hex string")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError("payload_digest must be a sha256 hex string") from exc
    unsigned = dict(payload)
    unsigned.pop("payload_digest")
    if digest != _canonical_digest(unsigned):
        raise ValueError("payload_digest does not match public payload")
    return True


def _evaluate(
    *,
    source_confidence_probability: Decimal,
    market_depth_probability: Decimal,
    spread_probability: Decimal,
    recent_price_move_probability: Decimal,
    source_freshness_age_hours: Decimal,
) -> dict[str, Any]:
    reason_codes: list[str] = []
    _append_floor_reason(
        reason_codes,
        source_confidence_probability,
        MIN_READY_SOURCE_CONFIDENCE,
        MIN_BLOCKED_SOURCE_CONFIDENCE,
        SOURCE_CONFIDENCE_WATCH_REASON,
        SOURCE_CONFIDENCE_BLOCKED_REASON,
    )
    _append_floor_reason(
        reason_codes,
        market_depth_probability,
        MIN_READY_MARKET_DEPTH,
        MIN_BLOCKED_MARKET_DEPTH,
        MARKET_DEPTH_WATCH_REASON,
        MARKET_DEPTH_BLOCKED_REASON,
    )
    _append_ceiling_reason(
        reason_codes,
        spread_probability,
        MAX_READY_SPREAD,
        MAX_BLOCKED_SPREAD,
        SPREAD_WATCH_REASON,
        SPREAD_BLOCKED_REASON,
    )
    _append_ceiling_reason(
        reason_codes,
        recent_price_move_probability,
        MAX_READY_RECENT_PRICE_MOVE,
        MAX_BLOCKED_RECENT_PRICE_MOVE,
        PRICE_MOVE_WATCH_REASON,
        PRICE_MOVE_BLOCKED_REASON,
    )
    _append_ceiling_reason(
        reason_codes,
        source_freshness_age_hours,
        MAX_READY_SOURCE_FRESHNESS_HOURS,
        MAX_BLOCKED_SOURCE_FRESHNESS_HOURS,
        FRESHNESS_WATCH_REASON,
        FRESHNESS_BLOCKED_REASON,
    )
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        status = STATUS_BLOCKED
        next_step = BLOCKED_NEXT_STEP
    elif reason_codes:
        status = STATUS_WATCH
        next_step = WATCH_NEXT_STEP
    else:
        status = STATUS_READY
        next_step = READY_NEXT_STEP
        reason_codes = [READY_REASON]
    return {
        "liquidity_aligned_confidence_probability": _aligned_confidence(
            source_confidence_probability=source_confidence_probability,
            market_depth_probability=market_depth_probability,
            spread_probability=spread_probability,
            recent_price_move_probability=recent_price_move_probability,
        ),
        "alignment_status": status,
        "reason_codes": tuple(reason_codes),
        "manual_next_step": next_step,
    }


def _aligned_confidence(
    *,
    source_confidence_probability: Decimal,
    market_depth_probability: Decimal,
    spread_probability: Decimal,
    recent_price_move_probability: Decimal,
) -> Decimal:
    del recent_price_move_probability
    spread_adjusted_source_confidence = source_confidence_probability - spread_probability
    if spread_adjusted_source_confidence < ZERO:
        spread_adjusted_source_confidence = ZERO
    return _quantize(min(spread_adjusted_source_confidence, market_depth_probability))


def _append_floor_reason(
    reason_codes: list[str],
    value: Decimal,
    ready_floor: Decimal,
    blocked_floor: Decimal,
    watch_reason: str,
    blocked_reason: str,
) -> None:
    if value < blocked_floor:
        reason_codes.append(blocked_reason)
    elif value < ready_floor:
        reason_codes.append(watch_reason)


def _append_ceiling_reason(
    reason_codes: list[str],
    value: Decimal,
    ready_ceiling: Decimal,
    blocked_ceiling: Decimal,
    watch_reason: str,
    blocked_reason: str,
) -> None:
    if value > blocked_ceiling:
        reason_codes.append(blocked_reason)
    elif value > ready_ceiling:
        reason_codes.append(watch_reason)


def _validate_report(
    report: ProbabilityEventLiquiditySourceAlignmentReport,
) -> None:
    expected = _evaluate(
        source_confidence_probability=report.source_confidence_probability,
        market_depth_probability=report.market_depth_probability,
        spread_probability=report.spread_probability,
        recent_price_move_probability=report.recent_price_move_probability,
        source_freshness_age_hours=report.source_freshness_age_hours,
    )
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match source liquidity alignment checks")


def _base_public_payload(
    report: ProbabilityEventLiquiditySourceAlignmentReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        ProbabilityEventLiquiditySourceAlignmentReport,
        "report",
    )
    _require_hard_flags("report", report)
    _validate_report(report)
    return {
        "source_confidence_probability": _public_decimal(
            report.source_confidence_probability,
        ),
        "market_depth_probability": _public_decimal(report.market_depth_probability),
        "spread_probability": _public_decimal(report.spread_probability),
        "recent_price_move_probability": _public_decimal(
            report.recent_price_move_probability,
        ),
        "source_freshness_age_hours": _public_decimal(
            report.source_freshness_age_hours,
        ),
        "liquidity_aligned_confidence_probability": _public_decimal(
            report.liquidity_aligned_confidence_probability,
        ),
        "alignment_status": report.alignment_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_payload(
    report: ProbabilityEventLiquiditySourceAlignmentReport,
) -> dict[str, Any]:
    payload = _base_public_payload(report)
    payload["payload_digest"] = _canonical_digest(payload)
    validate_probability_event_liquidity_source_alignment_public_payload(payload)
    return payload


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _public_decimal(value: Decimal) -> str:
    return format(_require_nonnegative_decimal("public decimal", value), "f")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value, field_name=field_name)


def _quantize(value: Decimal, *, field_name: str = "decimal") -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _require_choice(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_exact_type(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must have {field_name}=True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must have {field_name}=True")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("payload contains unsafe public key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
    elif type(value) in (Decimal, float, int):
        raise ValueError("public payload numeric values must be strings")
