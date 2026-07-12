from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

STATUS_NORMAL = "normal"
STATUS_WATCH = "watch"
STATUS_RISK = "risk"

NEXT_STEP_BY_STATUS = {
    STATUS_NORMAL: "continue_manual_monitoring",
    STATUS_WATCH: "manual_review_before_new_paper_research",
    STATUS_RISK: "manual_liquidity_volatility_review_required",
}


@dataclass(frozen=True)
class MarketLiquidityVolatilityRegimeReport:
    spread_probability: Decimal
    depth_probability: Decimal
    recent_volatility_probability: Decimal
    volume_change_probability: Decimal
    market_close_hours: Decimal
    regime_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not MarketLiquidityVolatilityRegimeReport:
            raise TypeError("MarketLiquidityVolatilityRegimeReport may not be subclassed")
        for field_name in (
            "spread_probability",
            "depth_probability",
            "recent_volatility_probability",
            "volume_change_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_nonnegative_decimal("market_close_hours", self.market_close_hours),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")

        expected_reason_codes = _reason_codes(
            spread_probability=self.spread_probability,
            depth_probability=self.depth_probability,
            recent_volatility_probability=self.recent_volatility_probability,
            volume_change_probability=self.volume_change_probability,
            market_close_hours=self.market_close_hours,
        )
        expected_status = _regime_status(expected_reason_codes)
        expected_next_step = NEXT_STEP_BY_STATUS[expected_status]

        if self.regime_status != expected_status:
            raise ValueError("regime_status must match liquidity volatility inputs")
        if self.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match liquidity volatility inputs")
        if self.manual_next_step != expected_next_step:
            raise ValueError("manual_next_step must match regime_status")

        expected_digest = _digest(_base_public_payload(self))
        if self.payload_digest:
            _require_digest("payload_digest", self.payload_digest)
            if self.payload_digest != expected_digest:
                raise ValueError("payload_digest must match public_payload")
        else:
            object.__setattr__(self, "payload_digest", expected_digest)

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _base_public_payload(self)
        payload["payload_digest"] = self.payload_digest
        if self.payload_digest != _digest(_base_public_payload(self)):
            raise ValueError("payload_digest must match public_payload")
        return payload


def build_market_liquidity_volatility_regime_report(
    *,
    spread_probability: Decimal,
    depth_probability: Decimal,
    recent_volatility_probability: Decimal,
    volume_change_probability: Decimal,
    market_close_hours: Decimal,
) -> MarketLiquidityVolatilityRegimeReport:
    normalized_spread_probability = _require_probability(
        "spread_probability",
        spread_probability,
    )
    normalized_depth_probability = _require_probability(
        "depth_probability",
        depth_probability,
    )
    normalized_recent_volatility_probability = _require_probability(
        "recent_volatility_probability",
        recent_volatility_probability,
    )
    normalized_volume_change_probability = _require_probability(
        "volume_change_probability",
        volume_change_probability,
    )
    normalized_market_close_hours = _require_nonnegative_decimal(
        "market_close_hours",
        market_close_hours,
    )
    reason_codes = _reason_codes(
        spread_probability=normalized_spread_probability,
        depth_probability=normalized_depth_probability,
        recent_volatility_probability=normalized_recent_volatility_probability,
        volume_change_probability=normalized_volume_change_probability,
        market_close_hours=normalized_market_close_hours,
    )
    regime_status = _regime_status(reason_codes)
    return MarketLiquidityVolatilityRegimeReport(
        spread_probability=normalized_spread_probability,
        depth_probability=normalized_depth_probability,
        recent_volatility_probability=normalized_recent_volatility_probability,
        volume_change_probability=normalized_volume_change_probability,
        market_close_hours=normalized_market_close_hours,
        regime_status=regime_status,
        reason_codes=reason_codes,
        manual_next_step=NEXT_STEP_BY_STATUS[regime_status],
    )


def _reason_codes(
    *,
    spread_probability: Decimal,
    depth_probability: Decimal,
    recent_volatility_probability: Decimal,
    volume_change_probability: Decimal,
    market_close_hours: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_probability_reason(
        reason_codes,
        "spread_probability",
        spread_probability,
        high_threshold=Decimal("0.700000"),
        watch_threshold=Decimal("0.400000"),
    )
    _append_probability_reason(
        reason_codes,
        "depth_probability",
        depth_probability,
        high_threshold=Decimal("0.700000"),
        watch_threshold=Decimal("0.400000"),
    )
    _append_probability_reason(
        reason_codes,
        "recent_volatility_probability",
        recent_volatility_probability,
        high_threshold=Decimal("0.700000"),
        watch_threshold=Decimal("0.400000"),
    )
    _append_probability_reason(
        reason_codes,
        "volume_change_probability",
        volume_change_probability,
        high_threshold=Decimal("0.750000"),
        watch_threshold=Decimal("0.400000"),
    )
    if market_close_hours <= Decimal("6.000000"):
        reason_codes.append("market_close_hours_urgent")
    elif market_close_hours <= Decimal("24.000000"):
        reason_codes.append("market_close_hours_watch")
    if not reason_codes:
        return ("liquidity_volatility_regime_clear",)
    return tuple(reason_codes)


def _append_probability_reason(
    reason_codes: list[str],
    field_name: str,
    value: Decimal,
    *,
    high_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if value >= high_threshold:
        reason_codes.append(f"{field_name}_high")
    elif value >= watch_threshold:
        reason_codes.append(f"{field_name}_watch")


def _regime_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_high") or reason_code.endswith("_urgent") for reason_code in reason_codes):
        return STATUS_RISK
    if reason_codes != ("liquidity_volatility_regime_clear",):
        return STATUS_WATCH
    return STATUS_NORMAL


def _base_public_payload(report: MarketLiquidityVolatilityRegimeReport) -> dict[str, Any]:
    return {
        "spread_probability": _decimal_payload(report.spread_probability),
        "depth_probability": _decimal_payload(report.depth_probability),
        "recent_volatility_probability": _decimal_payload(
            report.recent_volatility_probability,
        ),
        "volume_change_probability": _decimal_payload(report.volume_change_probability),
        "market_close_hours": _decimal_payload(report.market_close_hours),
        "regime_status": report.regime_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _decimal_payload(value: Decimal) -> str:
    return format(value.quantize(QUANT), "f")


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANT)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
