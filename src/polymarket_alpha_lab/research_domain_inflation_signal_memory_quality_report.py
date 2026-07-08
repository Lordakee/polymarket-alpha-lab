"""Public-safe inflation signal memory quality report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-inflation-signal-memory-quality-report-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = 86400
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PAPER_ACTION_BY_STATUS = {
    "pass": "paper_inflation_signal_memory_quality_pass",
    "watch": "paper_inflation_signal_memory_quality_watch",
    "block": "paper_inflation_signal_memory_quality_block",
}
SUPPORTED_INFLATION_INPUT_FAMILIES = (
    "cpi",
    "pce",
    "wages",
    "survey",
    "release-calendar",
)
PASS_ROW_REASON_CODE = "inflation_signal_memory_quality_pass"
WATCH_ROW_REASON_CODE = "inflation_signal_memory_quality_watch"
BLOCK_ROW_REASON_CODE = "inflation_signal_memory_quality_block"
EMPTY_REPORT_REASON_CODE = "inflation_signal_memory_quality_no_inputs"
QUEUE_CLEAR_REASON_CODE = "inflation_signal_memory_quality_queue_clear"
QUEUE_WATCH_REASON_CODE = "inflation_signal_memory_quality_queue_watch"
QUEUE_BLOCK_REASON_CODE = "inflation_signal_memory_quality_queue_block"
BLOCK_REASON_CODES = (
    "inflation_memory_freshness_below_watch",
    "inflation_memory_age_above_watch",
    "inflation_memory_conflict_above_watch",
    "inflation_memory_required_coverage_below_watch",
)
WATCH_REASON_CODES = (
    "inflation_memory_freshness_below_pass",
    "inflation_memory_age_above_pass",
    "inflation_memory_conflict_above_pass",
    "inflation_memory_required_coverage_below_pass",
)
MISSING_REASON_CODE = "inflation_memory_required_inputs_missing"
ROW_REASON_CODES = (
    PASS_ROW_REASON_CODE,
    WATCH_ROW_REASON_CODE,
    BLOCK_ROW_REASON_CODE,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
    MISSING_REASON_CODE,
)
REPORT_REASON_PRIORITY = (
    BLOCK_ROW_REASON_CODE,
    WATCH_ROW_REASON_CODE,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
    MISSING_REASON_CODE,
)
HEX_CHARS = frozenset("0123456789abcdef")


def _join(left: str, right: str) -> str:
    return left + right


UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "candidate",
        "event_id",
        "market_id",
        "market_slug",
        "question",
        "slug",
        "url",
        "http://",
        "https://",
        "source_text",
        "dsn",
        "table",
        "token",
        _join("wal", "let"),
        _join("au", "th"),
        _join("or", "der"),
        _join("tra", "de"),
        _join("li", "ve execution"),
        _join("recom", "mend"),
        _join("siz", "ing"),
        "allocation",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_STATUSES",
    "ResearchDomainInflationSignalMemoryInput",
    "ResearchDomainInflationSignalMemoryQualityConfig",
    "ResearchDomainInflationSignalMemoryQualityReasonCodeCount",
    "ResearchDomainInflationSignalMemoryQualityReport",
    "ResearchDomainInflationSignalMemoryQualityRow",
    "build_research_domain_inflation_signal_memory_quality_report",
    "research_domain_inflation_signal_memory_quality_report_digest",
    "research_domain_inflation_signal_memory_quality_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchDomainInflationSignalMemoryQualityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    max_pass_memory_age_seconds: Decimal = Decimal("43200")
    max_watch_memory_age_seconds: Decimal = Decimal("172800")
    min_pass_freshness_ratio: Decimal = Decimal("0.750000")
    min_watch_freshness_ratio: Decimal = Decimal("0.500000")
    max_pass_conflict_ratio: Decimal = Decimal("0.100000")
    max_watch_conflict_ratio: Decimal = Decimal("0.250000")
    min_pass_required_coverage_ratio: Decimal = Decimal("1.000000")
    min_watch_required_coverage_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainInflationSignalMemoryQualityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_freshness_ratio",
            "min_watch_freshness_ratio",
            "max_pass_conflict_ratio",
            "max_watch_conflict_ratio",
            "min_pass_required_coverage_ratio",
            "min_watch_required_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainInflationSignalMemoryInput(_FinalPublicDataclass):
    inflation_input_family: str
    memory_lane: str
    memory_input_count: Decimal
    fresh_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    required_input_count: Decimal
    missing_required_input_count: Decimal
    latest_memory_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainInflationSignalMemoryInput, "input")
        _require_inflation_input_family(self.inflation_input_family)
        _require_safe_public_string("memory_lane", self.memory_lane)
        for field_name in (
            "memory_input_count",
            "fresh_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
            "required_input_count",
            "missing_required_input_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_memory_observed_at",
            _as_utc("latest_memory_observed_at", self.latest_memory_observed_at),
        )
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchDomainInflationSignalMemoryQualityRow(_FinalPublicDataclass):
    inflation_input_family: str
    memory_lane: str
    status: str
    memory_input_count: Decimal
    fresh_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    required_input_count: Decimal
    missing_required_input_count: Decimal
    freshness_ratio: Decimal
    conflict_ratio: Decimal
    required_coverage_ratio: Decimal
    memory_age_seconds: Decimal
    latest_memory_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainInflationSignalMemoryQualityRow,
            "row",
        )
        _require_inflation_input_family(self.inflation_input_family)
        _require_safe_public_string("memory_lane", self.memory_lane)
        _require_status("status", self.status)
        for field_name in (
            "memory_input_count",
            "fresh_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
            "required_input_count",
            "missing_required_input_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_ratio",
            "conflict_ratio",
            "required_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_memory_observed_at",
            _as_utc("latest_memory_observed_at", self.latest_memory_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainInflationSignalMemoryQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    memory_lane_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainInflationSignalMemoryQualityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "memory_lane_ratio",
            _require_ratio_decimal("memory_lane_ratio", self.memory_lane_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchDomainInflationSignalMemoryQualityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    memory_lane_count: Decimal
    memory_input_count: Decimal
    fresh_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    required_input_count: Decimal
    missing_required_input_count: Decimal
    overall_freshness_ratio: Decimal
    overall_conflict_ratio: Decimal
    overall_required_coverage_ratio: Decimal
    max_memory_age_seconds: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchDomainInflationSignalMemoryQualityReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchDomainInflationSignalMemoryQualityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainInflationSignalMemoryQualityReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "memory_lane_count",
            "memory_input_count",
            "fresh_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
            "required_input_count",
            "missing_required_input_count",
            "max_memory_age_seconds",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "overall_freshness_ratio",
            "overall_conflict_ratio",
            "overall_required_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)


def build_research_domain_inflation_signal_memory_quality_report(
    memory_items: Iterable[ResearchDomainInflationSignalMemoryInput],
    *,
    config: ResearchDomainInflationSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainInflationSignalMemoryQualityReport:
    if type(config) is not ResearchDomainInflationSignalMemoryQualityConfig:
        raise ValueError("config must be a ResearchDomainInflationSignalMemoryQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_items)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.status for row in rows))
    memory_input_count = _sum_decimal(tuple(row.memory_input_count for row in rows))
    fresh_memory_input_count = _sum_decimal(
        tuple(row.fresh_memory_input_count for row in rows),
    )
    required_input_count = _sum_decimal(tuple(row.required_input_count for row in rows))
    missing_required_input_count = _sum_decimal(
        tuple(row.missing_required_input_count for row in rows),
    )
    return ResearchDomainInflationSignalMemoryQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        memory_lane_count=_count(len(rows)),
        memory_input_count=memory_input_count,
        fresh_memory_input_count=fresh_memory_input_count,
        stale_memory_input_count=_sum_decimal(
            tuple(row.stale_memory_input_count for row in rows),
        ),
        conflicting_memory_input_count=_sum_decimal(
            tuple(row.conflicting_memory_input_count for row in rows),
        ),
        required_input_count=required_input_count,
        missing_required_input_count=missing_required_input_count,
        overall_freshness_ratio=_ratio(fresh_memory_input_count, memory_input_count),
        overall_conflict_ratio=_ratio(
            _sum_decimal(tuple(row.conflicting_memory_input_count for row in rows)),
            memory_input_count,
        ),
        overall_required_coverage_ratio=_required_coverage_ratio(
            required_input_count,
            missing_required_input_count,
        ),
        max_memory_age_seconds=_max_decimal(
            tuple(row.memory_age_seconds for row in rows),
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_domain_inflation_signal_memory_quality_report_payload(
    report: ResearchDomainInflationSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainInflationSignalMemoryQualityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchDomainInflationSignalMemoryQualityReport")


def research_domain_inflation_signal_memory_quality_report_digest(
    report: ResearchDomainInflationSignalMemoryQualityReport,
) -> str:
    if type(report) is not ResearchDomainInflationSignalMemoryQualityReport:
        raise ValueError("report must be a ResearchDomainInflationSignalMemoryQualityReport")
    return _derived_validation_digest(report)


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


def _normalize_inputs(
    memory_items: Iterable[ResearchDomainInflationSignalMemoryInput],
) -> tuple[ResearchDomainInflationSignalMemoryInput, ...]:
    if isinstance(memory_items, (str, bytes)):
        raise ValueError("memory_items must be an iterable")
    try:
        items = tuple(memory_items)
    except TypeError as exc:
        raise ValueError("memory_items must be an iterable") from exc
    seen_lanes: set[str] = set()
    for item in items:
        if type(item) is not ResearchDomainInflationSignalMemoryInput:
            raise ValueError(
                "memory_items must contain ResearchDomainInflationSignalMemoryInput",
            )
        _require_hard_flags("input", item)
        if item.memory_lane in seen_lanes:
            raise ValueError("memory_lane values must be unique")
        seen_lanes.add(item.memory_lane)
    return items


def _row_from_input(
    item: ResearchDomainInflationSignalMemoryInput,
    *,
    config: ResearchDomainInflationSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainInflationSignalMemoryQualityRow:
    if item.latest_memory_observed_at > generated_at:
        raise ValueError("latest_memory_observed_at must not be in the future")
    memory_age_seconds = _memory_age_seconds(
        generated_at,
        item.latest_memory_observed_at,
    )
    freshness_ratio = _ratio(item.fresh_memory_input_count, item.memory_input_count)
    conflict_ratio = _ratio(
        item.conflicting_memory_input_count,
        item.memory_input_count,
    )
    required_coverage_ratio = _required_coverage_ratio(
        item.required_input_count,
        item.missing_required_input_count,
    )
    fresh_required_coverage_ratio = _fresh_required_coverage_ratio(item)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        memory_age_seconds=memory_age_seconds,
        freshness_ratio=freshness_ratio,
        conflict_ratio=conflict_ratio,
        fresh_required_coverage_ratio=fresh_required_coverage_ratio,
    )
    return ResearchDomainInflationSignalMemoryQualityRow(
        inflation_input_family=item.inflation_input_family,
        memory_lane=item.memory_lane,
        status=_row_status(reason_codes),
        memory_input_count=item.memory_input_count,
        fresh_memory_input_count=item.fresh_memory_input_count,
        stale_memory_input_count=item.stale_memory_input_count,
        conflicting_memory_input_count=item.conflicting_memory_input_count,
        required_input_count=item.required_input_count,
        missing_required_input_count=item.missing_required_input_count,
        freshness_ratio=freshness_ratio,
        conflict_ratio=conflict_ratio,
        required_coverage_ratio=required_coverage_ratio,
        memory_age_seconds=memory_age_seconds,
        latest_memory_observed_at=item.latest_memory_observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchDomainInflationSignalMemoryInput,
    *,
    config: ResearchDomainInflationSignalMemoryQualityConfig,
    memory_age_seconds: Decimal,
    freshness_ratio: Decimal,
    conflict_ratio: Decimal,
    fresh_required_coverage_ratio: Decimal,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if freshness_ratio < config.min_watch_freshness_ratio:
        block_reasons.append("inflation_memory_freshness_below_watch")
    elif freshness_ratio < config.min_pass_freshness_ratio:
        watch_reasons.append("inflation_memory_freshness_below_pass")

    if memory_age_seconds > config.max_watch_memory_age_seconds:
        block_reasons.append("inflation_memory_age_above_watch")
    elif memory_age_seconds > config.max_pass_memory_age_seconds:
        watch_reasons.append("inflation_memory_age_above_pass")

    if conflict_ratio > config.max_watch_conflict_ratio:
        block_reasons.append("inflation_memory_conflict_above_watch")
    elif conflict_ratio > config.max_pass_conflict_ratio:
        watch_reasons.append("inflation_memory_conflict_above_pass")

    if fresh_required_coverage_ratio < config.min_watch_required_coverage_ratio:
        block_reasons.append("inflation_memory_required_coverage_below_watch")
    elif fresh_required_coverage_ratio < config.min_pass_required_coverage_ratio:
        watch_reasons.append("inflation_memory_required_coverage_below_pass")

    if block_reasons:
        reason_codes = [BLOCK_ROW_REASON_CODE, *block_reasons]
    elif watch_reasons:
        reason_codes = [WATCH_ROW_REASON_CODE, *watch_reasons]
    else:
        reason_codes = [PASS_ROW_REASON_CODE]
    if item.missing_required_input_count > ZERO_COUNT and reason_codes[0] != PASS_ROW_REASON_CODE:
        reason_codes.append(MISSING_REASON_CODE)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes and reason_codes[0] == BLOCK_ROW_REASON_CODE:
        return "block"
    if reason_codes and reason_codes[0] == WATCH_ROW_REASON_CODE:
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainInflationSignalMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [
        {
            "pass": QUEUE_CLEAR_REASON_CODE,
            "watch": QUEUE_WATCH_REASON_CODE,
            "block": QUEUE_BLOCK_REASON_CODE,
        }[status],
    ]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchDomainInflationSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainInflationSignalMemoryQualityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(
            (
                PASS_ROW_REASON_CODE,
                WATCH_ROW_REASON_CODE,
                BLOCK_ROW_REASON_CODE,
                *WATCH_REASON_CODES,
                *BLOCK_REASON_CODES,
                MISSING_REASON_CODE,
            ),
        )
    }
    return tuple(
        ResearchDomainInflationSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=count,
            memory_lane_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchDomainInflationSignalMemoryQualityRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -_row_severity_score(row),
        row.inflation_input_family,
        row.memory_lane,
    )


def _row_severity_score(row: ResearchDomainInflationSignalMemoryQualityRow) -> Decimal:
    severity = STATUS_WEIGHT[row.status]
    severity += ONE_RATIO - row.freshness_ratio
    severity += row.conflict_ratio
    severity += ONE_RATIO - row.required_coverage_ratio
    return severity


def _status_count(
    rows: tuple[ResearchDomainInflationSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_config(
    config: ResearchDomainInflationSignalMemoryQualityConfig,
) -> None:
    if config.max_pass_memory_age_seconds > config.max_watch_memory_age_seconds:
        raise ValueError(
            "max_pass_memory_age_seconds must not exceed "
            "max_watch_memory_age_seconds",
        )
    if config.min_watch_freshness_ratio > config.min_pass_freshness_ratio:
        raise ValueError(
            "min_watch_freshness_ratio must not exceed min_pass_freshness_ratio",
        )
    if config.max_pass_conflict_ratio > config.max_watch_conflict_ratio:
        raise ValueError(
            "max_pass_conflict_ratio must not exceed max_watch_conflict_ratio",
        )
    if (
        config.min_watch_required_coverage_ratio
        > config.min_pass_required_coverage_ratio
    ):
        raise ValueError(
            "min_watch_required_coverage_ratio must not exceed "
            "min_pass_required_coverage_ratio",
        )


def _validate_input(item: ResearchDomainInflationSignalMemoryInput) -> None:
    if (
        item.fresh_memory_input_count + item.stale_memory_input_count
        != item.memory_input_count
    ):
        raise ValueError("fresh and stale memory input counts must sum to memory_input_count")
    if item.conflicting_memory_input_count > item.memory_input_count:
        raise ValueError("conflicting_memory_input_count must not exceed memory_input_count")
    if item.missing_required_input_count > item.required_input_count:
        raise ValueError("missing_required_input_count must not exceed required_input_count")


def _validate_row(row: ResearchDomainInflationSignalMemoryQualityRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_ROW_REASON_CODE,):
        raise ValueError("pass rows require inflation_signal_memory_quality_pass")
    if row.status != "pass" and PASS_ROW_REASON_CODE in row.reason_codes:
        raise ValueError("watch and block rows must not contain pass reason_codes")


def _validate_report_materialized_fields(
    report: ResearchDomainInflationSignalMemoryQualityReport,
) -> None:
    rows = report.rows
    memory_input_count = _sum_decimal(tuple(row.memory_input_count for row in rows))
    fresh_memory_input_count = _sum_decimal(
        tuple(row.fresh_memory_input_count for row in rows),
    )
    conflicting_memory_input_count = _sum_decimal(
        tuple(row.conflicting_memory_input_count for row in rows),
    )
    required_input_count = _sum_decimal(tuple(row.required_input_count for row in rows))
    missing_required_input_count = _sum_decimal(
        tuple(row.missing_required_input_count for row in rows),
    )
    checks = {
        "memory_lane_count": _count(len(rows)),
        "memory_input_count": memory_input_count,
        "fresh_memory_input_count": fresh_memory_input_count,
        "stale_memory_input_count": _sum_decimal(
            tuple(row.stale_memory_input_count for row in rows),
        ),
        "conflicting_memory_input_count": conflicting_memory_input_count,
        "required_input_count": required_input_count,
        "missing_required_input_count": missing_required_input_count,
        "overall_freshness_ratio": _ratio(
            fresh_memory_input_count,
            memory_input_count,
        ),
        "overall_conflict_ratio": _ratio(
            conflicting_memory_input_count,
            memory_input_count,
        ),
        "overall_required_coverage_ratio": _required_coverage_ratio(
            required_input_count,
            missing_required_input_count,
        ),
        "max_memory_age_seconds": _max_decimal(
            tuple(row.memory_age_seconds for row in rows),
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_status = _rollup_status(tuple(row.status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchDomainInflationSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainInflationSignalMemoryQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_lanes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchDomainInflationSignalMemoryQualityRow:
            raise ValueError(
                "rows must contain ResearchDomainInflationSignalMemoryQualityRow",
            )
        _require_hard_flags("row", row)
        if row.memory_lane in seen_lanes:
            raise ValueError("rows must contain unique memory_lane values")
        seen_lanes.add(row.memory_lane)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and memory quality")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchDomainInflationSignalMemoryQualityReasonCodeCount, ...],
) -> tuple[ResearchDomainInflationSignalMemoryQualityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchDomainInflationSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainInflationSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_safe_public_string(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_inflation_input_family(value: str) -> str:
    _require_safe_public_string("inflation_input_family", value)
    if value not in SUPPORTED_INFLATION_INPUT_FAMILIES:
        raise ValueError("inflation_input_family must be a supported inflation family")
    return value


def _require_status(field_name: str, value: str) -> str:
    _require_public_string(field_name, value)
    if value not in RESEARCH_DOMAIN_INFLATION_SIGNAL_MEMORY_QUALITY_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _require_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(value, require_nonempty=True)
    allowed_report_codes = (
        QUEUE_CLEAR_REASON_CODE,
        QUEUE_WATCH_REASON_CODE,
        QUEUE_BLOCK_REASON_CODE,
        EMPTY_REPORT_REASON_CODE,
    )
    for reason_code in normalized:
        if reason_code in ROW_REASON_CODES or reason_code in allowed_report_codes:
            continue
        raise ValueError("reason_codes contains unknown reason_code")
    return normalized


def _require_reason_codes(
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    if len(frozenset(value)) != len(value):
        raise ValueError("reason_codes values must be unique")
    allowed_report_codes = (
        QUEUE_CLEAR_REASON_CODE,
        QUEUE_WATCH_REASON_CODE,
        QUEUE_BLOCK_REASON_CODE,
        EMPTY_REPORT_REASON_CODE,
    )
    for item in value:
        _require_public_string("reason_code", item)
        if item not in ROW_REASON_CODES and item not in allowed_report_codes:
            raise ValueError("reason_codes contains unknown reason_code")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, ZERO_COUNT).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _required_coverage_ratio(
    required_input_count: Decimal,
    missing_required_input_count: Decimal,
) -> Decimal:
    if required_input_count == ZERO_COUNT:
        return ZERO_RATIO
    covered_count = required_input_count - missing_required_input_count
    return _ratio(covered_count, required_input_count)


def _fresh_required_coverage_ratio(
    item: ResearchDomainInflationSignalMemoryInput,
) -> Decimal:
    if item.required_input_count == ZERO_COUNT:
        return ONE_RATIO
    fresh_required_count = min(item.fresh_memory_input_count, item.required_input_count)
    return _ratio(fresh_required_count, item.required_input_count)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_COUNT
    return max(values)


def _memory_age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return Decimal(delta.days * SECONDS_PER_DAY + delta.seconds).quantize(COUNT_QUANTUM)


def _derived_validation_digest(
    report: ResearchDomainInflationSignalMemoryQualityReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"public payload contains unsupported value {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be serialized strings")
    if type(value) is datetime:
        raise ValueError("public payload datetime values must be serialized strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(f"{label}.key", str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_sha256(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value
