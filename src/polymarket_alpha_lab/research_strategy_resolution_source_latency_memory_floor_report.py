"""Readonly paper report for resolution source latency memory floor."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_RESOLUTION_SOURCE_LATENCY_MEMORY_FLOOR_CONFIG_VERSION = (
    "research-strategy-resolution-source-latency-memory-floor-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
SECONDS_PER_MINUTE = Decimal("60")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

STATUSES = ("pass", "watch", "block")
STATUS_SORT_PRIORITY = {"block": 0, "watch": 1, "pass": 2}
SOURCE_FAMILIES = ("official", "primary", "secondary")
EMPTY_REASON_CODE = "source_latency_memory_floor_report_empty"
ROW_REASON_CODES = (
    "source_latency_memory_floor_block",
    "source_latency_memory_floor_watch",
    "source_latency_memory_floor_pass",
    "source_latency_pressure_high",
    "source_latency_pressure_elevated",
    "memory_age_pressure_high",
    "memory_age_pressure_elevated",
    "source_memory_floor_below_watch",
    "source_memory_floor_below_pass",
)
REPORT_REASON_CODES = (EMPTY_REASON_CODE, *ROW_REASON_CODES)
REF_DENYLIST = (
    "0x",
    "@",
    "://",
    "api" "_" "key",
    "au" "th",
    "bearer ",
    "can" "didate",
    "d" "sn",
    "mar" "ket",
    "private",
    "ques" "tion",
    "se" "cret",
    "tab" "le",
    "to" "ken",
    "tr" "ade",
    "wal" "let",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_SOURCE_LATENCY_MEMORY_FLOOR_CONFIG_VERSION",
    "ResearchStrategyResolutionSourceLatencyMemoryFloorConfig",
    "ResearchStrategyResolutionSourceLatencyMemoryFloorObservation",
    "ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount",
    "ResearchStrategyResolutionSourceLatencyMemoryFloorReport",
    "ResearchStrategyResolutionSourceLatencyMemoryFloorRow",
    "build_research_strategy_resolution_source_latency_memory_floor_report",
    "research_strategy_resolution_source_latency_memory_floor_payload",
)


@dataclass(frozen=True)
class ResearchStrategyResolutionSourceLatencyMemoryFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_RESOLUTION_SOURCE_LATENCY_MEMORY_FLOOR_CONFIG_VERSION
    )
    max_source_latency_minutes: Decimal = Decimal("240")
    max_memory_age_minutes: Decimal = Decimal("720")
    latency_penalty_weight: Decimal = Decimal("0.400000")
    memory_age_penalty_weight: Decimal = Decimal("0.400000")
    pass_memory_floor_score: Decimal = Decimal("0.700000")
    watch_memory_floor_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_source_latency_minutes", "max_memory_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latency_penalty_weight",
            "memory_age_penalty_weight",
            "pass_memory_floor_score",
            "watch_memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        if self.pass_memory_floor_score < self.watch_memory_floor_score:
            raise ValueError("pass_memory_floor_score must not be below watch")
        _require_hard_flags(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorConfig",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyResolutionSourceLatencyMemoryFloorObservation:
    strategy_ref: str
    resolution_ref: str
    source_family: str
    resolution_observed_at: datetime
    source_first_seen_at: datetime
    memory_checked_at: datetime
    source_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "strategy_ref",
            _redacted_ref("strategy_ref", "strategy_ref", self.strategy_ref),
        )
        object.__setattr__(
            self,
            "resolution_ref",
            _redacted_ref("resolution_ref", "resolution_ref", self.resolution_ref),
        )
        object.__setattr__(
            self,
            "source_family",
            _require_member("source_family", self.source_family, SOURCE_FAMILIES),
        )
        for field_name in (
            "resolution_observed_at",
            "source_first_seen_at",
            "memory_checked_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_confidence_score",
            _normalize_score("source_confidence_score", self.source_confidence_score),
        )
        if self.source_first_seen_at < self.resolution_observed_at:
            raise ValueError("source_first_seen_at must be on or after resolution_observed_at")
        if self.memory_checked_at < self.source_first_seen_at:
            raise ValueError("memory_checked_at must be on or after source_first_seen_at")
        _require_hard_flags(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorObservation",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorObservation",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyResolutionSourceLatencyMemoryFloorRow:
    rank: Decimal
    strategy_ref: str
    resolution_ref: str
    source_family: str
    resolution_observed_at: datetime
    source_first_seen_at: datetime
    memory_checked_at: datetime
    source_confidence_score: Decimal
    source_latency_minutes: Decimal
    memory_age_minutes: Decimal
    latency_pressure_score: Decimal
    memory_age_pressure_score: Decimal
    source_memory_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_redacted_ref("strategy_ref", self.strategy_ref, "strategy_ref")
        _require_redacted_ref("resolution_ref", self.resolution_ref, "resolution_ref")
        object.__setattr__(
            self,
            "source_family",
            _require_member("source_family", self.source_family, SOURCE_FAMILIES),
        )
        for field_name in (
            "resolution_observed_at",
            "source_first_seen_at",
            "memory_checked_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_confidence_score",
            "latency_pressure_score",
            "memory_age_pressure_score",
            "source_memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_latency_minutes", "memory_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "status",
            _require_member("status", self.status, STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorRow",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorRow",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, ROW_REASON_CODES),
        )
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchStrategyResolutionSourceLatencyMemoryFloorReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_latency_minutes: Decimal
    average_memory_age_minutes: Decimal
    average_source_memory_floor_score: Decimal
    minimum_source_memory_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_latency_minutes",
            "average_memory_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_memory_floor_score",
            "minimum_source_memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        _require_hard_flags(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorReport",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorReport",
            self.payload,
        )

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(_dataclass_values(self))
        _reject_unsafe_public_payload(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorReport.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_resolution_source_latency_memory_floor_report(
    records: Iterable[object],
    *,
    config: ResearchStrategyResolutionSourceLatencyMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchStrategyResolutionSourceLatencyMemoryFloorReport:
    if type(config) is not ResearchStrategyResolutionSourceLatencyMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchStrategyResolutionSourceLatencyMemoryFloorConfig",
        )
    _require_hard_flags(
        "ResearchStrategyResolutionSourceLatencyMemoryFloorConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_records(records)
    for observation in observations:
        if observation.memory_checked_at > generated_at_utc:
            raise ValueError("memory_checked_at must not be in the future")
    rows_without_rank = tuple(
        _row_values(observation=observation, config=config)
        for observation in observations
    )
    sorted_values = tuple(sorted(rows_without_rank, key=_row_values_sort_key))
    rows = tuple(
        ResearchStrategyResolutionSourceLatencyMemoryFloorRow(
            rank=_count(index),
            **values,
        )
        for index, values in enumerate(sorted_values, start=1)
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "observation_count": _count(len(observations)),
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_source_latency_minutes": _average_decimal(
            tuple(row.source_latency_minutes for row in rows),
        ),
        "average_memory_age_minutes": _average_decimal(
            tuple(row.memory_age_minutes for row in rows),
        ),
        "average_source_memory_floor_score": _average_decimal(
            tuple(row.source_memory_floor_score for row in rows),
        ),
        "minimum_source_memory_floor_score": _minimum_score(
            tuple(row.source_memory_floor_score for row in rows),
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["validation_digest"] = _validation_digest(values)
    return ResearchStrategyResolutionSourceLatencyMemoryFloorReport(**values)


def research_strategy_resolution_source_latency_memory_floor_payload(
    report: ResearchStrategyResolutionSourceLatencyMemoryFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyResolutionSourceLatencyMemoryFloorReport:
        raise ValueError(
            "report must be a ResearchStrategyResolutionSourceLatencyMemoryFloorReport",
        )
    _require_hard_flags(
        "ResearchStrategyResolutionSourceLatencyMemoryFloorReport",
        report,
    )
    _validate_report(report)
    return report.payload


def _row_values(
    *,
    observation: ResearchStrategyResolutionSourceLatencyMemoryFloorObservation,
    config: ResearchStrategyResolutionSourceLatencyMemoryFloorConfig,
) -> dict[str, object]:
    source_latency_minutes = _minutes_between(
        observation.resolution_observed_at,
        observation.source_first_seen_at,
    )
    memory_age_minutes = _minutes_between(
        observation.source_first_seen_at,
        observation.memory_checked_at,
    )
    latency_pressure_score = _clamp_score(
        _safe_ratio(source_latency_minutes, config.max_source_latency_minutes),
    )
    memory_age_pressure_score = _clamp_score(
        _safe_ratio(memory_age_minutes, config.max_memory_age_minutes),
    )
    source_memory_floor_score = _source_memory_floor_score(
        source_confidence_score=observation.source_confidence_score,
        latency_pressure_score=latency_pressure_score,
        memory_age_pressure_score=memory_age_pressure_score,
        config=config,
    )
    status = _row_status(source_memory_floor_score, config)
    return {
        "strategy_ref": observation.strategy_ref,
        "resolution_ref": observation.resolution_ref,
        "source_family": observation.source_family,
        "resolution_observed_at": observation.resolution_observed_at,
        "source_first_seen_at": observation.source_first_seen_at,
        "memory_checked_at": observation.memory_checked_at,
        "source_confidence_score": observation.source_confidence_score,
        "source_latency_minutes": source_latency_minutes,
        "memory_age_minutes": memory_age_minutes,
        "latency_pressure_score": latency_pressure_score,
        "memory_age_pressure_score": memory_age_pressure_score,
        "source_memory_floor_score": source_memory_floor_score,
        "status": status,
        "reason_codes": _row_reason_codes(
            status=status,
            latency_pressure_score=latency_pressure_score,
            memory_age_pressure_score=memory_age_pressure_score,
            source_memory_floor_score=source_memory_floor_score,
            config=config,
        ),
    }


def _source_memory_floor_score(
    *,
    source_confidence_score: Decimal,
    latency_pressure_score: Decimal,
    memory_age_pressure_score: Decimal,
    config: ResearchStrategyResolutionSourceLatencyMemoryFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            source_confidence_score
            - (latency_pressure_score * config.latency_penalty_weight)
            - (memory_age_pressure_score * config.memory_age_penalty_weight)
        )
    return _clamp_score(score)


def _row_status(
    score: Decimal,
    config: ResearchStrategyResolutionSourceLatencyMemoryFloorConfig,
) -> str:
    if score < config.watch_memory_floor_score:
        return "block"
    if score < config.pass_memory_floor_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    latency_pressure_score: Decimal,
    memory_age_pressure_score: Decimal,
    source_memory_floor_score: Decimal,
    config: ResearchStrategyResolutionSourceLatencyMemoryFloorConfig,
) -> tuple[str, ...]:
    codes: list[str] = [f"source_latency_memory_floor_{status}"]
    if latency_pressure_score >= ONE_SCORE:
        codes.append("source_latency_pressure_high")
    elif latency_pressure_score > Decimal("0.500000"):
        codes.append("source_latency_pressure_elevated")
    if memory_age_pressure_score >= ONE_SCORE:
        codes.append("memory_age_pressure_high")
    elif memory_age_pressure_score > Decimal("0.500000"):
        codes.append("memory_age_pressure_elevated")
    if source_memory_floor_score < config.watch_memory_floor_score:
        codes.append("source_memory_floor_below_watch")
    elif source_memory_floor_score < config.pass_memory_floor_score:
        codes.append("source_memory_floor_below_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(code for code in REPORT_REASON_CODES[1:] if code in observed)


def _reason_code_counts(
    rows: tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorRow, ...],
) -> tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        sorted(
            (
                ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount(
                    reason_code=reason_code,
                    count=_count(count),
                )
                for reason_code, count in counts.items()
            ),
            key=_reason_count_sort_key,
        ),
    )


def _validate_row(row: ResearchStrategyResolutionSourceLatencyMemoryFloorRow) -> None:
    if row.source_first_seen_at < row.resolution_observed_at:
        raise ValueError("source_first_seen_at must be on or after resolution_observed_at")
    if row.memory_checked_at < row.source_first_seen_at:
        raise ValueError("memory_checked_at must be on or after source_first_seen_at")
    if row.source_latency_minutes != _minutes_between(
        row.resolution_observed_at,
        row.source_first_seen_at,
    ):
        raise ValueError("source_latency_minutes must match timestamps")
    if row.memory_age_minutes != _minutes_between(
        row.source_first_seen_at,
        row.memory_checked_at,
    ):
        raise ValueError("memory_age_minutes must match timestamps")
    if f"source_latency_memory_floor_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchStrategyResolutionSourceLatencyMemoryFloorReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    expected_ranks = tuple(_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.rank for row in report.rows) != expected_ranks:
        raise ValueError("rows must be deterministically ranked")
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    for status in STATUSES:
        field_name = "block_count" if status == "block" else f"{status}_count"
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.average_source_latency_minutes != _average_decimal(
        tuple(row.source_latency_minutes for row in report.rows),
    ):
        raise ValueError("average_source_latency_minutes must match rows")
    if report.average_memory_age_minutes != _average_decimal(
        tuple(row.memory_age_minutes for row in report.rows),
    ):
        raise ValueError("average_memory_age_minutes must match rows")
    if report.average_source_memory_floor_score != _average_decimal(
        tuple(row.source_memory_floor_score for row in report.rows),
    ):
        raise ValueError("average_source_memory_floor_score must match rows")
    if report.minimum_source_memory_floor_score != _minimum_score(
        tuple(row.source_memory_floor_score for row in report.rows),
    ):
        raise ValueError("minimum_source_memory_floor_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.validation_digest != _validation_digest(_dataclass_values(report)):
        raise ValueError("validation_digest must match report payload")


def _normalize_records(
    records: Iterable[object],
) -> tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorObservation, ...]:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be an iterable")
    try:
        normalized = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    observations: list[ResearchStrategyResolutionSourceLatencyMemoryFloorObservation] = []
    for record in normalized:
        if type(record) is not ResearchStrategyResolutionSourceLatencyMemoryFloorObservation:
            raise ValueError(
                "records must contain ResearchStrategyResolutionSourceLatencyMemoryFloorObservation values",
            )
        _require_hard_flags(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorObservation",
            record,
        )
        key = (record.strategy_ref, record.resolution_ref, record.source_family)
        if key in seen_keys:
            raise ValueError("records must be unique")
        seen_keys.add(key)
        observations.append(record)
    return tuple(observations)


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchStrategyResolutionSourceLatencyMemoryFloorRow:
            raise ValueError(
                "rows must contain ResearchStrategyResolutionSourceLatencyMemoryFloorRow values",
            )
        _require_hard_flags("ResearchStrategyResolutionSourceLatencyMemoryFloorRow", row)
        key = (row.strategy_ref, row.resolution_ref, row.source_family)
        if key in seen_keys:
            raise ValueError("rows must be unique")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    items = tuple(value)
    seen_codes: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount values",
            )
        _require_hard_flags(
            "ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount",
            item,
        )
        if item.reason_code in seen_codes:
            raise ValueError("reason_code_counts values must be unique")
        seen_codes.add(item.reason_code)
    if items != tuple(sorted(items, key=_reason_count_sort_key)):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return items


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed_codes)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(code for code in allowed_codes if code in codes)
    if codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return codes


def _row_values_sort_key(values: dict[str, object]) -> tuple[int, Decimal, Decimal, str, str, str]:
    status = values["status"]
    floor_score = values["source_memory_floor_score"]
    latency_minutes = values["source_latency_minutes"]
    strategy_ref = values["strategy_ref"]
    resolution_ref = values["resolution_ref"]
    source_family = values["source_family"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    if type(floor_score) is not Decimal:
        raise ValueError("source_memory_floor_score must be a Decimal")
    if type(latency_minutes) is not Decimal:
        raise ValueError("source_latency_minutes must be a Decimal")
    if type(strategy_ref) is not str:
        raise ValueError("strategy_ref must be a string")
    if type(resolution_ref) is not str:
        raise ValueError("resolution_ref must be a string")
    if type(source_family) is not str:
        raise ValueError("source_family must be a string")
    return (
        STATUS_SORT_PRIORITY[status],
        floor_score,
        -latency_minutes,
        strategy_ref,
        resolution_ref,
        source_family,
    )


def _row_sort_key(
    row: ResearchStrategyResolutionSourceLatencyMemoryFloorRow,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        STATUS_SORT_PRIORITY[row.status],
        row.source_memory_floor_score,
        -row.source_latency_minutes,
        row.strategy_ref,
        row.resolution_ref,
        row.source_family,
    )


def _reason_count_sort_key(
    item: ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount,
) -> tuple[Decimal, int, str]:
    return (-item.count, _reason_priority(item.reason_code), item.reason_code)


def _reason_priority(reason_code: str) -> int:
    try:
        return ROW_REASON_CODES.index(reason_code)
    except ValueError:
        return len(ROW_REASON_CODES)


def _status_count(
    rows: tuple[ResearchStrategyResolutionSourceLatencyMemoryFloorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_SCORE) / Decimal(len(values))).quantize(SCORE_QUANTUM)


def _minimum_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    return min(values).quantize(SCORE_QUANTUM)


def _minutes_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
        )
        * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return (
            total_microseconds / MICROSECONDS_PER_SECOND / SECONDS_PER_MINUTE
        ).quantize(SCORE_QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO_SCORE:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(SCORE_QUANTUM)


def _clamp_score(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE_SCORE, max(ZERO_SCORE, value)).quantize(SCORE_QUANTUM)


def _normalize_score(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SCORE or decimal_value > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(SCORE_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value.quantize(SCORE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(SCORE_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> str:
    text = _canonical_string(field_name, value)
    if text not in choices:
        raise ValueError(f"{field_name} must be a known value")
    return text


def _require_canonical_string(field_name: str, value: object) -> None:
    _canonical_string(field_name, value)


def _canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _redacted_ref(field_name: str, prefix: str, value: object) -> str:
    raw_value = _canonical_string(field_name, value)
    digest = sha256(raw_value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _require_redacted_ref(field_name: str, value: object, prefix: str) -> None:
    text = _canonical_string(field_name, value)
    if not text.startswith(f"{prefix}_"):
        raise ValueError(f"{field_name} must be redacted")
    if _has_ref_marker(text):
        raise ValueError(f"{field_name} must be redacted")


def _has_ref_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in REF_DENYLIST)


def _require_sha256_digest(field_name: str, value: object) -> None:
    text = _canonical_string(field_name, value)
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _dataclass_values(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


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
    if type(value) is int:
        raise ValueError("payload numbers must use Decimal")
    raise ValueError("payload contains unsupported value")


def _validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "validation_digest"
    }
    _reject_unsafe_public_payload("validation digest payload", digest_payload)
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
    if _has_ref_marker(value):
        raise ValueError(f"unsafe public payload in {label}")
