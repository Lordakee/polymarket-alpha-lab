"""Readonly market liquidity cost memory floor research report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_MEMORY_FLOOR_CONFIG_VERSION = (
    "research-market-liquidity-cost-memory-floor-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MARKET_REFERENCE_PREFIX = "market_ref_"
ALLOWED_PUBLIC_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "liquidity_cost_memory_floor_empty"
PASS_REASON = "liquidity_cost_memory_floor_pass"
WATCH_COST_REASON = "liquidity_cost_memory_floor_watch_cost"
BLOCK_COST_REASON = "liquidity_cost_memory_floor_block_cost"
INSUFFICIENT_MEMORY_REASON = "liquidity_cost_memory_floor_insufficient_memory"

ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_COST_REASON,
    BLOCK_COST_REASON,
    INSUFFICIENT_MEMORY_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    WATCH_COST_REASON,
    BLOCK_COST_REASON,
    INSUFFICIENT_MEMORY_REASON,
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
        "exec" + "ute",
        "exec" + "ution",
        "http",
        "live",
        "market" + "_" + "id",
        "market" + "_" + "sl" + "ug",
        "market" + "_" + "ques" + "tion",
        "net" + "work",
        "ord" + "er",
        "persist",
        "posi" + "tion",
        "private" + "_key",
        "ques" + "tion",
        "ra" + "w",
        "recom" + "mend",
        "reco" + "mmenda" + "tion",
        "secret",
        "sign",
        "siz" + "e",
        "siz" + "ing",
        "sl" + "ug",
        "source",
        "submit",
        "ta" + "ble",
        "text",
        "to" + "ken",
        "trade",
        "trading",
        "url",
        "wal" + "let",
    ),
)
REPORT_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "watch_cost_floor",
        "block_cost_floor",
        "min_memory_observations",
        "market_count",
        "pass_count",
        "watch_count",
        "block_count",
        "memory_floor_breach_count",
        "watch_ratio",
        "max_liquidity_cost",
        "max_pressure_score",
        "status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "market_key",
        "market_family",
        "cost_bucket",
        "liquidity_cost",
        "memory_observation_count",
        "pressure_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_COUNT_PAYLOAD_FIELDS = (
    "market_count",
    "pass_count",
    "watch_count",
    "block_count",
    "memory_floor_breach_count",
)
REPORT_RATIO_PAYLOAD_FIELDS = (
    "watch_cost_floor",
    "block_cost_floor",
    "watch_ratio",
    "max_liquidity_cost",
    "max_pressure_score",
)
ROW_COUNT_PAYLOAD_FIELDS = ("memory_observation_count",)
ROW_RATIO_PAYLOAD_FIELDS = ("liquidity_cost", "pressure_score")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_MEMORY_FLOOR_CONFIG_VERSION",
    "ResearchMarketLiquidityCostMemoryFloorConfig",
    "ResearchMarketLiquidityCostMemoryFloorObservation",
    "ResearchMarketLiquidityCostMemoryFloorRow",
    "ResearchMarketLiquidityCostMemoryFloorReport",
    "build_research_market_liquidity_cost_memory_floor_report",
    "research_market_liquidity_cost_memory_floor_report_payload",
    "validate_research_market_liquidity_cost_memory_floor_public_payload",
)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostMemoryFloorConfig:
    watch_cost_floor: Decimal = Decimal("0.030000")
    block_cost_floor: Decimal = Decimal("0.075000")
    min_memory_observations: Decimal = Decimal("2.000000")
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_MEMORY_FLOOR_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "watch_cost_floor",
            _require_ratio("watch_cost_floor", self.watch_cost_floor),
        )
        object.__setattr__(
            self,
            "block_cost_floor",
            _require_ratio("block_cost_floor", self.block_cost_floor),
        )
        object.__setattr__(
            self,
            "min_memory_observations",
            _require_positive_count(
                "min_memory_observations",
                self.min_memory_observations,
            ),
        )
        if self.block_cost_floor <= self.watch_cost_floor:
            raise ValueError("block_cost_floor must exceed watch_cost_floor")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostMemoryFloorObservation:
    market_key: str
    market_family: str
    cost_bucket: str
    liquidity_cost: Decimal
    memory_observation_count: Decimal
    pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_key",
            _require_redacted_market_key("market_key", self.market_key),
        )
        for field_name in ("market_family", "cost_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_cost",
            _require_ratio("liquidity_cost", self.liquidity_cost),
        )
        object.__setattr__(
            self,
            "memory_observation_count",
            _require_count(
                "memory_observation_count",
                self.memory_observation_count,
            ),
        )
        object.__setattr__(
            self,
            "pressure_score",
            _require_ratio("pressure_score", self.pressure_score),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostMemoryFloorRow:
    market_key: str
    market_family: str
    cost_bucket: str
    liquidity_cost: Decimal
    memory_observation_count: Decimal
    pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_key",
            _require_redacted_market_key("market_key", self.market_key),
        )
        for field_name in ("market_family", "cost_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_cost",
            _require_ratio("liquidity_cost", self.liquidity_cost),
        )
        object.__setattr__(
            self,
            "memory_observation_count",
            _require_count(
                "memory_observation_count",
                self.memory_observation_count,
            ),
        )
        object.__setattr__(
            self,
            "pressure_score",
            _require_ratio("pressure_score", self.pressure_score),
        )
        _require_known_value("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status is inconsistent with reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostMemoryFloorReport:
    generated_at: datetime
    config_version: str
    watch_cost_floor: Decimal
    block_cost_floor: Decimal
    min_memory_observations: Decimal
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    memory_floor_breach_count: Decimal
    watch_ratio: Decimal
    max_liquidity_cost: Decimal
    max_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketLiquidityCostMemoryFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "watch_cost_floor",
            _require_ratio("watch_cost_floor", self.watch_cost_floor),
        )
        object.__setattr__(
            self,
            "block_cost_floor",
            _require_ratio("block_cost_floor", self.block_cost_floor),
        )
        object.__setattr__(
            self,
            "min_memory_observations",
            _require_positive_count(
                "min_memory_observations",
                self.min_memory_observations,
            ),
        )
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "block_count",
            "memory_floor_breach_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "watch_ratio",
            _require_ratio("watch_ratio", self.watch_ratio),
        )
        for field_name in ("max_liquidity_cost", "max_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_known_value("status", self.status, STATUSES)
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


def build_research_market_liquidity_cost_memory_floor_report(
    observations: list[ResearchMarketLiquidityCostMemoryFloorObservation]
    | tuple[ResearchMarketLiquidityCostMemoryFloorObservation, ...],
    *,
    config: ResearchMarketLiquidityCostMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityCostMemoryFloorReport:
    if type(config) is not ResearchMarketLiquidityCostMemoryFloorConfig:
        raise ValueError("config must be a ResearchMarketLiquidityCostMemoryFloorConfig")
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
    return ResearchMarketLiquidityCostMemoryFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        watch_cost_floor=config.watch_cost_floor,
        block_cost_floor=config.block_cost_floor,
        min_memory_observations=config.min_memory_observations,
        market_count=market_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        memory_floor_breach_count=_count(
            sum(1 for row in rows if INSUFFICIENT_MEMORY_REASON in row.reason_codes),
        ),
        watch_ratio=_ratio(watch_count + block_count, market_count),
        max_liquidity_cost=_max_decimal(row.liquidity_cost for row in rows),
        max_pressure_score=_max_decimal(row.pressure_score for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_market_liquidity_cost_memory_floor_report_payload(
    report: ResearchMarketLiquidityCostMemoryFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityCostMemoryFloorReport:
        raise ValueError("report must be a ResearchMarketLiquidityCostMemoryFloorReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_market_liquidity_cost_memory_floor_public_payload(payload)
    return payload


def validate_research_market_liquidity_cost_memory_floor_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _validate_public_payload_shape(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    _validate_public_payload_consistency(payload)


def _row_from_observation(
    observation: ResearchMarketLiquidityCostMemoryFloorObservation,
    *,
    config: ResearchMarketLiquidityCostMemoryFloorConfig,
) -> ResearchMarketLiquidityCostMemoryFloorRow:
    if type(observation) is not ResearchMarketLiquidityCostMemoryFloorObservation:
        raise ValueError(
            "observation must be a ResearchMarketLiquidityCostMemoryFloorObservation",
        )
    _require_hard_flags("observation", observation)
    reason_codes = _row_reason_codes(observation, config=config)
    return ResearchMarketLiquidityCostMemoryFloorRow(
        market_key=observation.market_key,
        market_family=observation.market_family,
        cost_bucket=observation.cost_bucket,
        liquidity_cost=observation.liquidity_cost,
        memory_observation_count=observation.memory_observation_count,
        pressure_score=observation.pressure_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchMarketLiquidityCostMemoryFloorObservation,
    *,
    config: ResearchMarketLiquidityCostMemoryFloorConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if observation.liquidity_cost >= config.block_cost_floor:
        reasons.append(BLOCK_COST_REASON)
    elif observation.liquidity_cost >= config.watch_cost_floor:
        reasons.append(WATCH_COST_REASON)
    if observation.memory_observation_count < config.min_memory_observations:
        reasons.append(INSUFFICIENT_MEMORY_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        BLOCK_COST_REASON in reason_codes
        or INSUFFICIENT_MEMORY_REASON in reason_codes
    ):
        return "block"
    if WATCH_COST_REASON in reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchMarketLiquidityCostMemoryFloorRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityCostMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in REPORT_TRIGGER_REASONS
    }
    if not found:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in found)


def _row_sort_key(
    row: ResearchMarketLiquidityCostMemoryFloorRow,
) -> tuple[int, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.liquidity_cost, row.market_key)


def _normalize_observations(
    observations: list[ResearchMarketLiquidityCostMemoryFloorObservation]
    | tuple[ResearchMarketLiquidityCostMemoryFloorObservation, ...],
) -> tuple[ResearchMarketLiquidityCostMemoryFloorObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized: list[ResearchMarketLiquidityCostMemoryFloorObservation] = []
    for observation in observations:
        if type(observation) is not ResearchMarketLiquidityCostMemoryFloorObservation:
            raise ValueError(
                "observation must be a ResearchMarketLiquidityCostMemoryFloorObservation",
            )
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(normalized)


def _normalize_rows(
    rows: list[ResearchMarketLiquidityCostMemoryFloorRow]
    | tuple[ResearchMarketLiquidityCostMemoryFloorRow, ...],
) -> tuple[ResearchMarketLiquidityCostMemoryFloorRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized: list[ResearchMarketLiquidityCostMemoryFloorRow] = []
    for row in rows:
        if type(row) is not ResearchMarketLiquidityCostMemoryFloorRow:
            raise ValueError("row must be a ResearchMarketLiquidityCostMemoryFloorRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _validate_report_consistency(
    report: ResearchMarketLiquidityCostMemoryFloorReport,
) -> None:
    rows = report.rows
    expected_values = {
        "market_count": _count(len(rows)),
        "pass_count": _count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": _count(sum(1 for row in rows if row.status == "watch")),
        "block_count": _count(sum(1 for row in rows if row.status == "block")),
        "memory_floor_breach_count": _count(
            sum(1 for row in rows if INSUFFICIENT_MEMORY_REASON in row.reason_codes),
        ),
        "watch_ratio": _ratio(
            _count(
                sum(1 for row in rows if row.status in ("watch", "block")),
            ),
            _count(len(rows)),
        ),
        "max_liquidity_cost": _max_decimal(row.liquidity_cost for row in rows),
        "max_pressure_score": _max_decimal(row.pressure_score for row in rows),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")


def _derived_validation_digest(
    report: ResearchMarketLiquidityCostMemoryFloorReport,
) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: ResearchMarketLiquidityCostMemoryFloorReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_public_payload_keys(
        "public payload",
        payload,
        REPORT_PUBLIC_PAYLOAD_KEYS,
    )
    _as_public_payload_datetime("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_positive_count(
        "min_memory_observations",
        _decimal_from_public_payload(
            "min_memory_observations",
            payload["min_memory_observations"],
        ),
    )
    for field_name in REPORT_COUNT_PAYLOAD_FIELDS:
        _require_count(
            field_name,
            _decimal_from_public_payload(field_name, payload[field_name]),
        )
    for field_name in REPORT_RATIO_PAYLOAD_FIELDS:
        _require_ratio(
            field_name,
            _decimal_from_public_payload(field_name, payload[field_name]),
        )
    _require_known_value("status", payload["status"], STATUSES)
    _require_public_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for index, row in enumerate(rows):
        _validate_public_row_payload_shape(index, row)


def _validate_public_row_payload_shape(index: int, row: object) -> None:
    if type(row) is not dict:
        raise ValueError("rows entries must be JSON objects")
    _require_public_payload_keys(
        f"public row {index}",
        row,
        ROW_PUBLIC_PAYLOAD_KEYS,
    )
    _require_redacted_market_key("market_key", row["market_key"])
    _require_public_identifier("market_family", row["market_family"])
    _require_public_identifier("cost_bucket", row["cost_bucket"])
    for field_name in ROW_COUNT_PAYLOAD_FIELDS:
        _require_count(
            field_name,
            _decimal_from_public_payload(field_name, row[field_name]),
        )
    for field_name in ROW_RATIO_PAYLOAD_FIELDS:
        _require_ratio(
            field_name,
            _decimal_from_public_payload(field_name, row[field_name]),
        )
    _require_known_value("status", row["status"], STATUSES)
    _require_public_payload_reason_codes(
        "reason_codes",
        row["reason_codes"],
        ROW_REASON_CODES,
    )
    _require_hard_flags(f"public row {index}", _PayloadFlags(row))


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    ResearchMarketLiquidityCostMemoryFloorReport(
        generated_at=_as_public_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        watch_cost_floor=_decimal_from_public_payload(
            "watch_cost_floor",
            payload["watch_cost_floor"],
        ),
        block_cost_floor=_decimal_from_public_payload(
            "block_cost_floor",
            payload["block_cost_floor"],
        ),
        min_memory_observations=_decimal_from_public_payload(
            "min_memory_observations",
            payload["min_memory_observations"],
        ),
        market_count=_decimal_from_public_payload(
            "market_count",
            payload["market_count"],
        ),
        pass_count=_decimal_from_public_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_public_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_public_payload("block_count", payload["block_count"]),
        memory_floor_breach_count=_decimal_from_public_payload(
            "memory_floor_breach_count",
            payload["memory_floor_breach_count"],
        ),
        watch_ratio=_decimal_from_public_payload("watch_ratio", payload["watch_ratio"]),
        max_liquidity_cost=_decimal_from_public_payload(
            "max_liquidity_cost",
            payload["max_liquidity_cost"],
        ),
        max_pressure_score=_decimal_from_public_payload(
            "max_pressure_score",
            payload["max_pressure_score"],
        ),
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        rows=tuple(_row_from_public_payload(row) for row in payload["rows"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    row: dict[str, Any],
) -> ResearchMarketLiquidityCostMemoryFloorRow:
    return ResearchMarketLiquidityCostMemoryFloorRow(
        market_key=row["market_key"],
        market_family=row["market_family"],
        cost_bucket=row["cost_bucket"],
        liquidity_cost=_decimal_from_public_payload(
            "liquidity_cost",
            row["liquidity_cost"],
        ),
        memory_observation_count=_decimal_from_public_payload(
            "memory_observation_count",
            row["memory_observation_count"],
        ),
        pressure_score=_decimal_from_public_payload(
            "pressure_score",
            row["pressure_score"],
        ),
        status=row["status"],
        reason_codes=tuple(row["reason_codes"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _require_public_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = set(value)
    missing_keys = sorted(expected_keys - actual_keys)
    if missing_keys:
        raise ValueError(f"{label} missing field: {missing_keys[0]}")
    unexpected_keys = sorted(actual_keys - expected_keys)
    if unexpected_keys:
        raise ValueError(f"unexpected public field in {label}: {unexpected_keys[0]}")


def _require_public_payload_reason_codes(
    field_name: str,
    reason_codes: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(field_name, tuple(reason_codes), allowed_values)
    if tuple(reason_codes) != normalized:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    canonical = parsed.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    if parsed != canonical or str(canonical) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return parsed


def _as_public_payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_redacted_market_key(field_name: str, value: object) -> str:
    public_value = _require_public_identifier(field_name, value)
    if not public_value.startswith(MARKET_REFERENCE_PREFIX):
        raise ValueError(f"{field_name} must be a redacted market reference")
    digest = public_value.removeprefix(MARKET_REFERENCE_PREFIX)
    if len(digest) != len("000000000000"):
        raise ValueError(f"{field_name} must be a redacted market reference")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be a redacted market reference")
    return public_value


def _require_public_identifier(field_name: str, value: object) -> str:
    public_value = _require_public_string(field_name, value)
    if public_value.lower() != public_value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(character not in ALLOWED_PUBLIC_IDENTIFIER_CHARS for character in public_value):
        raise ValueError(f"{field_name} contains unsupported characters")
    return public_value


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        _require_known_value(field_name, reason_code, allowed_values)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: Any) -> Decimal:
    maximum = ZERO
    for value in values:
        if value > maximum:
            maximum = value
    return maximum


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, (str, bool)):
        return value
    if type(value) in (float, int):
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
