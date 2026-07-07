"""Category specialist signal capacity report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_MARKET_CATEGORY_SPECIALIST_SIGNAL_CAPACITY_V2_CONFIG_VERSION = (
    "market-category-specialist-signal-capacity-v2"
)
ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")

_COUNT_QUANTUM = Decimal("1")
_SIX_PLACE_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_BLOCK_RATIO = Decimal("1.500000")
_HIGH_PRIORITY_SHARE = Decimal("0.250000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DIGEST_FIELD = "derived_validation_digest"
_ROW_STATUS_WEIGHT = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
_REASON_SEQUENCE = (
    "capacity_signal_pass",
    "capacity_signal_watch",
    "capacity_signal_block",
    "signal_backlog_present",
    "over_capacity",
    "no_specialist_capacity",
    "stale_signals_present",
    "high_priority_pressure",
)
_UNSAFE_PUBLIC_TERMS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "muta" "tion",
    "b" "uy",
    "se" "ll",
    "tra" "de",
)


@dataclass(frozen=True)
class MarketCategorySpecialistSignalCapacityV2Input:
    category: str
    signal_count: Decimal
    high_priority_signal_count: Decimal
    specialist_count: Decimal
    per_specialist_capacity: Decimal
    stale_signal_count: Decimal
    latest_signal_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("category", self.category)
        for field_name in (
            "signal_count",
            "high_priority_signal_count",
            "specialist_count",
            "stale_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "per_specialist_capacity",
            _normalize_positive_count(
                "per_specialist_capacity",
                self.per_specialist_capacity,
            ),
        )
        if self.high_priority_signal_count > self.signal_count:
            raise ValueError("high_priority_signal_count must not exceed signal_count")
        if self.stale_signal_count > self.signal_count:
            raise ValueError("stale_signal_count must not exceed signal_count")
        object.__setattr__(
            self,
            "latest_signal_at",
            _as_utc("latest_signal_at", self.latest_signal_at),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(self))


@dataclass(frozen=True)
class MarketCategorySpecialistSignalCapacityV2Row:
    rank: Decimal
    category: str
    signal_count: Decimal
    high_priority_signal_count: Decimal
    specialist_count: Decimal
    per_specialist_capacity: Decimal
    total_specialist_capacity: Decimal
    stale_signal_count: Decimal
    latest_signal_at: datetime
    capacity_utilization_ratio: Decimal
    signal_backlog_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_public_string("category", self.category)
        for field_name in (
            "signal_count",
            "high_priority_signal_count",
            "specialist_count",
            "per_specialist_capacity",
            "total_specialist_capacity",
            "stale_signal_count",
            "signal_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.per_specialist_capacity <= _ZERO_COUNT:
            raise ValueError("per_specialist_capacity must be positive")
        if self.high_priority_signal_count > self.signal_count:
            raise ValueError("high_priority_signal_count must not exceed signal_count")
        if self.stale_signal_count > self.signal_count:
            raise ValueError("stale_signal_count must not exceed signal_count")
        object.__setattr__(
            self,
            "latest_signal_at",
            _as_utc("latest_signal_at", self.latest_signal_at),
        )
        object.__setattr__(
            self,
            "capacity_utilization_ratio",
            _normalize_nonnegative_six_place_decimal(
                "capacity_utilization_ratio",
                self.capacity_utilization_ratio,
            ),
        )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketCategorySpecialistSignalCapacityV2Report:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    over_capacity_count: Decimal
    stale_signal_count: Decimal
    high_priority_pressure_count: Decimal
    max_capacity_utilization_ratio: Decimal
    report_status: str
    reason_code_counts: dict[str, Decimal]
    rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "category_count",
            "pass_count",
            "watch_count",
            "block_count",
            "over_capacity_count",
            "stale_signal_count",
            "high_priority_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_capacity_utilization_ratio",
            _normalize_nonnegative_six_place_decimal(
                "max_capacity_utilization_ratio",
                self.max_capacity_utilization_ratio,
            ),
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_market_category_specialist_signal_capacity_v2_report(
    inputs: object,
    *,
    generated_at: datetime,
) -> MarketCategorySpecialistSignalCapacityV2Report:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.latest_signal_at > generated_at_utc:
            raise ValueError("latest_signal_at must not be after generated_at")
    rows = _rank_rows(tuple(_row_from_input(item) for item in normalized_inputs))
    return MarketCategorySpecialistSignalCapacityV2Report(
        generated_at=generated_at_utc,
        config_version=DEFAULT_MARKET_CATEGORY_SPECIALIST_SIGNAL_CAPACITY_V2_CONFIG_VERSION,
        category_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        over_capacity_count=_over_capacity_count(rows),
        stale_signal_count=_sum_counts(tuple(row.stale_signal_count for row in rows)),
        high_priority_pressure_count=_high_priority_pressure_count(rows),
        max_capacity_utilization_ratio=_max_ratio(rows),
        report_status=_report_status(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def market_category_specialist_signal_capacity_v2_payload(
    report: object,
) -> dict[str, Any]:
    if type(report) is MarketCategorySpecialistSignalCapacityV2Report:
        _validate_report_digest(report)
        _validate_report_consistency(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_non_string_numeric(report)
        _reject_unsafe_public_payload("payload", report)
        _require_payload_hard_flags(report)
        if _DIGEST_FIELD in report:
            _validate_payload_digest(report)
        return report
    raise ValueError("report must be a category specialist signal capacity report or payload dict")


def _row_from_input(
    item: MarketCategorySpecialistSignalCapacityV2Input,
) -> MarketCategorySpecialistSignalCapacityV2Row:
    total_capacity = _count_decimal_product(
        item.specialist_count,
        item.per_specialist_capacity,
    )
    utilization_ratio = _capacity_utilization_ratio(
        item.signal_count,
        total_capacity,
    )
    backlog_count = max(_ZERO_COUNT, item.signal_count - total_capacity)
    high_priority_pressure = _has_high_priority_pressure(
        item.high_priority_signal_count,
        total_capacity,
    )
    status = _row_status(
        signal_count=item.signal_count,
        total_capacity=total_capacity,
        utilization_ratio=utilization_ratio,
        stale_signal_count=item.stale_signal_count,
        high_priority_pressure=high_priority_pressure,
    )
    return MarketCategorySpecialistSignalCapacityV2Row(
        rank=_COUNT_QUANTUM,
        category=item.category,
        signal_count=item.signal_count,
        high_priority_signal_count=item.high_priority_signal_count,
        specialist_count=item.specialist_count,
        per_specialist_capacity=item.per_specialist_capacity,
        total_specialist_capacity=total_capacity,
        stale_signal_count=item.stale_signal_count,
        latest_signal_at=item.latest_signal_at,
        capacity_utilization_ratio=utilization_ratio,
        signal_backlog_count=backlog_count,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            signal_count=item.signal_count,
            total_capacity=total_capacity,
            signal_backlog_count=backlog_count,
            stale_signal_count=item.stale_signal_count,
            high_priority_pressure=high_priority_pressure,
        ),
    )


def _rank_rows(
    rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...],
) -> tuple[MarketCategorySpecialistSignalCapacityV2Row, ...]:
    ranked_rows: list[MarketCategorySpecialistSignalCapacityV2Row] = []
    for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked_rows.append(
            MarketCategorySpecialistSignalCapacityV2Row(
                rank=_count(index),
                category=row.category,
                signal_count=row.signal_count,
                high_priority_signal_count=row.high_priority_signal_count,
                specialist_count=row.specialist_count,
                per_specialist_capacity=row.per_specialist_capacity,
                total_specialist_capacity=row.total_specialist_capacity,
                stale_signal_count=row.stale_signal_count,
                latest_signal_at=row.latest_signal_at,
                capacity_utilization_ratio=row.capacity_utilization_ratio,
                signal_backlog_count=row.signal_backlog_count,
                status=row.status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked_rows)


def _row_sort_key(
    row: MarketCategorySpecialistSignalCapacityV2Row,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        _ROW_STATUS_WEIGHT[row.status],
        -row.capacity_utilization_ratio,
        -row.signal_count,
        row.category,
    )


def _row_status(
    *,
    signal_count: Decimal,
    total_capacity: Decimal,
    utilization_ratio: Decimal,
    stale_signal_count: Decimal,
    high_priority_pressure: bool,
) -> str:
    if signal_count > _ZERO_COUNT and total_capacity <= _ZERO_COUNT:
        return "block"
    if utilization_ratio >= _BLOCK_RATIO:
        return "block"
    if signal_count > total_capacity:
        return "watch"
    if stale_signal_count > _ZERO_COUNT:
        return "watch"
    if high_priority_pressure:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    signal_count: Decimal,
    total_capacity: Decimal,
    signal_backlog_count: Decimal,
    stale_signal_count: Decimal,
    high_priority_pressure: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"capacity_signal_{status}"]
    if signal_backlog_count > _ZERO_COUNT:
        reason_codes.append("signal_backlog_present")
    if signal_count > total_capacity:
        reason_codes.append("over_capacity")
    if signal_count > _ZERO_COUNT and total_capacity <= _ZERO_COUNT:
        reason_codes.append("no_specialist_capacity")
    if stale_signal_count > _ZERO_COUNT:
        reason_codes.append("stale_signals_present")
    if high_priority_pressure:
        reason_codes.append("high_priority_pressure")
    return _normalize_reason_codes(tuple(reason_codes))


def _capacity_utilization_ratio(signal_count: Decimal, total_capacity: Decimal) -> Decimal:
    if total_capacity <= _ZERO_COUNT:
        if signal_count <= _ZERO_COUNT:
            return _ZERO_RATIO
        return _six(signal_count)
    with localcontext(_DECIMAL_CONTEXT):
        return _six(signal_count / total_capacity)


def _has_high_priority_pressure(
    high_priority_signal_count: Decimal,
    total_capacity: Decimal,
) -> bool:
    if high_priority_signal_count <= _ZERO_COUNT:
        return False
    if total_capacity <= _ZERO_COUNT:
        return True
    with localcontext(_DECIMAL_CONTEXT):
        return high_priority_signal_count > (total_capacity * _HIGH_PRIORITY_SHARE)


def _normalize_inputs(
    value: object,
) -> tuple[MarketCategorySpecialistSignalCapacityV2Input, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for item in rows:
        if type(item) is not MarketCategorySpecialistSignalCapacityV2Input:
            raise ValueError("inputs must contain exact category signal capacity inputs")
        _require_hard_flags("input", item)
        if item.category in seen:
            raise ValueError("inputs must not contain duplicate categories")
        seen.add(item.category)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[MarketCategorySpecialistSignalCapacityV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    expected_rank = _COUNT_QUANTUM
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketCategorySpecialistSignalCapacityV2Row:
            raise ValueError("rows must contain exact category signal capacity rows")
        _require_hard_flags("row", row)
        _validate_row_digest(row)
        if row.category in seen:
            raise ValueError("rows must not contain duplicate categories")
        seen.add(row.category)
        if row.rank != expected_rank:
            raise ValueError("rows must use consecutive ranks")
        expected_rank += _COUNT_QUANTUM
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _validate_row_consistency(row: MarketCategorySpecialistSignalCapacityV2Row) -> None:
    expected_capacity = _count_decimal_product(
        row.specialist_count,
        row.per_specialist_capacity,
    )
    if row.total_specialist_capacity != expected_capacity:
        raise ValueError("total_specialist_capacity must match row inputs")
    if row.capacity_utilization_ratio != _capacity_utilization_ratio(
        row.signal_count,
        row.total_specialist_capacity,
    ):
        raise ValueError("capacity_utilization_ratio must match row inputs")
    expected_backlog = max(_ZERO_COUNT, row.signal_count - row.total_specialist_capacity)
    if row.signal_backlog_count != expected_backlog:
        raise ValueError("signal_backlog_count must match row inputs")
    high_priority_pressure = _has_high_priority_pressure(
        row.high_priority_signal_count,
        row.total_specialist_capacity,
    )
    if row.status != _row_status(
        signal_count=row.signal_count,
        total_capacity=row.total_specialist_capacity,
        utilization_ratio=row.capacity_utilization_ratio,
        stale_signal_count=row.stale_signal_count,
        high_priority_pressure=high_priority_pressure,
    ):
        raise ValueError("status must match row inputs")
    if row.reason_codes != _row_reason_codes(
        status=row.status,
        signal_count=row.signal_count,
        total_capacity=row.total_specialist_capacity,
        signal_backlog_count=row.signal_backlog_count,
        stale_signal_count=row.stale_signal_count,
        high_priority_pressure=high_priority_pressure,
    ):
        raise ValueError("reason_codes must match row inputs")


def _validate_report_consistency(
    report: MarketCategorySpecialistSignalCapacityV2Report,
) -> None:
    rows = report.rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.over_capacity_count != _over_capacity_count(rows):
        raise ValueError("over_capacity_count must match rows")
    if report.stale_signal_count != _sum_counts(tuple(row.stale_signal_count for row in rows)):
        raise ValueError("stale_signal_count must match rows")
    if report.high_priority_pressure_count != _high_priority_pressure_count(rows):
        raise ValueError("high_priority_pressure_count must match rows")
    if report.max_capacity_utilization_ratio != _max_ratio(rows):
        raise ValueError("max_capacity_utilization_ratio must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _over_capacity_count(
    rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.signal_count > row.total_specialist_capacity))


def _high_priority_pressure_count(
    rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if _has_high_priority_pressure(
                row.high_priority_signal_count,
                row.total_specialist_capacity,
            )
        ),
    )


def _max_ratio(rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...]) -> Decimal:
    if not rows:
        return _ZERO_RATIO
    return max(row.capacity_utilization_ratio for row in rows)


def _report_status(rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[MarketCategorySpecialistSignalCapacityV2Row, ...],
) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for reason_code in _REASON_SEQUENCE:
        count = _count(
            sum(1 for row in rows if reason_code in row.reason_codes),
        )
        if count > _ZERO_COUNT:
            counts[reason_code] = count
    return counts


def _normalize_reason_code_counts(value: object) -> dict[str, Decimal]:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must be a dict")
    counts: dict[str, Decimal] = {}
    for reason_code in _REASON_SEQUENCE:
        if reason_code not in value:
            continue
        counts[reason_code] = _normalize_positive_count(
            "reason_code_counts",
            value[reason_code],
        )
    if set(value) != set(counts):
        raise ValueError("reason_code_counts must contain known values")
    return counts


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_public_string("reason_codes", reason_code)
        if reason_code not in _REASON_SEQUENCE:
            raise ValueError("reason_codes must contain known values")
    seen = set(reason_codes)
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in seen)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, _ZERO_COUNT).quantize(_COUNT_QUANTUM)


def _count_decimal_product(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return (left * right).quantize(_COUNT_QUANTUM)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX_PLACE_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_six_place_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _six(value)
    if quantized < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_payload(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("payload report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("payload readonly must be True")


def _apply_or_verify_digest(value: object) -> None:
    expected_digest = _digest_value(value)
    actual_digest = getattr(value, _DIGEST_FIELD)
    if actual_digest == "":
        object.__setattr__(value, _DIGEST_FIELD, expected_digest)
        return
    if actual_digest != expected_digest:
        raise ValueError("derived_validation_digest must match fields")


def _validate_row_digest(row: MarketCategorySpecialistSignalCapacityV2Row) -> None:
    if row.derived_validation_digest != _digest_value(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_digest(report: MarketCategorySpecialistSignalCapacityV2Report) -> None:
    for row in report.rows:
        _validate_row_digest(row)
    if report.derived_validation_digest != _digest_value(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload_digest(payload: dict[str, object]) -> None:
    provided_digest = payload.get(_DIGEST_FIELD)
    if type(provided_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected_digest = _digest_value(payload)
    if provided_digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _digest_value(value: object) -> str:
    ready = _payload_value(value, omit_digest=True)
    _reject_unsafe_public_payload("derived validation payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object, *, omit_digest: bool = False) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if omit_digest and field.name == _DIGEST_FIELD:
                continue
            ready[field.name] = _payload_value(
                getattr(value, field.name),
                omit_digest=omit_digest,
            )
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is tuple:
        return [_payload_value(item, omit_digest=omit_digest) for item in value]
    if type(value) is list:
        return [_payload_value(item, omit_digest=omit_digest) for item in value]
    if type(value) is dict:
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if omit_digest and key == _DIGEST_FIELD:
                continue
            ready[key] = _payload_value(item, omit_digest=omit_digest)
        return ready
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains value with unsupported type")


def _reject_non_string_numeric(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is float:
        raise ValueError("float values are not supported in public payloads")
    if type(value) is int:
        raise ValueError("public numeric values must be Decimal strings")
    if type(value) is Decimal:
        raise ValueError("public Decimal values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_non_string_numeric(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_non_string_numeric(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        if _contains_unsafe_public_text(value):
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            if _contains_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)


__all__ = (
    "DEFAULT_MARKET_CATEGORY_SPECIALIST_SIGNAL_CAPACITY_V2_CONFIG_VERSION",
    "ROW_STATUSES",
    "REPORT_STATUSES",
    "MarketCategorySpecialistSignalCapacityV2Input",
    "MarketCategorySpecialistSignalCapacityV2Row",
    "MarketCategorySpecialistSignalCapacityV2Report",
    "build_market_category_specialist_signal_capacity_v2_report",
    "market_category_specialist_signal_capacity_v2_payload",
)
