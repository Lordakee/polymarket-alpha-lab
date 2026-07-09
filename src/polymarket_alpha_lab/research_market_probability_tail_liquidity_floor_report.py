"""Report-only reducer for probability-tail liquidity floor pressure."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_TAIL_LIQUIDITY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-market-probability-tail-liquidity-floor-report-v0"
)

Q = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_PREFIX = "sha256:"
SHA256_HEX_LENGTH = 64

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

REASON_EMPTY_INPUT = "probability_tail_liquidity_floor_empty"
REASON_REPORT_PASS = "tail_liquidity_floor_pass_present"
REASON_REPORT_WATCH = "tail_liquidity_floor_watch_present"
REASON_REPORT_BLOCK = "tail_liquidity_floor_block_present"
REASON_ROW_PASS = "tail_liquidity_floor_pass"
REASON_TAIL_PROBABILITY_WATCH = "tail_probability_watch"
REASON_TAIL_PROBABILITY_BLOCK = "tail_probability_block"
REASON_LIQUIDITY_FLOOR_WATCH = "liquidity_floor_watch"
REASON_LIQUIDITY_FLOOR_BLOCK = "liquidity_floor_block"
REASON_SPREAD_PRESSURE_WATCH = "spread_pressure_watch"
REASON_SPREAD_PRESSURE_BLOCK = "spread_pressure_block"
REASON_PRESSURE_WATCH = "tail_liquidity_pressure_watch"
REASON_PRESSURE_BLOCK = "tail_liquidity_pressure_block"

REPORT_REASON_CODES = (
    REASON_EMPTY_INPUT,
    REASON_REPORT_BLOCK,
    REASON_REPORT_WATCH,
    REASON_REPORT_PASS,
)
ROW_REASON_CODES = (
    REASON_ROW_PASS,
    REASON_TAIL_PROBABILITY_WATCH,
    REASON_TAIL_PROBABILITY_BLOCK,
    REASON_LIQUIDITY_FLOOR_WATCH,
    REASON_LIQUIDITY_FLOOR_BLOCK,
    REASON_SPREAD_PRESSURE_WATCH,
    REASON_SPREAD_PRESSURE_BLOCK,
    REASON_PRESSURE_WATCH,
    REASON_PRESSURE_BLOCK,
)
BLOCK_REASON_CODES = frozenset(
    (
        REASON_TAIL_PROBABILITY_BLOCK,
        REASON_LIQUIDITY_FLOOR_BLOCK,
        REASON_SPREAD_PRESSURE_BLOCK,
        REASON_PRESSURE_BLOCK,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        REASON_TAIL_PROBABILITY_WATCH,
        REASON_LIQUIDITY_FLOOR_WATCH,
        REASON_SPREAD_PRESSURE_WATCH,
        REASON_PRESSURE_WATCH,
    ),
)

REPORT_DECIMAL_FIELDS = (
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "tail_observation_count",
    "floor_breach_count",
    "average_tail_distance",
    "minimum_tail_distance",
    "average_liquidity_depth_units",
    "minimum_liquidity_depth_units",
    "maximum_floor_gap_ratio",
)
ROW_DECIMAL_FIELDS = (
    "rank",
    "probability",
    "tail_distance",
    "liquidity_depth_units",
    "liquidity_floor_gap_units",
    "liquidity_floor_gap_ratio",
    "spread_pressure_score",
    "tail_pressure_score",
    "tail_liquidity_pressure_score",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    *REPORT_DECIMAL_FIELDS,
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "rank",
    "analysis_digest",
    "probability",
    "tail_distance",
    "liquidity_depth_units",
    "liquidity_floor_gap_units",
    "liquidity_floor_gap_ratio",
    "spread_pressure_score",
    "tail_pressure_score",
    "tail_liquidity_pressure_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("raw_", "candidate", "_id"),
        _join("candidate", "_id"),
        _join("market", "_id"),
        _join("market", "_slug"),
        _join("ques", "tion"),
        _join("source", "_url"),
        _join("source", "_text"),
        _join("d", "sn"),
        _join("table", "_name"),
        _join("to", "ken"),
        _join("wal", "let"),
        _join("or", "der"),
        _join("tra", "de"),
        _join("siz", "ing"),
        _join("recomm", "endation"),
        _join("li", "ve"),
        _join("net", "work"),
        _join("au", "th"),
        _join("bear", "er"),
        "://",
        "http://",
        "https://",
        "www.",
        "postgres://",
        "mysql://",
        "jdbc:",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_TAIL_LIQUIDITY_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchMarketProbabilityTailLiquidityFloorConfig",
    "ResearchMarketProbabilityTailLiquidityFloorObservation",
    "ResearchMarketProbabilityTailLiquidityFloorRow",
    "ResearchMarketProbabilityTailLiquidityFloorReport",
    "build_research_market_probability_tail_liquidity_floor_report",
    "research_market_probability_tail_liquidity_floor_report_digest",
    "research_market_probability_tail_liquidity_floor_report_payload",
    "validate_research_market_probability_tail_liquidity_floor_report_digest",
    "validate_research_market_probability_tail_liquidity_floor_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketProbabilityTailLiquidityFloorConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_TAIL_LIQUIDITY_FLOOR_REPORT_CONFIG_VERSION
    )
    tail_probability_watch_distance: Decimal = Decimal("0.100000")
    tail_probability_block_distance: Decimal = Decimal("0.030000")
    pass_liquidity_floor_units: Decimal = Decimal("100.000000")
    watch_liquidity_floor_units: Decimal = Decimal("50.000000")
    block_liquidity_floor_units: Decimal = Decimal("20.000000")
    spread_pressure_watch_threshold: Decimal = Decimal("0.350000")
    spread_pressure_block_threshold: Decimal = Decimal("0.700000")
    tail_pressure_weight: Decimal = Decimal("0.400000")
    liquidity_pressure_weight: Decimal = Decimal("0.400000")
    spread_pressure_weight: Decimal = Decimal("0.200000")
    pressure_watch_threshold: Decimal = Decimal("0.400000")
    pressure_block_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityTailLiquidityFloorConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_TAIL_LIQUIDITY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "tail_probability_watch_distance",
            "tail_probability_block_distance",
            "spread_pressure_watch_threshold",
            "spread_pressure_block_threshold",
            "tail_pressure_weight",
            "liquidity_pressure_weight",
            "spread_pressure_weight",
            "pressure_watch_threshold",
            "pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_liquidity_floor_units",
            "watch_liquidity_floor_units",
            "block_liquidity_floor_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.tail_probability_block_distance > self.tail_probability_watch_distance:
            raise ValueError(
                "tail_probability_block_distance must not exceed "
                "tail_probability_watch_distance",
            )
        if self.block_liquidity_floor_units > self.watch_liquidity_floor_units:
            raise ValueError(
                "block_liquidity_floor_units must not exceed "
                "watch_liquidity_floor_units",
            )
        if self.watch_liquidity_floor_units > self.pass_liquidity_floor_units:
            raise ValueError(
                "watch_liquidity_floor_units must not exceed "
                "pass_liquidity_floor_units",
            )
        if self.spread_pressure_watch_threshold > self.spread_pressure_block_threshold:
            raise ValueError(
                "spread_pressure_watch_threshold must not exceed "
                "spread_pressure_block_threshold",
            )
        if self.pressure_watch_threshold > self.pressure_block_threshold:
            raise ValueError(
                "pressure_watch_threshold must not exceed pressure_block_threshold",
            )
        weight_sum = _q(
            self.tail_pressure_weight
            + self.liquidity_pressure_weight
            + self.spread_pressure_weight,
        )
        if weight_sum != ONE:
            raise ValueError("pressure weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public("config", _json_ready(asdict(self)))


@dataclass(frozen=True)
class ResearchMarketProbabilityTailLiquidityFloorObservation(_FinalPublicDataclass):
    private_reference: str
    probability: Decimal
    liquidity_depth_units: Decimal
    spread_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityTailLiquidityFloorObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "private_reference",
            _require_private_string("private_reference", self.private_reference),
        )
        object.__setattr__(
            self,
            "probability",
            _require_ratio_decimal("probability", self.probability),
        )
        object.__setattr__(
            self,
            "liquidity_depth_units",
            _require_nonnegative_decimal(
                "liquidity_depth_units",
                self.liquidity_depth_units,
            ),
        )
        object.__setattr__(
            self,
            "spread_pressure_score",
            _require_ratio_decimal("spread_pressure_score", self.spread_pressure_score),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityTailLiquidityFloorRow(_FinalPublicDataclass):
    rank: Decimal
    analysis_digest: str
    probability: Decimal
    tail_distance: Decimal
    liquidity_depth_units: Decimal
    liquidity_floor_gap_units: Decimal
    liquidity_floor_gap_ratio: Decimal
    spread_pressure_score: Decimal
    tail_pressure_score: Decimal
    tail_liquidity_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityTailLiquidityFloorRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        object.__setattr__(
            self,
            "analysis_digest",
            _require_public_digest("analysis_digest", self.analysis_digest),
        )
        for field_name in (
            "probability",
            "tail_distance",
            "liquidity_floor_gap_ratio",
            "spread_pressure_score",
            "tail_pressure_score",
            "tail_liquidity_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_depth_units", "liquidity_floor_gap_units"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public("row", _json_ready(asdict(self)))


@dataclass(frozen=True)
class ResearchMarketProbabilityTailLiquidityFloorReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    tail_observation_count: Decimal
    floor_breach_count: Decimal
    average_tail_distance: Decimal
    minimum_tail_distance: Decimal
    average_liquidity_depth_units: Decimal
    minimum_liquidity_depth_units: Decimal
    maximum_floor_gap_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketProbabilityTailLiquidityFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityTailLiquidityFloorReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_TAIL_LIQUIDITY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "tail_observation_count",
            "floor_breach_count",
            "average_tail_distance",
            "minimum_tail_distance",
            "average_liquidity_depth_units",
            "minimum_liquidity_depth_units",
            "maximum_floor_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_tail_distance",
            "minimum_tail_distance",
            "maximum_floor_gap_ratio",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
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
        expected_digest = _canonical_digest(_payload_from_report(self, include_digest=False))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        _reject_unsafe_public("report", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return _payload_from_report(self, include_digest=True)


def build_research_market_probability_tail_liquidity_floor_report(
    observations: Iterable[ResearchMarketProbabilityTailLiquidityFloorObservation],
    *,
    config: ResearchMarketProbabilityTailLiquidityFloorConfig | None = None,
    generated_at: datetime | None = None,
) -> ResearchMarketProbabilityTailLiquidityFloorReport:
    cfg = config or ResearchMarketProbabilityTailLiquidityFloorConfig()
    _require_exact_type(
        cfg,
        ResearchMarketProbabilityTailLiquidityFloorConfig,
        "config",
    )
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    try:
        items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observations") from exc
    for item in items:
        _require_exact_type(
            item,
            ResearchMarketProbabilityTailLiquidityFloorObservation,
            "observation",
        )

    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))
    derived_rows = sorted(
        (_derive_row_values(item, cfg) for item in items),
        key=_derived_sort_key,
    )
    rows = tuple(
        _row_from_derived(_count(index), values)
        for index, values in enumerate(derived_rows, start=1)
    )
    observation_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in rows if row.status == STATUS_BLOCK))
    tail_observation_count = _count(
        sum(
            1
            for row in rows
            if row.tail_distance <= cfg.tail_probability_watch_distance
        ),
    )
    floor_breach_count = _count(
        sum(1 for row in rows if row.liquidity_floor_gap_units > ZERO),
    )
    if rows:
        average_tail_distance = _q(
            sum((row.tail_distance for row in rows), ZERO) / observation_count,
        )
        minimum_tail_distance = min(row.tail_distance for row in rows)
        average_liquidity_depth_units = _q(
            sum((row.liquidity_depth_units for row in rows), ZERO) / observation_count,
        )
        minimum_liquidity_depth_units = min(row.liquidity_depth_units for row in rows)
        maximum_floor_gap_ratio = max(row.liquidity_floor_gap_ratio for row in rows)
    else:
        average_tail_distance = ZERO
        minimum_tail_distance = ZERO
        average_liquidity_depth_units = ZERO
        minimum_liquidity_depth_units = ZERO
        maximum_floor_gap_ratio = ZERO

    status = _report_status(pass_count, watch_count, block_count)
    reason_codes = _report_reason_codes(pass_count, watch_count, block_count)
    return ResearchMarketProbabilityTailLiquidityFloorReport(
        generated_at=generated,
        config_version=cfg.config_version,
        status=status,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        tail_observation_count=tail_observation_count,
        floor_breach_count=floor_breach_count,
        average_tail_distance=average_tail_distance,
        minimum_tail_distance=minimum_tail_distance,
        average_liquidity_depth_units=average_liquidity_depth_units,
        minimum_liquidity_depth_units=minimum_liquidity_depth_units,
        maximum_floor_gap_ratio=maximum_floor_gap_ratio,
        reason_codes=reason_codes,
        rows=rows,
    )


def research_market_probability_tail_liquidity_floor_report_payload(
    report: ResearchMarketProbabilityTailLiquidityFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketProbabilityTailLiquidityFloorReport:
        payload = report.payload
    elif type(report) is dict:
        payload = _copy_public_json(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketProbabilityTailLiquidityFloorReport",
        )
    validate_research_market_probability_tail_liquidity_floor_report_payload(payload)
    return payload


def research_market_probability_tail_liquidity_floor_report_digest(
    report: ResearchMarketProbabilityTailLiquidityFloorReport | dict[str, Any],
) -> str:
    payload = research_market_probability_tail_liquidity_floor_report_payload(report)
    return _canonical_digest(_unsigned_payload(payload))


def validate_research_market_probability_tail_liquidity_floor_report_digest(
    report: ResearchMarketProbabilityTailLiquidityFloorReport | dict[str, Any],
) -> bool:
    payload = research_market_probability_tail_liquidity_floor_report_payload(report)
    if payload["derived_validation_digest"] != _canonical_digest(
        _unsigned_payload(payload),
    ):
        raise ValueError("derived_validation_digest must match report payload")
    return True


def validate_research_market_probability_tail_liquidity_floor_report_payload(
    payload: dict[str, Any],
) -> bool:
    _reject_unsafe_public("payload", payload)
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    _require_timestamp_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_MARKET_PROBABILITY_TAIL_LIQUIDITY_FLOOR_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_status("status", payload["status"])
    for field_name in REPORT_DECIMAL_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _normalize_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
        public_payload=True,
    )
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_row_payload(row)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_sha256("derived_validation_digest", payload["derived_validation_digest"])
    expected_digest = _canonical_digest(_unsigned_payload(payload))
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match payload values")
    _validate_payload_consistency(payload)
    return True


def _derive_row_values(
    observation: ResearchMarketProbabilityTailLiquidityFloorObservation,
    config: ResearchMarketProbabilityTailLiquidityFloorConfig,
) -> dict[str, Any]:
    probability = observation.probability
    tail_distance = _q(min(probability, ONE - probability))
    liquidity_floor_gap_units = _q(
        max(ZERO, config.pass_liquidity_floor_units - observation.liquidity_depth_units),
    )
    liquidity_floor_gap_ratio = _q(
        min(ONE, liquidity_floor_gap_units / config.pass_liquidity_floor_units),
    )
    tail_pressure_score = _tail_pressure_score(tail_distance, config)
    pressure_score = _q(
        (tail_pressure_score * config.tail_pressure_weight)
        + (liquidity_floor_gap_ratio * config.liquidity_pressure_weight)
        + (observation.spread_pressure_score * config.spread_pressure_weight),
    )
    reason_codes = _row_reason_codes(
        tail_distance,
        observation.liquidity_depth_units,
        observation.spread_pressure_score,
        pressure_score,
        config,
    )
    return {
        "analysis_digest": _private_digest(observation.private_reference),
        "probability": probability,
        "tail_distance": tail_distance,
        "liquidity_depth_units": observation.liquidity_depth_units,
        "liquidity_floor_gap_units": liquidity_floor_gap_units,
        "liquidity_floor_gap_ratio": liquidity_floor_gap_ratio,
        "spread_pressure_score": observation.spread_pressure_score,
        "tail_pressure_score": tail_pressure_score,
        "tail_liquidity_pressure_score": pressure_score,
        "status": _row_status(reason_codes),
        "reason_codes": reason_codes,
    }


def _row_from_derived(
    rank: Decimal,
    values: dict[str, Any],
) -> ResearchMarketProbabilityTailLiquidityFloorRow:
    return ResearchMarketProbabilityTailLiquidityFloorRow(
        rank=rank,
        analysis_digest=values["analysis_digest"],
        probability=values["probability"],
        tail_distance=values["tail_distance"],
        liquidity_depth_units=values["liquidity_depth_units"],
        liquidity_floor_gap_units=values["liquidity_floor_gap_units"],
        liquidity_floor_gap_ratio=values["liquidity_floor_gap_ratio"],
        spread_pressure_score=values["spread_pressure_score"],
        tail_pressure_score=values["tail_pressure_score"],
        tail_liquidity_pressure_score=values["tail_liquidity_pressure_score"],
        status=values["status"],
        reason_codes=values["reason_codes"],
    )


def _derived_sort_key(values: dict[str, Any]) -> tuple[object, ...]:
    return (
        STATUS_SORT[values["status"]],
        -values["tail_liquidity_pressure_score"],
        values["tail_distance"],
        values["analysis_digest"],
    )


def _tail_pressure_score(
    tail_distance: Decimal,
    config: ResearchMarketProbabilityTailLiquidityFloorConfig,
) -> Decimal:
    if tail_distance <= config.tail_probability_block_distance:
        return ONE
    if tail_distance >= config.tail_probability_watch_distance:
        return ZERO
    denominator = (
        config.tail_probability_watch_distance
        - config.tail_probability_block_distance
    )
    if denominator <= ZERO:
        return ONE
    return _q((config.tail_probability_watch_distance - tail_distance) / denominator)


def _row_reason_codes(
    tail_distance: Decimal,
    liquidity_depth_units: Decimal,
    spread_pressure_score: Decimal,
    pressure_score: Decimal,
    config: ResearchMarketProbabilityTailLiquidityFloorConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if tail_distance <= config.tail_probability_block_distance:
        reason_codes.append(REASON_TAIL_PROBABILITY_BLOCK)
    elif tail_distance <= config.tail_probability_watch_distance:
        reason_codes.append(REASON_TAIL_PROBABILITY_WATCH)
    if liquidity_depth_units <= config.block_liquidity_floor_units:
        reason_codes.append(REASON_LIQUIDITY_FLOOR_BLOCK)
    elif liquidity_depth_units < config.watch_liquidity_floor_units:
        reason_codes.append(REASON_LIQUIDITY_FLOOR_WATCH)
    if spread_pressure_score >= config.spread_pressure_block_threshold:
        reason_codes.append(REASON_SPREAD_PRESSURE_BLOCK)
    elif spread_pressure_score >= config.spread_pressure_watch_threshold:
        reason_codes.append(REASON_SPREAD_PRESSURE_WATCH)
    if pressure_score >= config.pressure_block_threshold:
        reason_codes.append(REASON_PRESSURE_BLOCK)
    elif pressure_score >= config.pressure_watch_threshold:
        reason_codes.append(REASON_PRESSURE_WATCH)
    if not reason_codes:
        return (REASON_ROW_PASS,)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> str:
    if block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> tuple[str, ...]:
    if pass_count == ZERO and watch_count == ZERO and block_count == ZERO:
        return (REASON_EMPTY_INPUT,)
    reason_codes: list[str] = []
    if block_count > ZERO:
        reason_codes.append(REASON_REPORT_BLOCK)
    if watch_count > ZERO:
        reason_codes.append(REASON_REPORT_WATCH)
    if pass_count > ZERO:
        reason_codes.append(REASON_REPORT_PASS)
    return tuple(reason_codes)


def _payload_from_report(
    report: ResearchMarketProbabilityTailLiquidityFloorReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _timestamp_payload(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "observation_count": _decimal_payload(report.observation_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "tail_observation_count": _decimal_payload(report.tail_observation_count),
        "floor_breach_count": _decimal_payload(report.floor_breach_count),
        "average_tail_distance": _decimal_payload(report.average_tail_distance),
        "minimum_tail_distance": _decimal_payload(report.minimum_tail_distance),
        "average_liquidity_depth_units": _decimal_payload(
            report.average_liquidity_depth_units,
        ),
        "minimum_liquidity_depth_units": _decimal_payload(
            report.minimum_liquidity_depth_units,
        ),
        "maximum_floor_gap_ratio": _decimal_payload(report.maximum_floor_gap_ratio),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return {
        key: payload[key]
        for key in REPORT_PAYLOAD_KEYS
        if include_digest or key != "derived_validation_digest"
    }


def _row_payload(row: ResearchMarketProbabilityTailLiquidityFloorRow) -> dict[str, Any]:
    return {
        "rank": _decimal_payload(row.rank),
        "analysis_digest": row.analysis_digest,
        "probability": _decimal_payload(row.probability),
        "tail_distance": _decimal_payload(row.tail_distance),
        "liquidity_depth_units": _decimal_payload(row.liquidity_depth_units),
        "liquidity_floor_gap_units": _decimal_payload(row.liquidity_floor_gap_units),
        "liquidity_floor_gap_ratio": _decimal_payload(row.liquidity_floor_gap_ratio),
        "spread_pressure_score": _decimal_payload(row.spread_pressure_score),
        "tail_pressure_score": _decimal_payload(row.tail_pressure_score),
        "tail_liquidity_pressure_score": _decimal_payload(
            row.tail_liquidity_pressure_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_payload_consistency(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    pass_count = _count(sum(1 for row in rows if row["status"] == STATUS_PASS))
    watch_count = _count(sum(1 for row in rows if row["status"] == STATUS_WATCH))
    block_count = _count(sum(1 for row in rows if row["status"] == STATUS_BLOCK))
    observation_count = _count(len(rows))
    if _decimal_from_payload(payload["observation_count"]) != observation_count:
        raise ValueError("observation_count must match rows")
    if _decimal_from_payload(payload["pass_count"]) != pass_count:
        raise ValueError("pass_count must match rows")
    if _decimal_from_payload(payload["watch_count"]) != watch_count:
        raise ValueError("watch_count must match rows")
    if _decimal_from_payload(payload["block_count"]) != block_count:
        raise ValueError("block_count must match rows")
    cfg = ResearchMarketProbabilityTailLiquidityFloorConfig()
    tail_count = _count(
        sum(
            1
            for row in rows
            if _decimal_from_payload(row["tail_distance"])
            <= cfg.tail_probability_watch_distance
        ),
    )
    floor_count = _count(
        sum(
            1
            for row in rows
            if _decimal_from_payload(row["liquidity_floor_gap_units"]) > ZERO
        ),
    )
    if _decimal_from_payload(payload["tail_observation_count"]) != tail_count:
        raise ValueError("tail_observation_count must match rows")
    if _decimal_from_payload(payload["floor_breach_count"]) != floor_count:
        raise ValueError("floor_breach_count must match rows")
    if rows:
        denominator = observation_count
        average_tail_distance = _q(
            sum(
                (_decimal_from_payload(row["tail_distance"]) for row in rows),
                ZERO,
            )
            / denominator,
        )
        minimum_tail_distance = min(
            _decimal_from_payload(row["tail_distance"]) for row in rows
        )
        average_liquidity_depth_units = _q(
            sum(
                (
                    _decimal_from_payload(row["liquidity_depth_units"])
                    for row in rows
                ),
                ZERO,
            )
            / denominator,
        )
        minimum_liquidity_depth_units = min(
            _decimal_from_payload(row["liquidity_depth_units"]) for row in rows
        )
        maximum_floor_gap_ratio = max(
            _decimal_from_payload(row["liquidity_floor_gap_ratio"]) for row in rows
        )
    else:
        average_tail_distance = ZERO
        minimum_tail_distance = ZERO
        average_liquidity_depth_units = ZERO
        minimum_liquidity_depth_units = ZERO
        maximum_floor_gap_ratio = ZERO
    expected_values = {
        "average_tail_distance": average_tail_distance,
        "minimum_tail_distance": minimum_tail_distance,
        "average_liquidity_depth_units": average_liquidity_depth_units,
        "minimum_liquidity_depth_units": minimum_liquidity_depth_units,
        "maximum_floor_gap_ratio": maximum_floor_gap_ratio,
    }
    for field_name, expected in expected_values.items():
        if _decimal_from_payload(payload[field_name]) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _report_status(pass_count, watch_count, block_count)
    if payload["status"] != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = list(_report_reason_codes(pass_count, watch_count, block_count))
    if payload["reason_codes"] != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _validate_report_consistency(
    report: ResearchMarketProbabilityTailLiquidityFloorReport,
) -> None:
    pass_count = _count(sum(1 for row in report.rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in report.rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in report.rows if row.status == STATUS_BLOCK))
    observation_count = _count(len(report.rows))
    if report.observation_count != observation_count:
        raise ValueError("observation_count must match rows")
    if report.pass_count != pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != block_count:
        raise ValueError("block_count must match rows")
    if report.status != _report_status(pass_count, watch_count, block_count):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(pass_count, watch_count, block_count):
        raise ValueError("reason_codes must match rows")


def _validate_row(row: ResearchMarketProbabilityTailLiquidityFloorRow) -> None:
    status = _row_status(row.reason_codes)
    if row.status != status:
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (REASON_ROW_PASS,):
        raise ValueError("pass rows must use the pass reason")
    if row.status != STATUS_PASS and REASON_ROW_PASS in row.reason_codes:
        raise ValueError("non-pass rows must not use the pass reason")


def _validate_row_payload(row: object) -> None:
    if type(row) is not dict:
        raise ValueError("row must be a JSON object")
    _reject_unsafe_public("row", row)
    _require_payload_keys("row", row, ROW_PAYLOAD_KEYS)
    _require_public_digest("analysis_digest", row["analysis_digest"])
    for field_name in ROW_DECIMAL_FIELDS:
        _require_decimal_string(field_name, row[field_name])
    _require_status("status", row["status"])
    _normalize_reason_codes(
        "row.reason_codes",
        row["reason_codes"],
        ROW_REASON_CODES,
        public_payload=True,
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        if row[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    status = _row_status(tuple(row["reason_codes"]))
    if row["status"] != status:
        raise ValueError("row status must match reason_codes")


def _normalize_rows(
    rows: tuple[ResearchMarketProbabilityTailLiquidityFloorRow, ...],
) -> tuple[ResearchMarketProbabilityTailLiquidityFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchMarketProbabilityTailLiquidityFloorRow, "row")
    ranks = tuple(row.rank for row in rows)
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if ranks != expected_ranks:
        raise ValueError("row ranks must be consecutive")
    return rows


def _copy_public_json(value: Any) -> Any:
    if value is None:
        return None
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is list:
        return [_copy_public_json(item) for item in value]
    if type(value) is dict:
        return {
            _require_public_string("payload key", key): _copy_public_json(item)
            for key, item in value.items()
        }
    raise ValueError("payload value is not public JSON")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return _decimal_payload(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be an exact Decimal")
    if type(value) is datetime:
        return _timestamp_payload(value)
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numerics must use Decimal-derived strings")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            _require_public_string("JSON object key", key): _json_ready(item)
            for key, item in value.items()
        }
    raise ValueError("value is not JSON serializable")


def _unsigned_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    return unsigned


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _private_digest(value: str) -> str:
    return f"{SHA256_PREFIX}{sha256(value.encode('utf-8')).hexdigest()}"


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be an exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _timestamp_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _q(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


def _count(value: int) -> Decimal:
    return _q(Decimal(value))


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload value must be an exact Decimal")
    if not value.is_finite():
        raise ValueError("payload Decimal must be finite")
    return format(_q(value), "f")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _q(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return decimal_value


def _require_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    if format(_q(decimal_value), "f") != value:
        raise ValueError(f"{name} must use 6 decimal places")
    return decimal_value


def _decimal_from_payload(value: object) -> Decimal:
    return _require_decimal_string("payload Decimal", value)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{name} must be canonical text")
    return value


def _require_private_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value


def _require_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a SHA-256 digest")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{name} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a SHA-256 digest") from exc
    return value


def _require_public_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a public digest")
    if not value.startswith(SHA256_PREFIX):
        raise ValueError(f"{name} must be a public digest")
    _require_sha256(name, value[len(SHA256_PREFIX) :])
    return value


def _normalize_reason_codes(
    name: str,
    values: object,
    allowed_values: tuple[str, ...],
    *,
    public_payload: bool = False,
) -> tuple[str, ...]:
    expected_container = list if public_payload else tuple
    if type(values) is not expected_container:
        raise ValueError(f"{name} must be a {expected_container.__name__}")
    if not values:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{name} entries must be strings")
        if value not in allowed_values:
            raise ValueError(f"{name} contains an unsupported reason code")
        if value in normalized:
            raise ValueError(f"{name} must not contain duplicates")
        normalized.append(value)
    order = {reason_code: index for index, reason_code in enumerate(allowed_values)}
    sorted_values = tuple(sorted(normalized, key=lambda reason_code: order[reason_code]))
    if tuple(normalized) != sorted_values:
        raise ValueError(f"{name} must use canonical ordering")
    return sorted_values


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_payload_keys(
    name: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{name} must be a JSON object")
    for key in payload:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
    expected = set(expected_keys)
    actual = set(payload)
    if actual != expected:
        raise ValueError(f"{name} must use the supported public payload fields")


def _require_timestamp_string(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a timestamp string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO timestamp string") from exc
    return _as_utc(name, parsed)


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


for _public_dataclass in (
    ResearchMarketProbabilityTailLiquidityFloorConfig,
    ResearchMarketProbabilityTailLiquidityFloorObservation,
    ResearchMarketProbabilityTailLiquidityFloorRow,
    ResearchMarketProbabilityTailLiquidityFloorReport,
):
    for _field in fields(_public_dataclass):
        if _field.name in {"private_reference"}:
            continue
        if _has_unsafe_fragment(_field.name):
            raise RuntimeError(f"unsafe public dataclass field: {_field.name}")
del _field
del _public_dataclass
