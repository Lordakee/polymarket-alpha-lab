import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_READY_SOURCE_MIN = Decimal("2.000000")
_STALE_HOURS_MIN = Decimal("6.000000")
_MOVE_WATCH_MIN = Decimal("0.100000")

__all__ = (
    "MarketDataRefreshFailureFallbackReport",
    "build_market_data_refresh_failure_fallback_report",
)


@dataclass(frozen=True)
class MarketDataRefreshFailureFallbackReport:
    primary_refresh_failed: bool
    fallback_source_count: Decimal
    last_success_age_hours: Decimal
    market_move_probability: Decimal
    manual_refresh_owner_present: bool
    fallback_status: str = ""
    reason_codes: tuple[str, ...] = ()
    manual_next_step: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketDataRefreshFailureFallbackReport:
            raise TypeError(
                "MarketDataRefreshFailureFallbackReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketDataRefreshFailureFallbackReport:
            raise ValueError(
                "report must be exactly MarketDataRefreshFailureFallbackReport",
            )
        _require_bool("primary_refresh_failed", self.primary_refresh_failed)
        _require_bool(
            "manual_refresh_owner_present",
            self.manual_refresh_owner_present,
        )
        object.__setattr__(
            self,
            "fallback_source_count",
            _require_count_decimal("fallback_source_count", self.fallback_source_count),
        )
        object.__setattr__(
            self,
            "last_success_age_hours",
            _require_count_decimal("last_success_age_hours", self.last_success_age_hours),
        )
        object.__setattr__(
            self,
            "market_move_probability",
            _require_ratio_decimal(
                "market_move_probability",
                self.market_move_probability,
            ),
        )
        _require_flags(self)

        expected_status = _fallback_status(
            primary_refresh_failed=self.primary_refresh_failed,
            fallback_source_count=self.fallback_source_count,
            last_success_age_hours=self.last_success_age_hours,
            market_move_probability=self.market_move_probability,
            manual_refresh_owner_present=self.manual_refresh_owner_present,
        )
        expected_reasons = _reason_codes(
            primary_refresh_failed=self.primary_refresh_failed,
            fallback_source_count=self.fallback_source_count,
            last_success_age_hours=self.last_success_age_hours,
            market_move_probability=self.market_move_probability,
            manual_refresh_owner_present=self.manual_refresh_owner_present,
        )
        expected_step = _manual_next_step(
            fallback_status=expected_status,
            fallback_source_count=self.fallback_source_count,
            manual_refresh_owner_present=self.manual_refresh_owner_present,
        )

        if self.fallback_status:
            _require_known_status(self.fallback_status)
            if self.fallback_status != expected_status:
                raise ValueError("fallback_status must match refresh failure inputs")
        else:
            object.__setattr__(self, "fallback_status", expected_status)

        if self.reason_codes:
            normalized_reasons = _normalize_reason_codes(self.reason_codes)
            if normalized_reasons != expected_reasons:
                raise ValueError("reason_codes must match refresh failure inputs")
            object.__setattr__(self, "reason_codes", normalized_reasons)
        else:
            object.__setattr__(self, "reason_codes", expected_reasons)

        if self.manual_next_step:
            _require_known_step(self.manual_next_step)
            if self.manual_next_step != expected_step:
                raise ValueError("manual_next_step must match refresh failure inputs")
        else:
            object.__setattr__(self, "manual_next_step", expected_step)

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _payload_without_digest(self)
        payload["payload_digest"] = self.payload_digest
        return payload

    @property
    def payload_digest(self) -> str:
        encoded = json.dumps(
            _payload_without_digest(self),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def build_market_data_refresh_failure_fallback_report(
    *,
    primary_refresh_failed: bool,
    fallback_source_count: Decimal,
    last_success_age_hours: Decimal,
    market_move_probability: Decimal,
    manual_refresh_owner_present: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketDataRefreshFailureFallbackReport:
    return MarketDataRefreshFailureFallbackReport(
        primary_refresh_failed=primary_refresh_failed,
        fallback_source_count=fallback_source_count,
        last_success_age_hours=last_success_age_hours,
        market_move_probability=market_move_probability,
        manual_refresh_owner_present=manual_refresh_owner_present,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _payload_without_digest(
    report: MarketDataRefreshFailureFallbackReport,
) -> dict[str, Any]:
    return {
        "primary_refresh_failed": report.primary_refresh_failed,
        "fallback_source_count": _decimal_text(report.fallback_source_count),
        "last_success_age_hours": _decimal_text(report.last_success_age_hours),
        "market_move_probability": _decimal_text(report.market_move_probability),
        "manual_refresh_owner_present": report.manual_refresh_owner_present,
        "fallback_status": report.fallback_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _fallback_status(
    *,
    primary_refresh_failed: bool,
    fallback_source_count: Decimal,
    last_success_age_hours: Decimal,
    market_move_probability: Decimal,
    manual_refresh_owner_present: bool,
) -> str:
    if not primary_refresh_failed:
        return "not_needed"
    if not manual_refresh_owner_present or fallback_source_count == _ZERO:
        return "blocked"
    if (
        fallback_source_count < _READY_SOURCE_MIN
        or last_success_age_hours > _STALE_HOURS_MIN
        or market_move_probability >= _MOVE_WATCH_MIN
    ):
        return "watch"
    return "ready"


def _reason_codes(
    *,
    primary_refresh_failed: bool,
    fallback_source_count: Decimal,
    last_success_age_hours: Decimal,
    market_move_probability: Decimal,
    manual_refresh_owner_present: bool,
) -> tuple[str, ...]:
    if not primary_refresh_failed:
        return ("primary_refresh_available",)

    reasons: list[str] = ["primary_refresh_failed"]
    if fallback_source_count == _ZERO:
        reasons.append("fallback_sources_missing")
    elif fallback_source_count < _READY_SOURCE_MIN:
        reasons.append("single_fallback_source")
    else:
        reasons.append("fallback_sources_available")

    if manual_refresh_owner_present:
        reasons.append("manual_owner_present")
    else:
        reasons.append("manual_owner_missing")

    if last_success_age_hours > _STALE_HOURS_MIN:
        reasons.append("last_success_stale")
    if market_move_probability >= _MOVE_WATCH_MIN:
        reasons.append("market_move_watch")
    return tuple(reasons)


def _manual_next_step(
    *,
    fallback_status: str,
    fallback_source_count: Decimal,
    manual_refresh_owner_present: bool,
) -> str:
    if fallback_status == "not_needed":
        return "no_manual_fallback_needed"
    if not manual_refresh_owner_present:
        return "assign_manual_refresh_owner"
    if fallback_source_count == _ZERO:
        return "collect_fallback_sources"
    if fallback_source_count < _READY_SOURCE_MIN:
        return "verify_single_fallback_source"
    if fallback_status == "watch":
        return "review_stale_or_moving_market"
    return "prepare_manual_refresh_packet"


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite() or value < _ZERO:
        raise ValueError(f"{name} must be a nonnegative Decimal")
    return value.quantize(_QUANT)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    checked = _require_count_decimal(name, value)
    if checked > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return checked


def _require_flags(report: MarketDataRefreshFailureFallbackReport) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        value = getattr(report, name)
        if value is not True:
            raise ValueError(f"{name} must be True")


def _require_known_status(value: str) -> None:
    if value not in ("not_needed", "ready", "watch", "blocked"):
        raise ValueError("fallback_status is not supported")


def _require_known_step(value: str) -> None:
    if value not in (
        "assign_manual_refresh_owner",
        "collect_fallback_sources",
        "no_manual_fallback_needed",
        "prepare_manual_refresh_packet",
        "review_stale_or_moving_market",
        "verify_single_fallback_source",
    ):
        raise ValueError("manual_next_step is not supported")


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError("reason_codes must contain non-empty strings")
    return value


def _decimal_text(value: Decimal) -> str:
    return f"{value.quantize(_QUANT):f}"
