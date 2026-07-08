"""Pure public source-class triage priority report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ResearchSourceTriageScrapingPriorityConfig",
    "ResearchSourceTriageScrapingPriorityInput",
    "ResearchSourceTriageScrapingPriorityReasonCodeCount",
    "ResearchSourceTriageScrapingPriorityReport",
    "ResearchSourceTriageScrapingPriorityRow",
    "build_research_source_triage_scraping_priority_report",
    "research_source_triage_scraping_priority_report_digest",
    "research_source_triage_scraping_priority_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-triage-scraping-priority-report-v0"
STATUSES = ("pass", "watch", "block")
COLLECTION_MODES = ("scrape", "manual_check", "defer")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "http:",
    "https:",
    "www.",
    "url",
    "raw_",
    "raw-",
    "raw text",
    "rawtext",
    "source_ref",
    "source ref",
    "source_reference",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchSourceTriageScrapingPriorityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_source_age_seconds: Decimal = Decimal("3600")
    stale_source_age_seconds: Decimal = Decimal("86400")
    pass_priority_threshold: Decimal = Decimal("0.600000")
    watch_priority_threshold: Decimal = Decimal("0.300000")
    reliability_block_floor: Decimal = Decimal("0.250000")
    reliability_watch_floor: Decimal = Decimal("0.500000")
    manual_check_contradiction_threshold: Decimal = Decimal("0.600000")
    freshness_weight: Decimal = Decimal("0.250000")
    reliability_weight: Decimal = Decimal("0.200000")
    catalyst_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.200000")
    coverage_gap_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceTriageScrapingPriorityConfig, "config")
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("fresh_source_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_age_seconds <= self.fresh_source_age_seconds:
            raise ValueError(
                "stale_source_age_seconds must exceed fresh_source_age_seconds",
            )
        for field_name in (
            "pass_priority_threshold",
            "watch_priority_threshold",
            "reliability_block_floor",
            "reliability_watch_floor",
            "manual_check_contradiction_threshold",
            "freshness_weight",
            "reliability_weight",
            "catalyst_weight",
            "contradiction_weight",
            "coverage_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_priority_threshold <= self.watch_priority_threshold:
            raise ValueError("pass_priority_threshold must exceed watch_priority_threshold")
        if self.reliability_watch_floor <= self.reliability_block_floor:
            raise ValueError("reliability_watch_floor must exceed reliability_block_floor")
        component_weight_sum = _quantize(
            self.freshness_weight
            + self.reliability_weight
            + self.catalyst_weight
            + self.contradiction_weight
            + self.coverage_gap_weight,
        )
        if component_weight_sum != ONE:
            raise ValueError(
                "freshness_weight, reliability_weight, catalyst_weight, "
                "contradiction_weight, and coverage_gap_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceTriageScrapingPriorityInput:
    source_class_id: str
    latest_source_age_seconds: Decimal
    reliability_memory_score: Decimal
    catalyst_pressure_score: Decimal
    contradiction_score: Decimal
    coverage_gap_score: Decimal
    public_item_count: Decimal
    required_item_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceTriageScrapingPriorityInput, "input")
        _require_canonical_public_string("source_class_id", self.source_class_id)
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "reliability_memory_score",
            "catalyst_pressure_score",
            "contradiction_score",
            "coverage_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_item_count",
            _require_nonnegative_whole_decimal(
                "public_item_count",
                self.public_item_count,
            ),
        )
        object.__setattr__(
            self,
            "required_item_count",
            _require_positive_whole_decimal(
                "required_item_count",
                self.required_item_count,
            ),
        )
        if self.public_item_count > self.required_item_count:
            raise ValueError("required_item_count must cover public_item_count")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceTriageScrapingPriorityRow:
    source_class_id: str
    priority_rank: Decimal
    latest_source_age_seconds: Decimal
    freshness_pressure_score: Decimal
    reliability_memory_score: Decimal
    catalyst_pressure_score: Decimal
    contradiction_score: Decimal
    coverage_gap_score: Decimal
    public_item_count: Decimal
    required_item_count: Decimal
    observed_coverage_ratio: Decimal
    priority_score: Decimal
    status: str
    collection_mode: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceTriageScrapingPriorityRow, "row")
        _require_canonical_public_string("source_class_id", self.source_class_id)
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_whole_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _require_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "freshness_pressure_score",
            "reliability_memory_score",
            "catalyst_pressure_score",
            "contradiction_score",
            "coverage_gap_score",
            "observed_coverage_ratio",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_item_count",
            _require_nonnegative_whole_decimal(
                "public_item_count",
                self.public_item_count,
            ),
        )
        object.__setattr__(
            self,
            "required_item_count",
            _require_positive_whole_decimal(
                "required_item_count",
                self.required_item_count,
            ),
        )
        _require_enum("status", self.status, STATUSES)
        _require_enum("collection_mode", self.collection_mode, COLLECTION_MODES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceTriageScrapingPriorityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceTriageScrapingPriorityReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceTriageScrapingPriorityReport:
    generated_at: datetime
    config_version: str
    source_class_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    scrape_count: Decimal
    manual_check_count: Decimal
    average_priority_score: Decimal | None
    status: str
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...]
    reason_code_counts: tuple[ResearchSourceTriageScrapingPriorityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceTriageScrapingPriorityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "source_class_count",
            "pass_count",
            "watch_count",
            "block_count",
            "scrape_count",
            "manual_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_priority_score",
            _require_optional_probability_decimal(
                "average_priority_score",
                self.average_priority_score,
            ),
        )
        _require_enum("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_source_triage_scraping_priority_report(
    inputs: Iterable[object],
    *,
    config: ResearchSourceTriageScrapingPriorityConfig,
    generated_at: datetime,
) -> ResearchSourceTriageScrapingPriorityReport:
    if type(config) is not ResearchSourceTriageScrapingPriorityConfig:
        raise ValueError("config must be a ResearchSourceTriageScrapingPriorityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    ranked_rows = _rank_rows(
        tuple(_unranked_row_from_input(input_row, config=config) for input_row in input_rows),
    )
    reason_codes = _summary_reason_codes(ranked_rows)
    return ResearchSourceTriageScrapingPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_class_count=_decimal_count(len(ranked_rows)),
        pass_count=_decimal_count(_status_count(ranked_rows, "pass")),
        watch_count=_decimal_count(_status_count(ranked_rows, "watch")),
        block_count=_decimal_count(_status_count(ranked_rows, "block")),
        scrape_count=_decimal_count(_mode_count(ranked_rows, "scrape")),
        manual_check_count=_decimal_count(_mode_count(ranked_rows, "manual_check")),
        average_priority_score=_average_priority_score(ranked_rows),
        status=_summary_status(ranked_rows),
        rows=ranked_rows,
        reason_code_counts=_reason_code_counts(ranked_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_source_triage_scraping_priority_report_payload(
    report: ResearchSourceTriageScrapingPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceTriageScrapingPriorityReport:
        raise ValueError("report must be a ResearchSourceTriageScrapingPriorityReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def research_source_triage_scraping_priority_report_digest(
    report: ResearchSourceTriageScrapingPriorityReport,
) -> str:
    payload = research_source_triage_scraping_priority_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _unranked_row_from_input(
    input_row: ResearchSourceTriageScrapingPriorityInput,
    *,
    config: ResearchSourceTriageScrapingPriorityConfig,
) -> ResearchSourceTriageScrapingPriorityRow:
    freshness_pressure_score = _freshness_pressure_score(
        input_row.latest_source_age_seconds,
        config=config,
    )
    observed_coverage_ratio = _quantize(
        input_row.public_item_count / input_row.required_item_count,
    )
    priority_score = _priority_score(
        freshness_pressure_score=freshness_pressure_score,
        reliability_memory_score=input_row.reliability_memory_score,
        catalyst_pressure_score=input_row.catalyst_pressure_score,
        contradiction_score=input_row.contradiction_score,
        coverage_gap_score=input_row.coverage_gap_score,
        config=config,
    )
    status = _row_status(
        priority_score=priority_score,
        reliability_memory_score=input_row.reliability_memory_score,
        config=config,
    )
    collection_mode = _collection_mode(
        status=status,
        priority_score=priority_score,
        contradiction_score=input_row.contradiction_score,
        config=config,
    )
    return ResearchSourceTriageScrapingPriorityRow(
        source_class_id=input_row.source_class_id,
        priority_rank=ONE,
        latest_source_age_seconds=input_row.latest_source_age_seconds,
        freshness_pressure_score=freshness_pressure_score,
        reliability_memory_score=input_row.reliability_memory_score,
        catalyst_pressure_score=input_row.catalyst_pressure_score,
        contradiction_score=input_row.contradiction_score,
        coverage_gap_score=input_row.coverage_gap_score,
        public_item_count=input_row.public_item_count,
        required_item_count=input_row.required_item_count,
        observed_coverage_ratio=observed_coverage_ratio,
        priority_score=priority_score,
        status=status,
        collection_mode=collection_mode,
        reason_codes=_row_reason_codes(
            input_row=input_row,
            freshness_pressure_score=freshness_pressure_score,
            priority_score=priority_score,
            status=status,
            collection_mode=collection_mode,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
) -> tuple[ResearchSourceTriageScrapingPriorityRow, ...]:
    _reject_duplicate_source_classes(rows)
    ranked = sorted(
        rows,
        key=lambda row: (
            -row.priority_score,
            row.status,
            row.source_class_id,
        ),
    )
    return tuple(
        ResearchSourceTriageScrapingPriorityRow(
            source_class_id=row.source_class_id,
            priority_rank=_decimal_count(index + 1),
            latest_source_age_seconds=row.latest_source_age_seconds,
            freshness_pressure_score=row.freshness_pressure_score,
            reliability_memory_score=row.reliability_memory_score,
            catalyst_pressure_score=row.catalyst_pressure_score,
            contradiction_score=row.contradiction_score,
            coverage_gap_score=row.coverage_gap_score,
            public_item_count=row.public_item_count,
            required_item_count=row.required_item_count,
            observed_coverage_ratio=row.observed_coverage_ratio,
            priority_score=row.priority_score,
            status=row.status,
            collection_mode=row.collection_mode,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(ranked)
    )


def _freshness_pressure_score(
    latest_source_age_seconds: Decimal,
    *,
    config: ResearchSourceTriageScrapingPriorityConfig,
) -> Decimal:
    if latest_source_age_seconds <= config.fresh_source_age_seconds:
        return ZERO
    if latest_source_age_seconds >= config.stale_source_age_seconds:
        return ONE
    return _quantize(latest_source_age_seconds / config.stale_source_age_seconds)


def _priority_score(
    *,
    freshness_pressure_score: Decimal,
    reliability_memory_score: Decimal,
    catalyst_pressure_score: Decimal,
    contradiction_score: Decimal,
    coverage_gap_score: Decimal,
    config: ResearchSourceTriageScrapingPriorityConfig,
) -> Decimal:
    return _quantize(
        (freshness_pressure_score * config.freshness_weight)
        + (reliability_memory_score * config.reliability_weight)
        + (catalyst_pressure_score * config.catalyst_weight)
        + (contradiction_score * config.contradiction_weight)
        + (coverage_gap_score * config.coverage_gap_weight),
    )


def _row_status(
    *,
    priority_score: Decimal,
    reliability_memory_score: Decimal,
    config: ResearchSourceTriageScrapingPriorityConfig,
) -> str:
    if reliability_memory_score < config.reliability_block_floor:
        return "block"
    if priority_score >= config.pass_priority_threshold:
        return "pass"
    return "watch"


def _collection_mode(
    *,
    status: str,
    priority_score: Decimal,
    contradiction_score: Decimal,
    config: ResearchSourceTriageScrapingPriorityConfig,
) -> str:
    if status == "block":
        return "defer"
    if contradiction_score >= config.manual_check_contradiction_threshold:
        return "manual_check"
    if priority_score >= config.pass_priority_threshold:
        return "scrape"
    return "manual_check"


def _row_reason_codes(
    *,
    input_row: ResearchSourceTriageScrapingPriorityInput,
    freshness_pressure_score: Decimal,
    priority_score: Decimal,
    status: str,
    collection_mode: str,
    config: ResearchSourceTriageScrapingPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {
        f"public_collection_{collection_mode}",
        f"research_source_triage_priority_{status}",
    }
    if freshness_pressure_score == ONE:
        reason_codes.add("freshness_gap_pressure")
    if input_row.coverage_gap_score >= Decimal("0.500000"):
        reason_codes.add("coverage_gap_pressure")
    if input_row.contradiction_score >= config.manual_check_contradiction_threshold:
        reason_codes.add("contradiction_pressure")
    if collection_mode == "manual_check" and (
        input_row.contradiction_score >= config.manual_check_contradiction_threshold
    ):
        reason_codes.add("manual_check_contradiction")
    if input_row.reliability_memory_score < config.reliability_block_floor:
        reason_codes.add("reliability_memory_below_block_floor")
    elif input_row.reliability_memory_score < config.reliability_watch_floor:
        reason_codes.add("reliability_memory_watch")
    if status == "watch" and priority_score < config.watch_priority_threshold:
        reason_codes.add("low_priority_watch")
    for reason_code in input_row.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchSourceTriageScrapingPriorityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchSourceTriageScrapingPriorityInput:
    if type(value) is ResearchSourceTriageScrapingPriorityInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchSourceTriageScrapingPriorityInput(
        source_class_id=_field_value(value, "source_class_id"),
        latest_source_age_seconds=_field_value(value, "latest_source_age_seconds"),
        reliability_memory_score=_field_value(value, "reliability_memory_score"),
        catalyst_pressure_score=_field_value(value, "catalyst_pressure_score"),
        contradiction_score=_field_value(value, "contradiction_score"),
        coverage_gap_score=_field_value(value, "coverage_gap_score"),
        public_item_count=_field_value(value, "public_item_count"),
        required_item_count=_field_value(value, "required_item_count"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _reject_duplicate_source_classes(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.source_class_id in seen:
            raise ValueError("source_class_id values must be unique")
        seen.add(row.source_class_id)


def _summary_reason_codes(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_public_source_classes",)
    if all(row.status == "pass" for row in rows):
        return ("research_source_triage_priority_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...]) -> str:
    if not rows:
        return "block"
    if all(row.status == "pass" for row in rows):
        return "pass"
    if all(row.status == "block" for row in rows):
        return "block"
    return "watch"


def _reason_code_counts(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceTriageScrapingPriorityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceTriageScrapingPriorityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceTriageScrapingPriorityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_priority_score(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.priority_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _mode_count(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
    collection_mode: str,
) -> int:
    return sum(1 for row in rows if row.collection_mode == collection_mode)


def _normalize_rows(
    rows: tuple[ResearchSourceTriageScrapingPriorityRow, ...],
) -> tuple[ResearchSourceTriageScrapingPriorityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceTriageScrapingPriorityRow:
            raise ValueError(
                "rows must contain ResearchSourceTriageScrapingPriorityRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (row.priority_rank, -row.priority_score, row.source_class_id),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by priority_rank")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceTriageScrapingPriorityReasonCodeCount, ...],
) -> tuple[ResearchSourceTriageScrapingPriorityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSourceTriageScrapingPriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceTriageScrapingPriorityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchSourceTriageScrapingPriorityRow) -> None:
    if row.public_item_count > row.required_item_count:
        raise ValueError("public_item_count must not exceed required_item_count")
    if row.observed_coverage_ratio != _quantize(
        row.public_item_count / row.required_item_count,
    ):
        raise ValueError("observed_coverage_ratio must match item counts")
    if row.status == "pass" and row.priority_score < Decimal("0.600000"):
        raise ValueError("priority_score must support pass status")
    if row.status == "watch" and row.priority_score < Decimal("0.300000"):
        if "low_priority_watch" not in row.reason_codes:
            raise ValueError("priority_score must support watch status")
    if row.status == "block" and (
        "reliability_memory_below_block_floor" not in row.reason_codes
    ):
        raise ValueError("block status must have reliability reason")
    if row.collection_mode == "scrape" and row.status != "pass":
        raise ValueError("scrape rows must be pass status")
    if row.collection_mode == "defer" and row.status != "block":
        raise ValueError("defer rows must be block status")


def _validate_report_consistency(report: ResearchSourceTriageScrapingPriorityReport) -> None:
    if report.source_class_count != _decimal_count(len(report.rows)):
        raise ValueError("source_class_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.scrape_count != _decimal_count(_mode_count(report.rows, "scrape")):
        raise ValueError("scrape_count must match rows")
    if report.manual_check_count != _decimal_count(_mode_count(report.rows, "manual_check")):
        raise ValueError("manual_check_count must match rows")
    if report.average_priority_score != _average_priority_score(report.rows):
        raise ValueError("average_priority_score must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, float):
        raise ValueError("payload values must not be floats")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_string(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    _reject_unsafe_public_string(field_name, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe public surface text")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must use lower_snake_case reason codes")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")
