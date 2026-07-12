"""Pure Phase 1 adverse selection report for caller-supplied inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ProbabilityEventMarketMakerAdverseSelectionPayload",
    "ProbabilityEventMarketMakerAdverseSelectionReport",
    "build_probability_event_market_maker_adverse_selection_report",
    "probability_event_market_maker_adverse_selection_payload_digest",
)


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
EDGE_SENTINEL = Decimal("-1.000000")
QUANTUM = Decimal("0.000001")

PASS = "pass"
WATCH = "watch"
BLOCK = "block"
STATUS_VALUES = (PASS, WATCH, BLOCK)

SPREAD_WATCH = Decimal("0.050000")
SPREAD_BLOCK = Decimal("0.150000")
PRICE_MOVE_WATCH = Decimal("0.050000")
PRICE_MOVE_BLOCK = Decimal("0.150000")
DEPTH_IMBALANCE_WATCH = Decimal("0.300000")
DEPTH_IMBALANCE_BLOCK = Decimal("0.700000")
SOURCE_AGE_WATCH_HOURS = Decimal("6.000000")
SOURCE_AGE_BLOCK_HOURS = Decimal("24.000000")
FORECAST_AGE_WATCH_HOURS = Decimal("12.000000")
FORECAST_AGE_BLOCK_HOURS = Decimal("48.000000")
SCORE_WATCH = Decimal("0.250000")
SCORE_BLOCK = Decimal("0.700000")

SPREAD_WEIGHT = Decimal("0.500000")
PRICE_MOVE_WEIGHT = Decimal("0.750000")
DEPTH_IMBALANCE_WEIGHT = Decimal("0.375000")
SOURCE_AGE_WEIGHT = Decimal("0.007169")
FORECAST_AGE_WEIGHT = Decimal("0.004957")

PAYLOAD_KEYS = (
    "spread_probability",
    "recent_price_move_probability",
    "depth_imbalance_probability",
    "source_freshness_age_hours",
    "forecast_age_hours",
    "adverse_selection_status",
    "risk_adjusted_edge_probability",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class ProbabilityEventMarketMakerAdverseSelectionPayload(dict[str, object]):
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
class ProbabilityEventMarketMakerAdverseSelectionReport:
    spread_probability: Decimal
    recent_price_move_probability: Decimal
    depth_imbalance_probability: Decimal
    source_freshness_age_hours: Decimal
    forecast_age_hours: Decimal
    adverse_selection_status: str = ""
    risk_adjusted_edge_probability: Decimal = EDGE_SENTINEL
    reason_codes: tuple[str, ...] = ()
    manual_next_step: str = ""
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventMarketMakerAdverseSelectionReport:
            raise ValueError(
                "report must be exactly "
                "ProbabilityEventMarketMakerAdverseSelectionReport",
            )
        object.__setattr__(
            self,
            "spread_probability",
            _require_probability_decimal("spread_probability", self.spread_probability),
        )
        object.__setattr__(
            self,
            "recent_price_move_probability",
            _require_probability_decimal(
                "recent_price_move_probability",
                self.recent_price_move_probability,
            ),
        )
        object.__setattr__(
            self,
            "depth_imbalance_probability",
            _require_probability_decimal(
                "depth_imbalance_probability",
                self.depth_imbalance_probability,
            ),
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
            "forecast_age_hours",
            _require_nonnegative_decimal("forecast_age_hours", self.forecast_age_hours),
        )
        _require_hard_flags(self)

        derived_edge = _risk_adjusted_edge_probability(self)
        if self.risk_adjusted_edge_probability == EDGE_SENTINEL:
            object.__setattr__(self, "risk_adjusted_edge_probability", derived_edge)
        else:
            object.__setattr__(
                self,
                "risk_adjusted_edge_probability",
                _require_probability_decimal(
                    "risk_adjusted_edge_probability",
                    self.risk_adjusted_edge_probability,
                ),
            )
            if self.risk_adjusted_edge_probability != derived_edge:
                raise ValueError("risk_adjusted_edge_probability must match inputs")

        derived_status = _adverse_selection_status(self)
        if self.adverse_selection_status == "":
            object.__setattr__(self, "adverse_selection_status", derived_status)
        elif self.adverse_selection_status != derived_status:
            raise ValueError("adverse_selection_status must match inputs")
        elif self.adverse_selection_status not in STATUS_VALUES:
            raise ValueError("adverse_selection_status must be pass, watch, or block")

        derived_reasons = _reason_codes(self)
        if self.reason_codes == ():
            object.__setattr__(self, "reason_codes", derived_reasons)
        else:
            normalized_reasons = _normalize_reason_codes("reason_codes", self.reason_codes)
            if normalized_reasons != derived_reasons:
                raise ValueError("reason_codes must match inputs")
            object.__setattr__(self, "reason_codes", normalized_reasons)

        derived_next_step = _manual_next_step_for(self.adverse_selection_status)
        if self.manual_next_step == "":
            object.__setattr__(self, "manual_next_step", derived_next_step)
        elif self.manual_next_step != derived_next_step:
            raise ValueError("manual_next_step must match status")
        else:
            _require_public_code("manual_next_step", self.manual_next_step)

        derived_digest = _payload_digest(_payload_items(self, digest=""))
        if self.payload_digest == "":
            object.__setattr__(self, "payload_digest", derived_digest)
        elif self.payload_digest != derived_digest:
            raise ValueError("payload_digest must match public payload")
        else:
            _require_digest("payload_digest", self.payload_digest)

    @property
    def public_payload(self) -> ProbabilityEventMarketMakerAdverseSelectionPayload:
        payload = ProbabilityEventMarketMakerAdverseSelectionPayload(
            _payload_items(self, digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_market_maker_adverse_selection_report(
    *,
    spread_probability: Decimal,
    recent_price_move_probability: Decimal,
    depth_imbalance_probability: Decimal,
    source_freshness_age_hours: Decimal,
    forecast_age_hours: Decimal,
) -> ProbabilityEventMarketMakerAdverseSelectionReport:
    return ProbabilityEventMarketMakerAdverseSelectionReport(
        spread_probability=spread_probability,
        recent_price_move_probability=recent_price_move_probability,
        depth_imbalance_probability=depth_imbalance_probability,
        source_freshness_age_hours=source_freshness_age_hours,
        forecast_age_hours=forecast_age_hours,
    )


def probability_event_market_maker_adverse_selection_payload_digest(
    payload: ProbabilityEventMarketMakerAdverseSelectionReport | Mapping[str, object],
) -> str:
    if type(payload) is ProbabilityEventMarketMakerAdverseSelectionReport:
        public_payload = payload.public_payload
    elif isinstance(payload, Mapping):
        public_payload = dict(payload)
    else:
        raise ValueError("payload must be a report or mapping")
    _validate_public_payload(public_payload)
    without_digest = dict(public_payload)
    without_digest["payload_digest"] = ""
    digest = _payload_digest(without_digest)
    if public_payload["payload_digest"] != digest:
        raise ValueError("payload_digest must match public payload")
    return digest


def _adverse_selection_score(
    report: ProbabilityEventMarketMakerAdverseSelectionReport,
) -> Decimal:
    return _clamp_probability(
        report.spread_probability * SPREAD_WEIGHT
        + report.recent_price_move_probability * PRICE_MOVE_WEIGHT
        + report.depth_imbalance_probability * DEPTH_IMBALANCE_WEIGHT
        + report.source_freshness_age_hours * SOURCE_AGE_WEIGHT
        + report.forecast_age_hours * FORECAST_AGE_WEIGHT,
    )


def _risk_adjusted_edge_probability(
    report: ProbabilityEventMarketMakerAdverseSelectionReport,
) -> Decimal:
    return _quantize(max(ZERO, ONE - _adverse_selection_score(report)))


def _adverse_selection_status(
    report: ProbabilityEventMarketMakerAdverseSelectionReport,
) -> str:
    reasons = _reason_codes(report)
    if any(reason.endswith("_block") for reason in reasons):
        return BLOCK
    if any(reason.endswith("_watch") for reason in reasons):
        return WATCH
    return PASS


def _reason_codes(
    report: ProbabilityEventMarketMakerAdverseSelectionReport,
) -> tuple[str, ...]:
    reasons: list[str] = []
    score = _adverse_selection_score(report)
    _append_threshold_reason(
        reasons,
        score,
        watch=SCORE_WATCH,
        block=SCORE_BLOCK,
        watch_code="adverse_selection_score_watch",
        block_code="adverse_selection_score_block",
    )
    _append_threshold_reason(
        reasons,
        report.spread_probability,
        watch=SPREAD_WATCH,
        block=SPREAD_BLOCK,
        watch_code="spread_probability_watch",
        block_code="spread_probability_block",
    )
    _append_threshold_reason(
        reasons,
        report.recent_price_move_probability,
        watch=PRICE_MOVE_WATCH,
        block=PRICE_MOVE_BLOCK,
        watch_code="recent_price_move_probability_watch",
        block_code="recent_price_move_probability_block",
    )
    _append_threshold_reason(
        reasons,
        report.depth_imbalance_probability,
        watch=DEPTH_IMBALANCE_WATCH,
        block=DEPTH_IMBALANCE_BLOCK,
        watch_code="depth_imbalance_probability_watch",
        block_code="depth_imbalance_probability_block",
    )
    _append_threshold_reason(
        reasons,
        report.source_freshness_age_hours,
        watch=SOURCE_AGE_WATCH_HOURS,
        block=SOURCE_AGE_BLOCK_HOURS,
        watch_code="source_freshness_age_watch",
        block_code="source_freshness_age_block",
    )
    _append_threshold_reason(
        reasons,
        report.forecast_age_hours,
        watch=FORECAST_AGE_WATCH_HOURS,
        block=FORECAST_AGE_BLOCK_HOURS,
        watch_code="forecast_age_watch",
        block_code="forecast_age_block",
    )
    if reasons:
        return tuple(sorted(reasons))
    return ("adverse_selection_pass",)


def _append_threshold_reason(
    reasons: list[str],
    value: Decimal,
    *,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value >= block:
        reasons.append(block_code)
    elif value > watch:
        reasons.append(watch_code)


def _manual_next_step_for(status: str) -> str:
    if status == BLOCK:
        return "pause_until_manual_adverse_selection_clearance"
    if status == WATCH:
        return "manual_review_market_maker_adverse_selection"
    return "continue_public_research_review"


def _payload_items(
    report: ProbabilityEventMarketMakerAdverseSelectionReport,
    *,
    digest: str,
) -> dict[str, object]:
    return {
        "spread_probability": _decimal_text(report.spread_probability),
        "recent_price_move_probability": _decimal_text(
            report.recent_price_move_probability,
        ),
        "depth_imbalance_probability": _decimal_text(report.depth_imbalance_probability),
        "source_freshness_age_hours": _decimal_text(report.source_freshness_age_hours),
        "forecast_age_hours": _decimal_text(report.forecast_age_hours),
        "adverse_selection_status": report.adverse_selection_status,
        "risk_adjusted_edge_probability": _decimal_text(
            report.risk_adjusted_edge_probability,
        ),
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "payload_digest": digest,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match public schema")
    _reject_numeric_payload_values(payload)
    for field_name in (
        "spread_probability",
        "recent_price_move_probability",
        "depth_imbalance_probability",
        "risk_adjusted_edge_probability",
    ):
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if _decimal_text(_require_probability_decimal(field_name, Decimal(payload[field_name]))) != payload[field_name]:
            raise ValueError(f"{field_name} must be quantized")
    for field_name in ("source_freshness_age_hours", "forecast_age_hours"):
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        if _decimal_text(_require_nonnegative_decimal(field_name, Decimal(payload[field_name]))) != payload[field_name]:
            raise ValueError(f"{field_name} must be quantized")
    if payload["adverse_selection_status"] not in STATUS_VALUES:
        raise ValueError("adverse_selection_status must be pass, watch, or block")
    _normalize_reason_codes("reason_codes", payload["reason_codes"])
    _require_public_code("manual_next_step", payload["manual_next_step"])
    _require_hard_flags(_DictFlags(payload))
    _require_digest("payload_digest", payload["payload_digest"])


def _reject_numeric_payload_values(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_numeric_payload_values(item)
    elif isinstance(value, tuple):
        for item in value:
            _reject_numeric_payload_values(item)
    elif type(value) in (int, float):
        raise ValueError("payload must not contain numeric values")


def _payload_digest(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    quantized = _quantize(value)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    quantized = _quantize(value)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _clamp_probability(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _decimal_text(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(sorted(values))
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_public_code(field_name, value)
    return normalized


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a public code")
    for char in value:
        if not (char == "_" or char.isdigit() or "a" <= char <= "z"):
            raise ValueError(f"{field_name} must be a public code")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex string")
    for char in value:
        if not (char.isdigit() or "a" <= char <= "f"):
            raise ValueError(f"{field_name} must be a sha256 hex string")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
