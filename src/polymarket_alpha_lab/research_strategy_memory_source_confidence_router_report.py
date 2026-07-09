"""Report-only memory confidence router research snapshot."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_REPORT_VERSION = (
    "research-strategy-memory-source-confidence-router-report-v0"
)
RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_ROUTE_READY = "memory_source_confidence_route_ready"
REASON_REVIEW_REQUESTED = "memory_source_confidence_review_requested"
REASON_ROUTER_PASS = "memory_source_confidence_router_pass"
REASON_ROUTE_SCORE_BLOCK = "route_score_block"
REASON_ROUTE_SCORE_WATCH = "route_score_watch"
REASON_MEMORY_CONFIDENCE_BLOCK = "memory_confidence_block"
REASON_MEMORY_CONFIDENCE_WATCH = "memory_confidence_watch"
REASON_SOURCE_CONFIDENCE_BLOCK = "source_confidence_block"
REASON_SOURCE_CONFIDENCE_WATCH = "source_confidence_watch"
REASON_TRACE_CONFIDENCE_BLOCK = "trace_confidence_block"
REASON_TRACE_CONFIDENCE_WATCH = "trace_confidence_watch"
REASON_FRESHNESS_BLOCK = "freshness_block"
REASON_FRESHNESS_WATCH = "freshness_watch"
REASON_CONFLICT_BLOCK = "conflict_block"
REASON_CONFLICT_WATCH = "conflict_watch"
REASON_REPORT_PASS = "memory_source_confidence_router_report_pass"
REASON_REPORT_WATCH = "memory_source_confidence_router_report_watch"
REASON_REPORT_BLOCK = "memory_source_confidence_router_report_block"
REASON_NO_INPUTS = "memory_source_confidence_router_no_inputs"

UPSTREAM_REASON_CODES = (
    REASON_ROUTE_READY,
    REASON_REVIEW_REQUESTED,
)
ROW_REASON_CODES = (
    REASON_ROUTER_PASS,
    REASON_ROUTE_READY,
    REASON_REVIEW_REQUESTED,
    REASON_ROUTE_SCORE_BLOCK,
    REASON_ROUTE_SCORE_WATCH,
    REASON_MEMORY_CONFIDENCE_BLOCK,
    REASON_MEMORY_CONFIDENCE_WATCH,
    REASON_SOURCE_CONFIDENCE_BLOCK,
    REASON_SOURCE_CONFIDENCE_WATCH,
    REASON_TRACE_CONFIDENCE_BLOCK,
    REASON_TRACE_CONFIDENCE_WATCH,
    REASON_FRESHNESS_BLOCK,
    REASON_FRESHNESS_WATCH,
    REASON_CONFLICT_BLOCK,
    REASON_CONFLICT_WATCH,
)
REPORT_REASON_CODES = (
    REASON_REPORT_PASS,
    REASON_REPORT_WATCH,
    REASON_REPORT_BLOCK,
    REASON_NO_INPUTS,
)
REASON_SEQUENCE = ROW_REASON_CODES + REPORT_REASON_CODES

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
STATUS_VALUES = frozenset(RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_STATUSES)
FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PUBLIC_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "candidate=",
    "market=",
    "source_url",
    "raw_text",
    "raw text",
    "dsn=",
    "postgres://",
    "mysql://",
    "sqlite://",
    "http://",
    "https://",
    "://",
    "token=",
    "wallet key",
    "auth secret",
    "order id",
    "live trading",
    "position sizing",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_REPORT_VERSION",
    "RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_STATUSES",
    "ResearchStrategyMemorySourceConfidenceRouterConfig",
    "ResearchStrategyMemorySourceConfidenceRouterInput",
    "ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount",
    "ResearchStrategyMemorySourceConfidenceRouterReport",
    "ResearchStrategyMemorySourceConfidenceRouterRow",
    "build_research_strategy_memory_source_confidence_router_report",
    "research_strategy_memory_source_confidence_router_report_digest",
    "research_strategy_memory_source_confidence_router_report_payload",
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
class ResearchStrategyMemorySourceConfidenceRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_REPORT_VERSION
    )
    min_pass_route_score: Decimal = Decimal("0.700000")
    min_watch_route_score: Decimal = Decimal("0.400000")
    min_pass_memory_confidence_score: Decimal = Decimal("0.700000")
    min_watch_memory_confidence_score: Decimal = Decimal("0.500000")
    min_pass_source_confidence_score: Decimal = Decimal("0.700000")
    min_watch_source_confidence_score: Decimal = Decimal("0.500000")
    min_pass_trace_confidence_score: Decimal = Decimal("0.700000")
    min_watch_trace_confidence_score: Decimal = Decimal("0.500000")
    min_pass_freshness_score: Decimal = Decimal("0.700000")
    min_watch_freshness_score: Decimal = Decimal("0.500000")
    max_pass_conflict_score: Decimal = Decimal("0.200000")
    max_watch_conflict_score: Decimal = Decimal("0.500000")
    memory_confidence_weight: Decimal = Decimal("0.350000")
    source_confidence_weight: Decimal = Decimal("0.300000")
    trace_confidence_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.150000")
    conflict_drag: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemorySourceConfidenceRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_route_score",
            "min_watch_route_score",
            "min_pass_memory_confidence_score",
            "min_watch_memory_confidence_score",
            "min_pass_source_confidence_score",
            "min_watch_source_confidence_score",
            "min_pass_trace_confidence_score",
            "min_watch_trace_confidence_score",
            "min_pass_freshness_score",
            "min_watch_freshness_score",
            "max_pass_conflict_score",
            "max_watch_conflict_score",
            "memory_confidence_weight",
            "source_confidence_weight",
            "trace_confidence_weight",
            "freshness_weight",
            "conflict_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "min_pass_route_score",
            self.min_pass_route_score,
            "min_watch_route_score",
            self.min_watch_route_score,
        )
        _require_floor_pair(
            "min_pass_memory_confidence_score",
            self.min_pass_memory_confidence_score,
            "min_watch_memory_confidence_score",
            self.min_watch_memory_confidence_score,
        )
        _require_floor_pair(
            "min_pass_source_confidence_score",
            self.min_pass_source_confidence_score,
            "min_watch_source_confidence_score",
            self.min_watch_source_confidence_score,
        )
        _require_floor_pair(
            "min_pass_trace_confidence_score",
            self.min_pass_trace_confidence_score,
            "min_watch_trace_confidence_score",
            self.min_watch_trace_confidence_score,
        )
        _require_floor_pair(
            "min_pass_freshness_score",
            self.min_pass_freshness_score,
            "min_watch_freshness_score",
            self.min_watch_freshness_score,
        )
        _require_ceiling_pair(
            "max_pass_conflict_score",
            self.max_pass_conflict_score,
            "max_watch_conflict_score",
            self.max_watch_conflict_score,
        )
        _require_weight_sum(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyMemorySourceConfidenceRouterInput(_FinalPublicDataclass):
    route_ref: str
    evaluated_at: datetime
    memory_confidence_score: Decimal
    source_confidence_score: Decimal
    trace_confidence_score: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemorySourceConfidenceRouterInput,
            "input",
        )
        object.__setattr__(
            self,
            "route_ref",
            _require_private_route_ref("route_ref", self.route_ref),
        )
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "memory_confidence_score",
            "source_confidence_score",
            "trace_confidence_score",
            "freshness_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                UPSTREAM_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyMemorySourceConfidenceRouterRow(_FinalPublicDataclass):
    route_digest: str
    evaluated_at: datetime
    aggregate_row_number: Decimal
    memory_confidence_score: Decimal
    evidence_confidence_score: Decimal
    trace_confidence_score: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    route_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemorySourceConfidenceRouterRow,
            "row",
        )
        _require_private_digest("route_digest", self.route_digest)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        for field_name in (
            "memory_confidence_score",
            "evidence_confidence_score",
            "trace_confidence_score",
            "freshness_score",
            "conflict_score",
            "route_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags("row", self)
        _set_or_validate_digest(self, "row")


@dataclass(frozen=True)
class ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code, REASON_SEQUENCE),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyMemorySourceConfidenceRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    route_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_route_score: Decimal
    lowest_route_score: Decimal
    highest_conflict_score: Decimal
    rows: tuple[ResearchStrategyMemorySourceConfidenceRouterRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemorySourceConfidenceRouterReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("route_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_route_score",
            "lowest_route_score",
            "highest_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags("report", self)
        _set_or_validate_digest(self, "report")
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        return _report_payload(self, include_digest=True)


def build_research_strategy_memory_source_confidence_router_report(
    inputs: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchStrategyMemorySourceConfidenceRouterConfig,
) -> ResearchStrategyMemorySourceConfidenceRouterReport:
    if type(config) is not ResearchStrategyMemorySourceConfidenceRouterConfig:
        raise ValueError(
            "config must be a ResearchStrategyMemorySourceConfidenceRouterConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    for item in items:
        if item.evaluated_at > generated_at_utc:
            raise ValueError("evaluated_at must not be after generated_at")

    planned = []
    seen_digests: set[str] = set()
    for item in items:
        route_digest = _private_digest(item.route_ref)
        if route_digest in seen_digests:
            raise ValueError("duplicate route_digest values are not allowed")
        seen_digests.add(route_digest)
        route_score = _route_score(item, config)
        status = _row_status(item, route_score, config)
        planned.append(
            {
                "route_digest": route_digest,
                "evaluated_at": item.evaluated_at,
                "memory_confidence_score": item.memory_confidence_score,
                "evidence_confidence_score": item.source_confidence_score,
                "trace_confidence_score": item.trace_confidence_score,
                "freshness_score": item.freshness_score,
                "conflict_score": item.conflict_score,
                "route_score": route_score,
                "status": status,
                "reason_codes": _row_reason_codes(item, route_score, status, config),
            },
        )

    planned.sort(
        key=lambda row: (
            _status_sort_key(row["status"]),
            row["route_score"],
            row["route_digest"],
        ),
    )
    rows = tuple(
        ResearchStrategyMemorySourceConfidenceRouterRow(
            aggregate_row_number=_count(index),
            **row,
        )
        for index, row in enumerate(planned, start=1)
    )
    route_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == STATUS_PASS))
    watch_count = _count(sum(1 for row in rows if row.status == STATUS_WATCH))
    block_count = _count(sum(1 for row in rows if row.status == STATUS_BLOCK))
    return ResearchStrategyMemorySourceConfidenceRouterReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        route_count=route_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_route_score=_average(tuple(row.route_score for row in rows)),
        lowest_route_score=min((row.route_score for row in rows), default=ZERO),
        highest_conflict_score=max((row.conflict_score for row in rows), default=ZERO),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, route_count),
        reason_codes=_report_reason_codes(rows),
    )


def research_strategy_memory_source_confidence_router_report_payload(
    report: ResearchStrategyMemorySourceConfidenceRouterReport,
) -> dict[str, object]:
    if type(report) is not ResearchStrategyMemorySourceConfidenceRouterReport:
        raise ValueError(
            "report must be a ResearchStrategyMemorySourceConfidenceRouterReport",
        )
    return report.payload


def research_strategy_memory_source_confidence_router_report_digest(
    report: ResearchStrategyMemorySourceConfidenceRouterReport,
) -> str:
    if type(report) is not ResearchStrategyMemorySourceConfidenceRouterReport:
        raise ValueError(
            "report must be a ResearchStrategyMemorySourceConfidenceRouterReport",
        )
    return _digest_payload(_report_payload(report, include_digest=False))


def _route_score(
    item: ResearchStrategyMemorySourceConfidenceRouterInput,
    config: ResearchStrategyMemorySourceConfidenceRouterConfig,
) -> Decimal:
    weighted_score = (
        item.memory_confidence_score * config.memory_confidence_weight
        + item.source_confidence_score * config.source_confidence_weight
        + item.trace_confidence_score * config.trace_confidence_weight
        + item.freshness_score * config.freshness_weight
    )
    conflict_penalty = item.conflict_score * config.conflict_drag
    return _clamp_ratio(_quantize(weighted_score - conflict_penalty))


def _row_status(
    item: ResearchStrategyMemorySourceConfidenceRouterInput,
    route_score: Decimal,
    config: ResearchStrategyMemorySourceConfidenceRouterConfig,
) -> str:
    if (
        route_score < config.min_watch_route_score
        or item.memory_confidence_score < config.min_watch_memory_confidence_score
        or item.source_confidence_score < config.min_watch_source_confidence_score
        or item.trace_confidence_score < config.min_watch_trace_confidence_score
        or item.freshness_score < config.min_watch_freshness_score
        or item.conflict_score > config.max_watch_conflict_score
    ):
        return STATUS_BLOCK
    if (
        route_score < config.min_pass_route_score
        or item.memory_confidence_score < config.min_pass_memory_confidence_score
        or item.source_confidence_score < config.min_pass_source_confidence_score
        or item.trace_confidence_score < config.min_pass_trace_confidence_score
        or item.freshness_score < config.min_pass_freshness_score
        or item.conflict_score > config.max_pass_conflict_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    item: ResearchStrategyMemorySourceConfidenceRouterInput,
    route_score: Decimal,
    status: str,
    config: ResearchStrategyMemorySourceConfidenceRouterConfig,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return _dedupe_reason_codes((REASON_ROUTER_PASS, *item.reason_codes))
    reason_codes: list[str] = list(item.reason_codes)
    if status == STATUS_BLOCK:
        if route_score < config.min_watch_route_score:
            reason_codes.append(REASON_ROUTE_SCORE_BLOCK)
        if item.memory_confidence_score < config.min_watch_memory_confidence_score:
            reason_codes.append(REASON_MEMORY_CONFIDENCE_BLOCK)
        if item.source_confidence_score < config.min_watch_source_confidence_score:
            reason_codes.append(REASON_SOURCE_CONFIDENCE_BLOCK)
        if item.trace_confidence_score < config.min_watch_trace_confidence_score:
            reason_codes.append(REASON_TRACE_CONFIDENCE_BLOCK)
        if item.freshness_score < config.min_watch_freshness_score:
            reason_codes.append(REASON_FRESHNESS_BLOCK)
        if item.conflict_score > config.max_watch_conflict_score:
            reason_codes.append(REASON_CONFLICT_BLOCK)
    else:
        if route_score < config.min_pass_route_score:
            reason_codes.append(REASON_ROUTE_SCORE_WATCH)
        if item.memory_confidence_score < config.min_pass_memory_confidence_score:
            reason_codes.append(REASON_MEMORY_CONFIDENCE_WATCH)
        if item.source_confidence_score < config.min_pass_source_confidence_score:
            reason_codes.append(REASON_SOURCE_CONFIDENCE_WATCH)
        if item.trace_confidence_score < config.min_pass_trace_confidence_score:
            reason_codes.append(REASON_TRACE_CONFIDENCE_WATCH)
        if item.freshness_score < config.min_pass_freshness_score:
            reason_codes.append(REASON_FRESHNESS_WATCH)
        if item.conflict_score > config.max_pass_conflict_score:
            reason_codes.append(REASON_CONFLICT_WATCH)
    return _dedupe_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchStrategyMemorySourceConfidenceRouterRow, ...],
) -> str:
    statuses = tuple(row.status for row in rows)
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses or not rows:
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyMemorySourceConfidenceRouterRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if not rows:
        return (REASON_NO_INPUTS,)
    if status == STATUS_BLOCK:
        return (REASON_REPORT_BLOCK,)
    if status == STATUS_WATCH:
        return (REASON_REPORT_WATCH,)
    return (REASON_REPORT_PASS,)


def _reason_code_counts(
    rows: tuple[ResearchStrategyMemorySourceConfidenceRouterRow, ...],
    route_count: Decimal,
) -> tuple[ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    ordered_codes = [
        reason_code for reason_code in REASON_SEQUENCE if counter.get(reason_code, 0)
    ]
    return tuple(
        ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            row_ratio=ZERO
            if route_count == ZERO
            else _quantize(_count(counter[reason_code]) / route_count),
        )
        for reason_code in ordered_codes
    )


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyMemorySourceConfidenceRouterInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchStrategyMemorySourceConfidenceRouterInput:
            raise ValueError(
                "inputs must contain ResearchStrategyMemorySourceConfidenceRouterInput items",
            )
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyMemorySourceConfidenceRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyMemorySourceConfidenceRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategyMemorySourceConfidenceRouterRow items",
            )
    return rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in values:
        if type(item) is not ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount items",
            )
    return values


def _validate_report(report: ResearchStrategyMemorySourceConfidenceRouterReport) -> None:
    rows = report.rows
    if report.route_count != _count(len(rows)):
        raise ValueError("route_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if tuple(row.aggregate_row_number for row in rows) != tuple(
        _count(index) for index in range(1, len(rows) + 1)
    ):
        raise ValueError("aggregate_row_number values must be sequential")
    if report.average_route_score != _average(tuple(row.route_score for row in rows)):
        raise ValueError("average_route_score must match rows")
    if report.lowest_route_score != min((row.route_score for row in rows), default=ZERO):
        raise ValueError("lowest_route_score must match rows")
    if report.highest_conflict_score != max(
        (row.conflict_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("highest_conflict_score must match rows")


def _set_or_validate_digest(obj: object, label: str) -> None:
    expected = _object_digest(obj)
    current = getattr(obj, "derived_validation_digest")
    if current == "":
        object.__setattr__(obj, "derived_validation_digest", expected)
        return
    _require_public_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError(f"{label} derived_validation_digest does not match payload")


def _object_digest(obj: object) -> str:
    if type(obj) is ResearchStrategyMemorySourceConfidenceRouterReport:
        payload = _report_payload(obj, include_digest=False)
    else:
        payload = _json_ready(asdict(obj))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        payload.pop("derived_validation_digest", None)
        _reject_unsafe_public_payload("payload", payload)
    return _digest_payload(payload)


def _report_payload(
    report: ResearchStrategyMemorySourceConfidenceRouterReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    if not include_digest:
        payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("report.payload", payload)
    return payload


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {value!r}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.{key}", key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is not str:
        return
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload value")


def _private_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _require_exact_type(obj: object, cls: type[object], label: str) -> None:
    if type(obj) is not cls:
        raise ValueError(f"{label} must be exactly {cls.__name__}")


def _require_public_id(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    return value


def _require_private_route_ref(name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_private_digest(name: str, value: object) -> str:
    if type(value) is not str or not PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_public_digest(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_reason_code(
    name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{name} must be a supported reason code")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{name} must be one of pass/watch/block")
    return value


def _normalize_reason_codes(
    name: str,
    values: object,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    if not values and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    for value in values:
        reason_code = _require_reason_code(name, value, allowed_values)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _dedupe_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if value not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a nonnegative whole Decimal")
    return normalized


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must not be below {watch_name}")


def _require_ceiling_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_name} must not exceed {watch_name}")


def _require_weight_sum(
    config: ResearchStrategyMemorySourceConfidenceRouterConfig,
) -> None:
    total = _quantize(
        config.memory_confidence_weight
        + config.source_confidence_weight
        + config.trace_confidence_weight
        + config.freshness_weight,
    )
    if total != ONE:
        raise ValueError("confidence weights must sum to 1")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _status_sort_key(status: object) -> Decimal:
    if status == STATUS_BLOCK:
        return ZERO
    if status == STATUS_WATCH:
        return Decimal("1.000000")
    return Decimal("2.000000")
