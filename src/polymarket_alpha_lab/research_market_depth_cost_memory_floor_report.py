"""Readonly depth cost memory floor research report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_DEPTH_COST_MEMORY_FLOOR_CONFIG_VERSION = (
    "research-market-depth-cost-memory-floor-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "depth_cost_memory_floor_empty"
PASS_REASON = "depth_cost_memory_floor_pass"
WATCH_COST_REASON = "depth_cost_memory_floor_watch_cost"
BLOCK_COST_REASON = "depth_cost_memory_floor_block_cost"
INSUFFICIENT_MEMORY_REASON = "depth_cost_memory_floor_insufficient_memory"
THIN_DEPTH_REASON = "depth_cost_memory_floor_thin_depth"

ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_COST_REASON,
    BLOCK_COST_REASON,
    INSUFFICIENT_MEMORY_REASON,
    THIN_DEPTH_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    WATCH_COST_REASON,
    BLOCK_COST_REASON,
    INSUFFICIENT_MEMORY_REASON,
    THIN_DEPTH_REASON,
)
REPORT_TRIGGER_REASONS = tuple(
    reason_code
    for reason_code in REPORT_REASON_CODES
    if reason_code not in (EMPTY_REASON, PASS_REASON)
)

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        ":" + "//",
        "api" + "_key",
        "au" + "th",
        "candidate",
        "client" + "_secret",
        "data" + "base",
        "d" + "sn",
        "http",
        "live",
        "net" + "work",
        "ord" + "er",
        "persist",
        "private" + "_key",
        "raw",
        "recommenda" + "tion",
        "secret",
        "sign",
        "so" + "urce",
        "submit",
        "ta" + "ble",
        "te" + "xt",
        "to" + "ken",
        "trade",
        "trading",
        "u" + "rl",
        "wal" + "let",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_COST_MEMORY_FLOOR_CONFIG_VERSION",
    "ResearchMarketDepthCostMemoryFloorConfig",
    "ResearchMarketDepthCostMemoryFloorObservation",
    "ResearchMarketDepthCostMemoryFloorRow",
    "ResearchMarketDepthCostMemoryFloorReport",
    "build_research_market_depth_cost_memory_floor_report",
    "research_market_depth_cost_memory_floor_report_payload",
    "validate_research_market_depth_cost_memory_floor_public_payload",
)


@dataclass(frozen=True)
class ResearchMarketDepthCostMemoryFloorConfig:
    watch_depth_cost_floor: Decimal = Decimal("0.030000")
    block_depth_cost_floor: Decimal = Decimal("0.075000")
    min_memory_points: Decimal = Decimal("2.000000")
    min_depth_ratio: Decimal = Decimal("0.500000")
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_COST_MEMORY_FLOOR_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthCostMemoryFloorConfig:
            raise TypeError(
                "ResearchMarketDepthCostMemoryFloorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthCostMemoryFloorConfig:
            raise ValueError(
                "config must be exactly ResearchMarketDepthCostMemoryFloorConfig",
            )
        object.__setattr__(
            self,
            "watch_depth_cost_floor",
            _require_ratio("watch_depth_cost_floor", self.watch_depth_cost_floor),
        )
        object.__setattr__(
            self,
            "block_depth_cost_floor",
            _require_ratio("block_depth_cost_floor", self.block_depth_cost_floor),
        )
        object.__setattr__(
            self,
            "min_memory_points",
            _require_positive_count("min_memory_points", self.min_memory_points),
        )
        object.__setattr__(
            self,
            "min_depth_ratio",
            _require_ratio("min_depth_ratio", self.min_depth_ratio),
        )
        if self.block_depth_cost_floor <= self.watch_depth_cost_floor:
            raise ValueError("block_depth_cost_floor must exceed watch_depth_cost_floor")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthCostMemoryFloorObservation:
    private_reference: str
    segment_key: str
    depth_cost: Decimal
    memory_point_count: Decimal
    depth_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthCostMemoryFloorObservation:
            raise TypeError(
                "ResearchMarketDepthCostMemoryFloorObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthCostMemoryFloorObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketDepthCostMemoryFloorObservation",
            )
        object.__setattr__(
            self,
            "private_reference",
            _require_private_reference("private_reference", self.private_reference),
        )
        object.__setattr__(
            self,
            "segment_key",
            _require_public_identifier("segment_key", self.segment_key),
        )
        object.__setattr__(
            self,
            "depth_cost",
            _require_ratio("depth_cost", self.depth_cost),
        )
        object.__setattr__(
            self,
            "memory_point_count",
            _require_count("memory_point_count", self.memory_point_count),
        )
        object.__setattr__(
            self,
            "depth_ratio",
            _require_ratio("depth_ratio", self.depth_ratio),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthCostMemoryFloorRow:
    segment_key: str
    reference_digest: str
    depth_cost: Decimal
    memory_point_count: Decimal
    depth_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthCostMemoryFloorRow:
            raise TypeError(
                "ResearchMarketDepthCostMemoryFloorRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthCostMemoryFloorRow:
            raise ValueError(
                "row must be exactly ResearchMarketDepthCostMemoryFloorRow",
            )
        object.__setattr__(
            self,
            "segment_key",
            _require_public_identifier("segment_key", self.segment_key),
        )
        _require_reference_digest("reference_digest", self.reference_digest)
        object.__setattr__(
            self,
            "depth_cost",
            _require_ratio("depth_cost", self.depth_cost),
        )
        object.__setattr__(
            self,
            "memory_point_count",
            _require_count("memory_point_count", self.memory_point_count),
        )
        object.__setattr__(
            self,
            "depth_ratio",
            _require_ratio("depth_ratio", self.depth_ratio),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status is inconsistent with reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthCostMemoryFloorReport:
    generated_at: datetime
    config_version: str
    watch_depth_cost_floor: Decimal
    block_depth_cost_floor: Decimal
    min_memory_points: Decimal
    min_depth_ratio: Decimal
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    memory_floor_breach_count: Decimal
    cost_floor_breach_count: Decimal
    watch_ratio: Decimal
    max_depth_cost: Decimal
    min_depth_ratio_observed: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketDepthCostMemoryFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthCostMemoryFloorReport:
            raise TypeError(
                "ResearchMarketDepthCostMemoryFloorReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthCostMemoryFloorReport:
            raise ValueError(
                "report must be exactly ResearchMarketDepthCostMemoryFloorReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "watch_depth_cost_floor",
            "block_depth_cost_floor",
            "min_depth_ratio",
            "watch_ratio",
            "max_depth_cost",
            "min_depth_ratio_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_memory_points",
            _require_positive_count("min_memory_points", self.min_memory_points),
        )
        if self.block_depth_cost_floor <= self.watch_depth_cost_floor:
            raise ValueError("block_depth_cost_floor must exceed watch_depth_cost_floor")
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "block_count",
            "memory_floor_breach_count",
            "cost_floor_breach_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match public payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_market_depth_cost_memory_floor_report(
    observations: list[ResearchMarketDepthCostMemoryFloorObservation]
    | tuple[ResearchMarketDepthCostMemoryFloorObservation, ...],
    *,
    config: ResearchMarketDepthCostMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchMarketDepthCostMemoryFloorReport:
    if type(config) is not ResearchMarketDepthCostMemoryFloorConfig:
        raise ValueError("config must be a ResearchMarketDepthCostMemoryFloorConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in _normalize_observations(observations)
            ),
            key=_row_sort_key,
        ),
    )
    market_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    return ResearchMarketDepthCostMemoryFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        watch_depth_cost_floor=config.watch_depth_cost_floor,
        block_depth_cost_floor=config.block_depth_cost_floor,
        min_memory_points=config.min_memory_points,
        min_depth_ratio=config.min_depth_ratio,
        market_count=market_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        memory_floor_breach_count=_count(
            sum(1 for row in rows if INSUFFICIENT_MEMORY_REASON in row.reason_codes),
        ),
        cost_floor_breach_count=_count(
            sum(
                1
                for row in rows
                if (
                    WATCH_COST_REASON in row.reason_codes
                    or BLOCK_COST_REASON in row.reason_codes
                )
            ),
        ),
        watch_ratio=_ratio(watch_count + block_count, market_count),
        max_depth_cost=_max_decimal(row.depth_cost for row in rows),
        min_depth_ratio_observed=_min_decimal(row.depth_ratio for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_market_depth_cost_memory_floor_report_payload(
    report: ResearchMarketDepthCostMemoryFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthCostMemoryFloorReport:
        raise ValueError("report must be a ResearchMarketDepthCostMemoryFloorReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_market_depth_cost_memory_floor_public_payload(payload)
    return payload


def validate_research_market_depth_cost_memory_floor_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_payload_flags(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_observation(
    observation: ResearchMarketDepthCostMemoryFloorObservation,
    *,
    config: ResearchMarketDepthCostMemoryFloorConfig,
) -> ResearchMarketDepthCostMemoryFloorRow:
    if type(observation) is not ResearchMarketDepthCostMemoryFloorObservation:
        raise ValueError(
            "observation must be a ResearchMarketDepthCostMemoryFloorObservation",
        )
    _require_hard_flags("observation", observation)
    reason_codes = _row_reason_codes(observation, config=config)
    return ResearchMarketDepthCostMemoryFloorRow(
        segment_key=observation.segment_key,
        reference_digest=_reference_digest(observation.private_reference),
        depth_cost=observation.depth_cost,
        memory_point_count=observation.memory_point_count,
        depth_ratio=observation.depth_ratio,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchMarketDepthCostMemoryFloorObservation,
    *,
    config: ResearchMarketDepthCostMemoryFloorConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.depth_cost >= config.block_depth_cost_floor:
        reasons.append(BLOCK_COST_REASON)
    elif observation.depth_cost >= config.watch_depth_cost_floor:
        reasons.append(WATCH_COST_REASON)
    if observation.memory_point_count < config.min_memory_points:
        reasons.append(INSUFFICIENT_MEMORY_REASON)
    if observation.depth_ratio < config.min_depth_ratio:
        reasons.append(THIN_DEPTH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        BLOCK_COST_REASON in reason_codes
        or INSUFFICIENT_MEMORY_REASON in reason_codes
        or THIN_DEPTH_REASON in reason_codes
    ):
        return "block"
    if WATCH_COST_REASON in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchMarketDepthCostMemoryFloorRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthCostMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not present:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_TRIGGER_REASONS if reason_code in present)


def _row_sort_key(row: ResearchMarketDepthCostMemoryFloorRow) -> tuple[object, ...]:
    return (STATUS_RANK[row.status], row.segment_key, row.reference_digest)


def _normalize_observations(
    observations: list[ResearchMarketDepthCostMemoryFloorObservation]
    | tuple[ResearchMarketDepthCostMemoryFloorObservation, ...],
) -> tuple[ResearchMarketDepthCostMemoryFloorObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchMarketDepthCostMemoryFloorObservation:
            raise ValueError(
                "observations must contain ResearchMarketDepthCostMemoryFloorObservation",
            )
        _require_hard_flags("observation", observation)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchMarketDepthCostMemoryFloorRow, ...],
) -> tuple[ResearchMarketDepthCostMemoryFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketDepthCostMemoryFloorRow:
            raise ValueError("rows must contain ResearchMarketDepthCostMemoryFloorRow")
        _require_hard_flags("row", row)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_known_value(field_name, reason_code, allowed_reason_codes)
        if reason_code in normalized:
            raise ValueError(f"{field_name} values must be unique")
        normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    expected = tuple(reason_code for reason_code in allowed_reason_codes if reason_code in normalized)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must follow canonical sequence")
    return tuple(normalized)


def _validate_report_consistency(
    report: ResearchMarketDepthCostMemoryFloorReport,
) -> None:
    rows = report.rows
    market_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    if report.market_count != market_count:
        raise ValueError("market_count is inconsistent with rows")
    if report.pass_count != pass_count:
        raise ValueError("pass_count is inconsistent with rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count is inconsistent with rows")
    if report.block_count != block_count:
        raise ValueError("block_count is inconsistent with rows")
    if report.memory_floor_breach_count != _count(
        sum(1 for row in rows if INSUFFICIENT_MEMORY_REASON in row.reason_codes),
    ):
        raise ValueError("memory_floor_breach_count is inconsistent with rows")
    if report.cost_floor_breach_count != _count(
        sum(
            1
            for row in rows
            if WATCH_COST_REASON in row.reason_codes
            or BLOCK_COST_REASON in row.reason_codes
        ),
    ):
        raise ValueError("cost_floor_breach_count is inconsistent with rows")
    if report.watch_ratio != _ratio(watch_count + block_count, market_count):
        raise ValueError("watch_ratio is inconsistent with rows")
    if report.max_depth_cost != _max_decimal(row.depth_cost for row in rows):
        raise ValueError("max_depth_cost is inconsistent with rows")
    if report.min_depth_ratio_observed != _min_decimal(row.depth_ratio for row in rows):
        raise ValueError("min_depth_ratio_observed is inconsistent with rows")
    if report.status != _report_status(rows):
        raise ValueError("status is inconsistent with rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes is inconsistent with rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_flags(value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for public payload")
        for item in value.values():
            _require_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _require_payload_flags(item)


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: object) -> Decimal:
    decimal_values = tuple(values)
    if not decimal_values:
        return ZERO
    return max(decimal_values).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _min_decimal(values: object) -> Decimal:
    decimal_values = tuple(values)
    if not decimal_values:
        return ZERO
    return min(decimal_values).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > 128:
        raise ValueError(f"{field_name} is too long")
    for char in value:
        if not (char.islower() or char.isdigit() or char in "-_."):
            raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_known_value(field_name, value, STATUSES)


def _reference_digest(value: str) -> str:
    encoded = value.encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()[:12]


def _require_reference_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 reference")
    suffix = value.removeprefix("sha256:")
    if len(suffix) != 12 or any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{field_name} must be a sha256 reference")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _derived_validation_digest(
    report: ResearchMarketDepthCostMemoryFloorReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_surface("report payload", payload)
    _reject_public_numerics(payload)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload fields must be strings")
            _reject_unsafe_public_key(key)
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public field")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")
