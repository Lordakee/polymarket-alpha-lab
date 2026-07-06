"""Readonly Decimal optimizer for specialist capacity allocation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CAPACITY_ALLOCATION_OPTIMIZER_V2_CONFIG_VERSION = (
    "team-specialist-capacity-allocation-optimizer-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
UNIT_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ROW_STATUSES = ("allocate", "watch", "defer")
OPTIMIZER_STATUSES = ("pass", "watch", "defer")
ROW_REASON_CODES = (
    "capacity_allocation_allocate",
    "capacity_allocation_watch",
    "capacity_allocation_defer",
    "queue_priority_high",
    "queue_priority_watch",
    "queue_priority_low",
    "urgency_high",
    "urgency_watch",
    "urgency_low",
    "specialist_fit_strong",
    "specialist_fit_watch",
    "specialist_fit_weak",
    "readiness_ready",
    "readiness_watch",
    "readiness_not_ready",
    "capacity_clear",
    "capacity_limited",
    "capacity_overloaded",
    "overload_penalty_clear",
    "overload_penalty_watch",
    "overload_penalty_high",
)
REPORT_REASON_CODES = (
    "capacity_allocation_optimizer_passed",
    "capacity_allocation_optimizer_watch_rows",
    "capacity_allocation_optimizer_defer_rows",
    "capacity_allocation_optimizer_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CAPACITY_ALLOCATION_OPTIMIZER_V2_CONFIG_VERSION",
    "TeamSpecialistCapacityAllocationOptimizerV2Config",
    "TeamSpecialistCapacityAllocationV2Input",
    "TeamSpecialistCapacityAllocationOptimizerV2Row",
    "TeamSpecialistCapacityAllocationOptimizerV2Report",
    "build_team_specialist_capacity_allocation_optimizer_v2",
    "team_specialist_capacity_allocation_optimizer_v2_payload",
    "validate_team_specialist_capacity_allocation_optimizer_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistCapacityAllocationOptimizerV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CAPACITY_ALLOCATION_OPTIMIZER_V2_CONFIG_VERSION
    )
    capacity_availability_weight: Decimal = Decimal("0.300000")
    queue_priority_weight: Decimal = Decimal("0.250000")
    urgency_weight: Decimal = Decimal("0.200000")
    specialist_fit_weight: Decimal = Decimal("0.150000")
    readiness_weight: Decimal = Decimal("0.100000")
    overload_penalty_weight: Decimal = Decimal("0.250000")
    allocate_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not supported")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "capacity_availability_weight",
            "queue_priority_weight",
            "urgency_weight",
            "specialist_fit_weight",
            "readiness_weight",
            "overload_penalty_weight",
            "allocate_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistCapacityAllocationOptimizerV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCapacityAllocationOptimizerV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCapacityAllocationV2Input:
    specialist_id: str
    queue_id: str
    requested_units: Decimal
    available_capacity_units: Decimal
    current_load_units: Decimal
    queue_priority_score: Decimal
    urgency_score: Decimal
    specialist_fit_score: Decimal
    readiness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not supported")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        object.__setattr__(
            self,
            "queue_id",
            _require_non_empty_string("queue_id", self.queue_id),
        )
        object.__setattr__(
            self,
            "requested_units",
            _normalize_positive_units("requested_units", self.requested_units),
        )
        for field_name in ("available_capacity_units", "current_load_units"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_units(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "queue_priority_score",
            "urgency_score",
            "specialist_fit_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("TeamSpecialistCapacityAllocationV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCapacityAllocationV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCapacityAllocationOptimizerV2Row:
    rank: Decimal
    specialist_id: str
    queue_id: str
    requested_units: Decimal
    available_capacity_units: Decimal
    current_load_units: Decimal
    remaining_capacity_units: Decimal
    allocated_units: Decimal
    overload_units: Decimal
    capacity_fill_ratio: Decimal
    overload_penalty_score: Decimal
    queue_priority_score: Decimal
    urgency_score: Decimal
    specialist_fit_score: Decimal
    readiness_score: Decimal
    allocation_priority_score: Decimal
    allocation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not supported")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_non_empty_string("specialist_id", self.specialist_id),
        )
        object.__setattr__(
            self,
            "queue_id",
            _require_non_empty_string("queue_id", self.queue_id),
        )
        object.__setattr__(
            self,
            "requested_units",
            _normalize_positive_units("requested_units", self.requested_units),
        )
        for field_name in (
            "available_capacity_units",
            "current_load_units",
            "remaining_capacity_units",
            "allocated_units",
            "overload_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_units(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capacity_fill_ratio",
            "overload_penalty_score",
            "queue_priority_score",
            "urgency_score",
            "specialist_fit_score",
            "readiness_score",
            "allocation_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("allocation_status", self.allocation_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistCapacityAllocationOptimizerV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCapacityAllocationOptimizerV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistCapacityAllocationOptimizerV2Report:
    generated_at: datetime
    config_version: str
    optimizer_status: str
    item_count: Decimal
    allocate_count: Decimal
    watch_count: Decimal
    defer_count: Decimal
    total_requested_units: Decimal
    total_allocated_units: Decimal
    total_overload_units: Decimal
    allocation_rate: Decimal
    average_allocation_priority_score: Decimal
    top_allocation_priority_score: Decimal
    bottom_allocation_priority_score: Decimal
    rows: tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("subclassing is not supported")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_member("optimizer_status", self.optimizer_status, OPTIMIZER_STATUSES)
        for field_name in (
            "item_count",
            "allocate_count",
            "watch_count",
            "defer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "total_requested_units",
            "total_allocated_units",
            "total_overload_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_units(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "allocation_rate",
            "average_allocation_priority_score",
            "top_allocation_priority_score",
            "bottom_allocation_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistCapacityAllocationOptimizerV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCapacityAllocationOptimizerV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        return team_specialist_capacity_allocation_optimizer_v2_payload(self)


def build_team_specialist_capacity_allocation_optimizer_v2(
    capacity_items: object,
    *,
    config: TeamSpecialistCapacityAllocationOptimizerV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistCapacityAllocationOptimizerV2Report:
    if config is None:
        config = TeamSpecialistCapacityAllocationOptimizerV2Config()
    if type(config) is not TeamSpecialistCapacityAllocationOptimizerV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCapacityAllocationOptimizerV2Config",
        )
    _require_hard_flags("TeamSpecialistCapacityAllocationOptimizerV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_capacity_items(capacity_items)
    rows = tuple(
        _row_for_item(rank=index, item=item, config=config)
        for index, item in enumerate(_sorted_items(items, config), start=1)
    )
    status = _optimizer_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "optimizer_status": status,
        "item_count": _count_decimal(len(rows)),
        "allocate_count": _status_count(rows, "allocate"),
        "watch_count": _status_count(rows, "watch"),
        "defer_count": _status_count(rows, "defer"),
        "total_requested_units": _sum_units(row.requested_units for row in rows),
        "total_allocated_units": _sum_units(row.allocated_units for row in rows),
        "total_overload_units": _sum_units(row.overload_units for row in rows),
        "allocation_rate": _ratio(
            _sum_units(row.allocated_units for row in rows),
            _sum_units(row.requested_units for row in rows),
        ),
        "average_allocation_priority_score": _average_score(rows),
        "top_allocation_priority_score": _top_score(rows),
        "bottom_allocation_priority_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCapacityAllocationOptimizerV2Report(**values)


def team_specialist_capacity_allocation_optimizer_v2_payload(
    report: TeamSpecialistCapacityAllocationOptimizerV2Report,
) -> dict[str, object]:
    if type(report) is not TeamSpecialistCapacityAllocationOptimizerV2Report:
        raise ValueError(
            "report must be a TeamSpecialistCapacityAllocationOptimizerV2Report",
        )
    payload = _payload_value(asdict(report))
    _reject_unsafe_public_payload(
        "TeamSpecialistCapacityAllocationOptimizerV2Report.payload",
        payload,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def validate_team_specialist_capacity_allocation_optimizer_v2_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "TeamSpecialistCapacityAllocationOptimizerV2Report.payload",
        payload,
    )
    if "derived_validation_digest" not in payload:
        raise ValueError("payload missing derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", payload["derived_validation_digest"])
    expected = _derived_validation_digest(
        {key: value for key, value in payload.items() if key != "derived_validation_digest"},
    )
    if payload["derived_validation_digest"] != expected:
        raise ValueError("derived_validation_digest must match payload fields")
    return True


def _sorted_items(
    items: tuple[TeamSpecialistCapacityAllocationV2Input, ...],
    config: TeamSpecialistCapacityAllocationOptimizerV2Config,
) -> tuple[TeamSpecialistCapacityAllocationV2Input, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_priority_score_for_item(item, config),
                _overload_units_for_item(item),
                item.specialist_id,
                item.queue_id,
            ),
        ),
    )


def _row_for_item(
    *,
    rank: int,
    item: TeamSpecialistCapacityAllocationV2Input,
    config: TeamSpecialistCapacityAllocationOptimizerV2Config,
) -> TeamSpecialistCapacityAllocationOptimizerV2Row:
    remaining_capacity_units = _remaining_capacity_units(item)
    allocated_units = _allocated_units_for_item(item)
    overload_units = _overload_units_for_item(item)
    capacity_fill_ratio = _ratio(allocated_units, item.requested_units)
    overload_penalty_score = _ratio(overload_units, item.requested_units)
    allocation_priority_score = _priority_score_for_item(item, config)
    allocation_status = _allocation_status(
        allocation_priority_score,
        overload_units,
        config,
    )
    return TeamSpecialistCapacityAllocationOptimizerV2Row(
        rank=_count_decimal(rank),
        specialist_id=item.specialist_id,
        queue_id=item.queue_id,
        requested_units=item.requested_units,
        available_capacity_units=item.available_capacity_units,
        current_load_units=item.current_load_units,
        remaining_capacity_units=remaining_capacity_units,
        allocated_units=allocated_units,
        overload_units=overload_units,
        capacity_fill_ratio=capacity_fill_ratio,
        overload_penalty_score=overload_penalty_score,
        queue_priority_score=item.queue_priority_score,
        urgency_score=item.urgency_score,
        specialist_fit_score=item.specialist_fit_score,
        readiness_score=item.readiness_score,
        allocation_priority_score=allocation_priority_score,
        allocation_status=allocation_status,
        reason_codes=_row_reason_codes(item, allocation_status, overload_units),
    )


def _priority_score_for_item(
    item: TeamSpecialistCapacityAllocationV2Input,
    config: TeamSpecialistCapacityAllocationOptimizerV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        allocated_units = _allocated_units_for_item(item)
        overload_units = _overload_units_for_item(item)
        capacity_fill_ratio = _ratio(allocated_units, item.requested_units)
        overload_penalty_score = _ratio(overload_units, item.requested_units)
        score = (
            capacity_fill_ratio * config.capacity_availability_weight
            + item.queue_priority_score * config.queue_priority_weight
            + item.urgency_score * config.urgency_weight
            + item.specialist_fit_score * config.specialist_fit_weight
            + item.readiness_score * config.readiness_weight
            - overload_penalty_score * config.overload_penalty_weight
        )
        return _clamp_ratio(score)


def _remaining_capacity_units(item: TeamSpecialistCapacityAllocationV2Input) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return max(
            ZERO,
            item.available_capacity_units - item.current_load_units,
        ).quantize(UNIT_QUANT)


def _allocated_units_for_item(item: TeamSpecialistCapacityAllocationV2Input) -> Decimal:
    return min(item.requested_units, _remaining_capacity_units(item)).quantize(UNIT_QUANT)


def _overload_units_for_item(item: TeamSpecialistCapacityAllocationV2Input) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (item.requested_units - _allocated_units_for_item(item)).quantize(UNIT_QUANT)


def _allocation_status(
    score: Decimal,
    overload_units: Decimal,
    config: TeamSpecialistCapacityAllocationOptimizerV2Config,
) -> str:
    if score >= config.allocate_score_floor and overload_units == ZERO:
        return "allocate"
    if score >= config.watch_score_floor:
        return "watch"
    return "defer"


def _optimizer_status(
    rows: tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...],
) -> str:
    if not rows:
        return "defer"
    if any(row.allocation_status == "defer" for row in rows):
        return "defer"
    if any(row.allocation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: TeamSpecialistCapacityAllocationV2Input,
    status: str,
    overload_units: Decimal,
) -> tuple[str, ...]:
    return (
        f"capacity_allocation_{status}",
        _tier_reason(
            item.queue_priority_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="queue_priority_high",
            watch_reason="queue_priority_watch",
            weak_reason="queue_priority_low",
        ),
        _tier_reason(
            item.urgency_score,
            strong=Decimal("0.750000"),
            watch=Decimal("0.500000"),
            strong_reason="urgency_high",
            watch_reason="urgency_watch",
            weak_reason="urgency_low",
        ),
        _tier_reason(
            item.specialist_fit_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="specialist_fit_strong",
            watch_reason="specialist_fit_watch",
            weak_reason="specialist_fit_weak",
        ),
        _tier_reason(
            item.readiness_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.500000"),
            strong_reason="readiness_ready",
            watch_reason="readiness_watch",
            weak_reason="readiness_not_ready",
        ),
        _capacity_reason(item, overload_units),
        _overload_penalty_reason(_ratio(overload_units, item.requested_units)),
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("capacity_allocation_optimizer_empty",)
    reasons: list[str] = []
    if any(row.allocation_status == "defer" for row in rows):
        reasons.append("capacity_allocation_optimizer_defer_rows")
    if any(row.allocation_status == "watch" for row in rows):
        reasons.append("capacity_allocation_optimizer_watch_rows")
    if not reasons and status == "pass":
        reasons.append("capacity_allocation_optimizer_passed")
    return tuple(reasons)


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _capacity_reason(
    item: TeamSpecialistCapacityAllocationV2Input,
    overload_units: Decimal,
) -> str:
    if overload_units == ZERO:
        return "capacity_clear"
    if _allocated_units_for_item(item) > ZERO:
        return "capacity_limited"
    return "capacity_overloaded"


def _overload_penalty_reason(overload_penalty_score: Decimal) -> str:
    if overload_penalty_score == ZERO:
        return "overload_penalty_clear"
    if overload_penalty_score < Decimal("0.500000"):
        return "overload_penalty_watch"
    return "overload_penalty_high"


def _normalize_capacity_items(
    capacity_items: object,
) -> tuple[TeamSpecialistCapacityAllocationV2Input, ...]:
    if type(capacity_items) not in (list, tuple):
        raise ValueError("capacity_items must be a list or tuple")
    normalized = tuple(capacity_items)
    for item in normalized:
        if type(item) is not TeamSpecialistCapacityAllocationV2Input:
            raise ValueError(
                "capacity_items must contain TeamSpecialistCapacityAllocationV2Input",
            )
        _require_hard_flags("TeamSpecialistCapacityAllocationV2Input", item)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not TeamSpecialistCapacityAllocationOptimizerV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistCapacityAllocationOptimizerV2Row",
            )
        _require_hard_flags("TeamSpecialistCapacityAllocationOptimizerV2Row", row)
    return rows


def _validate_config(config: TeamSpecialistCapacityAllocationOptimizerV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_sum = (
            config.capacity_availability_weight
            + config.queue_priority_weight
            + config.urgency_weight
            + config.specialist_fit_weight
            + config.readiness_weight
        ).quantize(SCORE_QUANT)
    if weight_sum != ONE:
        raise ValueError("allocation score weights must sum to 1.000000")
    if config.watch_score_floor > config.allocate_score_floor:
        raise ValueError("watch_score_floor must not exceed allocate_score_floor")


def _validate_row_consistency(
    row: TeamSpecialistCapacityAllocationOptimizerV2Row,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        if row.remaining_capacity_units != max(
            ZERO,
            row.available_capacity_units - row.current_load_units,
        ).quantize(UNIT_QUANT):
            raise ValueError("remaining_capacity_units must match capacity inputs")
        if row.allocated_units != min(
            row.requested_units,
            row.remaining_capacity_units,
        ).quantize(UNIT_QUANT):
            raise ValueError("allocated_units must match capacity inputs")
        if row.overload_units != (
            row.requested_units - row.allocated_units
        ).quantize(UNIT_QUANT):
            raise ValueError("overload_units must match capacity inputs")
    if row.capacity_fill_ratio != _ratio(row.allocated_units, row.requested_units):
        raise ValueError("capacity_fill_ratio must match capacity inputs")
    if row.overload_penalty_score != _ratio(row.overload_units, row.requested_units):
        raise ValueError("overload_penalty_score must match capacity inputs")


def _validate_report_consistency(
    report: TeamSpecialistCapacityAllocationOptimizerV2Report,
) -> None:
    rows = report.rows
    if report.item_count != _count_decimal(len(rows)):
        raise ValueError("item_count must match rows")
    if report.allocate_count != _status_count(rows, "allocate"):
        raise ValueError("status counts must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("status counts must match rows")
    if report.defer_count != _status_count(rows, "defer"):
        raise ValueError("status counts must match rows")
    total_requested_units = _sum_units(row.requested_units for row in rows)
    total_allocated_units = _sum_units(row.allocated_units for row in rows)
    total_overload_units = _sum_units(row.overload_units for row in rows)
    if report.total_requested_units != total_requested_units:
        raise ValueError("total_requested_units must match rows")
    if report.total_allocated_units != total_allocated_units:
        raise ValueError("total_allocated_units must match rows")
    if report.total_overload_units != total_overload_units:
        raise ValueError("total_overload_units must match rows")
    if report.allocation_rate != _ratio(total_allocated_units, total_requested_units):
        raise ValueError("allocation_rate must match rows")
    if report.average_allocation_priority_score != _average_score(rows):
        raise ValueError("average_allocation_priority_score must match rows")
    if report.top_allocation_priority_score != _top_score(rows):
        raise ValueError("top_allocation_priority_score must match rows")
    if report.bottom_allocation_priority_score != _bottom_score(rows):
        raise ValueError("bottom_allocation_priority_score must match rows")
    if report.optimizer_status != _optimizer_status(rows):
        raise ValueError("optimizer_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.optimizer_status):
        raise ValueError("reason_codes must match optimizer_status")
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.allocation_priority_score,
                row.overload_units,
                row.specialist_id,
                row.queue_id,
            ),
        ),
    ):
        raise ValueError("rows must be sorted by priority and rank")
    for index, row in enumerate(rows, start=1):
        if row.rank != _count_decimal(index):
            raise ValueError("rows must be sorted by priority and rank")
    expected_digest = _derived_validation_digest(
        {
            field.name: getattr(report, field.name)
            for field in fields(report)
            if field.name != "derived_validation_digest"
        },
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _status_count(
    rows: tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.allocation_status == status))


def _sum_units(values: object) -> Decimal:
    if type(values) not in (list, tuple):
        values = tuple(values)  # type: ignore[arg-type]
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(UNIT_QUANT)  # type: ignore[arg-type]


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(SCORE_QUANT)


def _average_score(
    rows: tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.allocation_priority_score for row in rows), ZERO)
            / Decimal(len(rows))
        ).quantize(SCORE_QUANT)


def _top_score(
    rows: tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.allocation_priority_score for row in rows).quantize(SCORE_QUANT)


def _bottom_score(
    rows: tuple[TeamSpecialistCapacityAllocationOptimizerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.allocation_priority_score for row in rows).quantize(SCORE_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_non_empty_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_units(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(UNIT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_positive_units(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_units(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float or type(value) is int:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
