"""Pure paper report live data gap audit reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "StrategyMarketLiveDataGapAuditV10Input",
    "StrategyMarketLiveDataGapAuditV10Result",
    "audit_strategy_market_live_data_gap_v10",
    "build_strategy_market_live_data_gap_audit_v10_result",
    "evaluate_strategy_market_live_data_gap_audit_v10",
    "strategy_market_live_data_gap_audit_v10_payload",
)


VALUE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MARKET_SNAPSHOT_AGING_MINUTES = Decimal("5.000000")
MARKET_SNAPSHOT_STALE_MINUTES = Decimal("15.000000")
MARKET_SNAPSHOT_CRITICAL_MINUTES = Decimal("60.000000")
PRIMARY_SOURCE_AGING_MINUTES = Decimal("30.000000")
PRIMARY_SOURCE_STALE_MINUTES = Decimal("120.000000")
PRIMARY_SOURCE_CRITICAL_MINUTES = Decimal("360.000000")
ORDERBOOK_DEPTH_AGING_MINUTES = Decimal("5.000000")
ORDERBOOK_DEPTH_STALE_MINUTES = Decimal("15.000000")
ORDERBOOK_DEPTH_CRITICAL_MINUTES = Decimal("60.000000")
NEAR_RESOLUTION_MINUTES = Decimal("240.000000")
IMMINENT_RESOLUTION_MINUTES = Decimal("60.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DATA_GAP_STATUSES = ("complete", "watch", "incomplete", "critical")
REFRESH_PRIORITIES = ("monitor", "normal", "high", "urgent")
MISSING_DATA_TYPES = (
    "source_family_quorum",
    "market_snapshot",
    "primary_source",
    "orderbook_depth",
)
REASON_CODES = (
    "live_data_gap_audit_clear",
    "live_data_gap_watch",
    "live_data_gap_incomplete",
    "live_data_gap_critical",
    "market_snapshot_aging",
    "market_snapshot_stale",
    "market_snapshot_critical",
    "orderbook_depth_aging",
    "orderbook_depth_stale",
    "orderbook_depth_critical",
    "primary_source_aging",
    "primary_source_stale",
    "primary_source_critical",
    "resolution_near",
    "resolution_imminent",
    "source_family_count_below_required",
    "source_family_count_zero",
)


@dataclass(frozen=True)
class StrategyMarketLiveDataGapAuditV10Input:
    market_id: str
    source_family_count: Decimal
    required_source_family_count: Decimal
    last_market_snapshot_minutes: Decimal
    last_primary_source_minutes: Decimal
    last_orderbook_depth_minutes: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "source_family_count",
            _normalize_nonnegative_whole_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "required_source_family_count",
            _normalize_positive_whole_decimal(
                "required_source_family_count",
                self.required_source_family_count,
            ),
        )
        for field_name in (
            "last_market_snapshot_minutes",
            "last_primary_source_minutes",
            "last_orderbook_depth_minutes",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketLiveDataGapAuditV10Result:
    market_id: str
    source_family_count: Decimal
    required_source_family_count: Decimal
    last_market_snapshot_minutes: Decimal
    last_primary_source_minutes: Decimal
    last_orderbook_depth_minutes: Decimal
    time_to_resolution_minutes: Decimal
    data_gap_status: str
    missing_data_types: tuple[str, ...]
    refresh_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "source_family_count",
            _normalize_nonnegative_whole_decimal(
                "source_family_count",
                self.source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "required_source_family_count",
            _normalize_positive_whole_decimal(
                "required_source_family_count",
                self.required_source_family_count,
            ),
        )
        for field_name in (
            "last_market_snapshot_minutes",
            "last_primary_source_minutes",
            "last_orderbook_depth_minutes",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "data_gap_status",
            _normalize_choice(
                "data_gap_status",
                self.data_gap_status,
                DATA_GAP_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "missing_data_types",
            _normalize_missing_data_types(self.missing_data_types),
        )
        object.__setattr__(
            self,
            "refresh_priority",
            _normalize_choice(
                "refresh_priority",
                self.refresh_priority,
                REFRESH_PRIORITIES,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result_derivations(self)
        _require_paper_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_market_live_data_gap_audit_v10_payload(self)


def audit_strategy_market_live_data_gap_v10(
    input_row: StrategyMarketLiveDataGapAuditV10Input,
) -> StrategyMarketLiveDataGapAuditV10Result:
    if type(input_row) is not StrategyMarketLiveDataGapAuditV10Input:
        raise ValueError(
            "input_row must be a StrategyMarketLiveDataGapAuditV10Input",
        )
    _require_paper_flags("input", input_row)

    data_gap_status = _data_gap_status(input_row)
    return StrategyMarketLiveDataGapAuditV10Result(
        market_id=input_row.market_id,
        source_family_count=input_row.source_family_count,
        required_source_family_count=input_row.required_source_family_count,
        last_market_snapshot_minutes=input_row.last_market_snapshot_minutes,
        last_primary_source_minutes=input_row.last_primary_source_minutes,
        last_orderbook_depth_minutes=input_row.last_orderbook_depth_minutes,
        time_to_resolution_minutes=input_row.time_to_resolution_minutes,
        data_gap_status=data_gap_status,
        missing_data_types=_missing_data_types(input_row),
        refresh_priority=_refresh_priority(data_gap_status),
        reason_codes=_reason_codes(input_row, data_gap_status),
    )


def build_strategy_market_live_data_gap_audit_v10_result(
    input_row: StrategyMarketLiveDataGapAuditV10Input,
) -> StrategyMarketLiveDataGapAuditV10Result:
    return audit_strategy_market_live_data_gap_v10(input_row)


def evaluate_strategy_market_live_data_gap_audit_v10(
    input_row: StrategyMarketLiveDataGapAuditV10Input,
) -> StrategyMarketLiveDataGapAuditV10Result:
    return audit_strategy_market_live_data_gap_v10(input_row)


def strategy_market_live_data_gap_audit_v10_payload(
    result: StrategyMarketLiveDataGapAuditV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyMarketLiveDataGapAuditV10Result:
        raise ValueError(
            "result must be a StrategyMarketLiveDataGapAuditV10Result",
        )
    _require_paper_flags("result", result)
    return {
        "market_id": result.market_id,
        "source_family_count": _decimal_payload(result.source_family_count),
        "required_source_family_count": _decimal_payload(
            result.required_source_family_count,
        ),
        "last_market_snapshot_minutes": _decimal_payload(
            result.last_market_snapshot_minutes,
        ),
        "last_primary_source_minutes": _decimal_payload(
            result.last_primary_source_minutes,
        ),
        "last_orderbook_depth_minutes": _decimal_payload(
            result.last_orderbook_depth_minutes,
        ),
        "time_to_resolution_minutes": _decimal_payload(
            result.time_to_resolution_minutes,
        ),
        "data_gap_status": result.data_gap_status,
        "missing_data_types": list(result.missing_data_types),
        "refresh_priority": result.refresh_priority,
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _data_gap_status(input_row: StrategyMarketLiveDataGapAuditV10Input) -> str:
    critical_condition = (
        input_row.source_family_count == ZERO
        or input_row.last_market_snapshot_minutes >= MARKET_SNAPSHOT_CRITICAL_MINUTES
        or input_row.last_primary_source_minutes >= PRIMARY_SOURCE_CRITICAL_MINUTES
        or input_row.last_orderbook_depth_minutes >= ORDERBOOK_DEPTH_CRITICAL_MINUTES
        or (
            input_row.time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES
            and (
                input_row.source_family_count < input_row.required_source_family_count
                or input_row.last_market_snapshot_minutes >= MARKET_SNAPSHOT_STALE_MINUTES
                or input_row.last_primary_source_minutes >= PRIMARY_SOURCE_STALE_MINUTES
                or input_row.last_orderbook_depth_minutes >= ORDERBOOK_DEPTH_STALE_MINUTES
            )
        )
    )
    if critical_condition:
        return "critical"
    if (
        input_row.source_family_count < input_row.required_source_family_count
        or input_row.last_market_snapshot_minutes >= MARKET_SNAPSHOT_STALE_MINUTES
        or input_row.last_primary_source_minutes >= PRIMARY_SOURCE_STALE_MINUTES
        or input_row.last_orderbook_depth_minutes >= ORDERBOOK_DEPTH_STALE_MINUTES
    ):
        return "incomplete"
    if (
        input_row.last_market_snapshot_minutes >= MARKET_SNAPSHOT_AGING_MINUTES
        or input_row.last_primary_source_minutes >= PRIMARY_SOURCE_AGING_MINUTES
        or input_row.last_orderbook_depth_minutes >= ORDERBOOK_DEPTH_AGING_MINUTES
    ):
        return "watch"
    return "complete"


def _refresh_priority(data_gap_status: str) -> str:
    if data_gap_status == "critical":
        return "urgent"
    if data_gap_status == "incomplete":
        return "high"
    if data_gap_status == "watch":
        return "normal"
    if data_gap_status == "complete":
        return "monitor"
    raise ValueError("data_gap_status is not supported")


def _missing_data_types(
    input_row: StrategyMarketLiveDataGapAuditV10Input,
) -> tuple[str, ...]:
    missing: list[str] = []
    if input_row.source_family_count < input_row.required_source_family_count:
        missing.append("source_family_quorum")
    if input_row.last_market_snapshot_minutes >= MARKET_SNAPSHOT_AGING_MINUTES:
        missing.append("market_snapshot")
    if input_row.last_primary_source_minutes >= PRIMARY_SOURCE_AGING_MINUTES:
        missing.append("primary_source")
    if input_row.last_orderbook_depth_minutes >= ORDERBOOK_DEPTH_AGING_MINUTES:
        missing.append("orderbook_depth")
    return tuple(missing)


def _reason_codes(
    input_row: StrategyMarketLiveDataGapAuditV10Input,
    data_gap_status: str,
) -> tuple[str, ...]:
    if data_gap_status == "complete":
        return ("live_data_gap_audit_clear",)

    codes: list[str] = [f"live_data_gap_{data_gap_status}"]
    codes.extend(_market_snapshot_reason_codes(input_row.last_market_snapshot_minutes))
    codes.extend(_orderbook_depth_reason_codes(input_row.last_orderbook_depth_minutes))
    codes.extend(_primary_source_reason_codes(input_row.last_primary_source_minutes))
    codes.extend(_resolution_reason_codes(input_row.time_to_resolution_minutes))
    codes.extend(
        _source_family_reason_codes(
            input_row.source_family_count,
            input_row.required_source_family_count,
        ),
    )
    return _normalize_reason_codes(tuple(codes))


def _market_snapshot_reason_codes(age_minutes: Decimal) -> tuple[str, ...]:
    if age_minutes >= MARKET_SNAPSHOT_CRITICAL_MINUTES:
        return ("market_snapshot_critical",)
    if age_minutes >= MARKET_SNAPSHOT_STALE_MINUTES:
        return ("market_snapshot_stale",)
    if age_minutes >= MARKET_SNAPSHOT_AGING_MINUTES:
        return ("market_snapshot_aging",)
    return ()


def _orderbook_depth_reason_codes(age_minutes: Decimal) -> tuple[str, ...]:
    if age_minutes >= ORDERBOOK_DEPTH_CRITICAL_MINUTES:
        return ("orderbook_depth_critical",)
    if age_minutes >= ORDERBOOK_DEPTH_STALE_MINUTES:
        return ("orderbook_depth_stale",)
    if age_minutes >= ORDERBOOK_DEPTH_AGING_MINUTES:
        return ("orderbook_depth_aging",)
    return ()


def _primary_source_reason_codes(age_minutes: Decimal) -> tuple[str, ...]:
    if age_minutes >= PRIMARY_SOURCE_CRITICAL_MINUTES:
        return ("primary_source_critical",)
    if age_minutes >= PRIMARY_SOURCE_STALE_MINUTES:
        return ("primary_source_stale",)
    if age_minutes >= PRIMARY_SOURCE_AGING_MINUTES:
        return ("primary_source_aging",)
    return ()


def _resolution_reason_codes(time_to_resolution_minutes: Decimal) -> tuple[str, ...]:
    if time_to_resolution_minutes <= IMMINENT_RESOLUTION_MINUTES:
        return ("resolution_imminent",)
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return ("resolution_near",)
    return ()


def _source_family_reason_codes(
    source_family_count: Decimal,
    required_source_family_count: Decimal,
) -> tuple[str, ...]:
    if source_family_count == ZERO:
        return ("source_family_count_zero",)
    if source_family_count < required_source_family_count:
        return ("source_family_count_below_required",)
    return ()


def _validate_result_derivations(
    result: StrategyMarketLiveDataGapAuditV10Result,
) -> None:
    input_row = StrategyMarketLiveDataGapAuditV10Input(
        market_id=result.market_id,
        source_family_count=result.source_family_count,
        required_source_family_count=result.required_source_family_count,
        last_market_snapshot_minutes=result.last_market_snapshot_minutes,
        last_primary_source_minutes=result.last_primary_source_minutes,
        last_orderbook_depth_minutes=result.last_orderbook_depth_minutes,
        time_to_resolution_minutes=result.time_to_resolution_minutes,
    )
    expected_status = _data_gap_status(input_row)
    if result.data_gap_status != expected_status:
        raise ValueError("data_gap_status must match inputs")
    if result.refresh_priority != _refresh_priority(expected_status):
        raise ValueError("refresh_priority must match data_gap_status")
    if result.missing_data_types != _missing_data_types(input_row):
        raise ValueError("missing_data_types must match inputs")
    if result.reason_codes != _reason_codes(input_row, expected_status):
        raise ValueError("reason_codes must match inputs")


def _normalize_nonnegative_whole_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(VALUE_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} precision is too granular")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _normalize_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of the allowed values")
    return value


def _normalize_missing_data_types(value: object) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "missing_data_types",
        value,
        MISSING_DATA_TYPES,
        allow_empty=True,
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "reason_codes",
        value,
        REASON_CODES,
        allow_empty=False,
    )


def _normalize_string_tuple(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in allowed_values:
            raise ValueError(f"{field_name} must contain supported values")
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return format(value, "f")
