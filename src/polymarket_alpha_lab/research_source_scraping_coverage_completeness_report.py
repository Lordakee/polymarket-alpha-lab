"""Pure report-only scraping coverage completeness reducer.

Callers provide already-observed, sanitized collection telemetry. This module
performs no network or database access and returns a deterministic public report
with Decimal-only numerics and SHA-256 digest validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPING_COVERAGE_COMPLETENESS_REPORT_CONFIG_VERSION = (
    "research-source-scraping-coverage-completeness-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUSES = ("pass", "watch", "block")
TOOL_FAMILIES = ("primary_channel", "secondary_channel", "generic")
TOOL_FAMILY_SORT = {name: index for index, name in enumerate(TOOL_FAMILIES)}

NO_INPUTS_REASON = "scraping_coverage_completeness_no_inputs"
PASS_REASON = "scraping_coverage_completeness_pass"
WATCH_REASON = "scraping_coverage_completeness_watch"
BLOCK_REASON = "scraping_coverage_completeness_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "coverage_below_watch_threshold",
    "parse_confidence_below_watch_threshold",
    "critical_field_completeness_below_watch_threshold",
    "duplicate_corroboration_below_watch_threshold",
    "freshness_below_watch_threshold",
    "authority_below_watch_threshold",
    "completeness_score_below_watch_threshold",
    "coverage_below_target",
    "parse_confidence_below_pass_threshold",
    "critical_field_completeness_below_pass_threshold",
    "duplicate_corroboration_below_pass_threshold",
    "freshness_below_pass_threshold",
    "authority_below_pass_threshold",
    "completeness_score_below_pass_threshold",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in REASON_CODE_SEQUENCE
    if reason_code.endswith("_below_watch_threshold")
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "raw_text",
    "raw text",
    "url",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "scr" "apling",
    "agent" "_reach",
    "agent" " reach",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPING_COVERAGE_COMPLETENESS_REPORT_CONFIG_VERSION",
    "ResearchSourceScrapingCoverageCompletenessConfig",
    "ResearchSourceScrapingCoverageCompletenessInput",
    "ResearchSourceScrapingCoverageCompletenessReasonCodeCount",
    "ResearchSourceScrapingCoverageCompletenessReport",
    "ResearchSourceScrapingCoverageCompletenessRow",
    "STATUSES",
    "build_research_source_scraping_coverage_completeness_report",
    "research_source_scraping_coverage_completeness_report_digest",
    "research_source_scraping_coverage_completeness_report_payload",
    "validate_research_source_scraping_coverage_completeness_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScrapingCoverageCompletenessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPING_COVERAGE_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    min_coverage_pass_ratio: Decimal = Decimal("0.900000")
    min_coverage_watch_ratio: Decimal = Decimal("0.500000")
    min_parse_confidence_pass_ratio: Decimal = Decimal("0.800000")
    min_parse_confidence_watch_ratio: Decimal = Decimal("0.600000")
    min_critical_field_completeness_pass_ratio: Decimal = Decimal("0.900000")
    min_critical_field_completeness_watch_ratio: Decimal = Decimal("0.500000")
    min_duplicate_corroboration_pass_ratio: Decimal = Decimal("0.600000")
    min_duplicate_corroboration_watch_ratio: Decimal = Decimal("0.500000")
    fresh_collection_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_collection_block_age_seconds: Decimal = Decimal("86400.000000")
    min_freshness_pass_score: Decimal = Decimal("0.800000")
    min_freshness_watch_score: Decimal = Decimal("0.500000")
    min_authority_pass_score: Decimal = Decimal("0.800000")
    min_authority_watch_score: Decimal = Decimal("0.500000")
    min_completeness_pass_score: Decimal = Decimal("0.800000")
    min_completeness_watch_score: Decimal = Decimal("0.500000")
    target_coverage_weight: Decimal = Decimal("0.250000")
    parse_confidence_weight: Decimal = Decimal("0.200000")
    critical_field_weight: Decimal = Decimal("0.200000")
    duplicate_corroboration_weight: Decimal = Decimal("0.150000")
    freshness_weight: Decimal = Decimal("0.100000")
    authority_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingCoverageCompletenessConfig:
            raise TypeError(
                "ResearchSourceScrapingCoverageCompletenessConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScrapingCoverageCompletenessConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPING_COVERAGE_COMPLETENESS_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_collection_max_age_seconds",
            "stale_collection_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_collection_max_age_seconds >= self.stale_collection_block_age_seconds:
            raise ValueError(
                "fresh_collection_max_age_seconds must be below "
                "stale_collection_block_age_seconds",
            )
        for field_name in (
            "min_coverage_pass_ratio",
            "min_coverage_watch_ratio",
            "min_parse_confidence_pass_ratio",
            "min_parse_confidence_watch_ratio",
            "min_critical_field_completeness_pass_ratio",
            "min_critical_field_completeness_watch_ratio",
            "min_duplicate_corroboration_pass_ratio",
            "min_duplicate_corroboration_watch_ratio",
            "min_freshness_pass_score",
            "min_freshness_watch_score",
            "min_authority_pass_score",
            "min_authority_watch_score",
            "min_completeness_pass_score",
            "min_completeness_watch_score",
            "target_coverage_weight",
            "parse_confidence_weight",
            "critical_field_weight",
            "duplicate_corroboration_weight",
            "freshness_weight",
            "authority_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ordered_threshold(
            "coverage",
            self.min_coverage_watch_ratio,
            self.min_coverage_pass_ratio,
        )
        _require_ordered_threshold(
            "parse confidence",
            self.min_parse_confidence_watch_ratio,
            self.min_parse_confidence_pass_ratio,
        )
        _require_ordered_threshold(
            "critical field completeness",
            self.min_critical_field_completeness_watch_ratio,
            self.min_critical_field_completeness_pass_ratio,
        )
        _require_ordered_threshold(
            "duplicate corroboration",
            self.min_duplicate_corroboration_watch_ratio,
            self.min_duplicate_corroboration_pass_ratio,
        )
        _require_ordered_threshold(
            "freshness",
            self.min_freshness_watch_score,
            self.min_freshness_pass_score,
        )
        _require_ordered_threshold(
            "authority",
            self.min_authority_watch_score,
            self.min_authority_pass_score,
        )
        _require_ordered_threshold(
            "completeness score",
            self.min_completeness_watch_score,
            self.min_completeness_pass_score,
        )
        weight_sum = _quantize(
            self.target_coverage_weight
            + self.parse_confidence_weight
            + self.critical_field_weight
            + self.duplicate_corroboration_weight
            + self.freshness_weight
            + self.authority_weight,
        )
        if weight_sum != ONE:
            raise ValueError("completeness score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScrapingCoverageCompletenessInput:
    private_collection_ref: str
    tool_family: str
    collected_at: datetime
    target_source_count: Decimal
    covered_source_count: Decimal
    parse_confidence_ratio: Decimal
    critical_field_count: Decimal
    missing_critical_field_count: Decimal
    duplicate_corroboration_count: Decimal
    required_duplicate_corroboration_count: Decimal
    authority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingCoverageCompletenessInput:
            raise TypeError(
                "ResearchSourceScrapingCoverageCompletenessInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingCoverageCompletenessInput, "input")
        _require_private_string("private_collection_ref", self.private_collection_ref)
        _require_member("tool_family", self.tool_family, TOOL_FAMILIES)
        object.__setattr__(self, "collected_at", _as_utc("collected_at", self.collected_at))
        for field_name in (
            "covered_source_count",
            "missing_critical_field_count",
            "duplicate_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "target_source_count",
            "critical_field_count",
            "required_duplicate_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("parse_confidence_ratio", "authority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.covered_source_count > self.target_source_count:
            raise ValueError("covered_source_count must not exceed target_source_count")
        if self.missing_critical_field_count > self.critical_field_count:
            raise ValueError(
                "missing_critical_field_count must not exceed critical_field_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScrapingCoverageCompletenessRow:
    row_index: Decimal
    tool_family: str
    collection_age_seconds: Decimal
    target_source_count: Decimal
    covered_source_count: Decimal
    coverage_ratio: Decimal
    parse_confidence_ratio: Decimal
    critical_field_completeness_score: Decimal
    missing_critical_field_count: Decimal
    duplicate_corroboration_score: Decimal
    freshness_score: Decimal
    authority_score: Decimal
    completeness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingCoverageCompletenessRow:
            raise TypeError(
                "ResearchSourceScrapingCoverageCompletenessRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingCoverageCompletenessRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _normalize_positive_count("row_index", self.row_index),
        )
        _require_member("tool_family", self.tool_family, TOOL_FAMILIES)
        object.__setattr__(
            self,
            "collection_age_seconds",
            _normalize_nonnegative_decimal(
                "collection_age_seconds",
                self.collection_age_seconds,
            ),
        )
        for field_name in (
            "target_source_count",
            "covered_source_count",
            "missing_critical_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_ratio",
            "parse_confidence_ratio",
            "critical_field_completeness_score",
            "duplicate_corroboration_score",
            "freshness_score",
            "authority_score",
            "completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScrapingCoverageCompletenessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingCoverageCompletenessReasonCodeCount:
            raise TypeError(
                "ResearchSourceScrapingCoverageCompletenessReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScrapingCoverageCompletenessReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScrapingCoverageCompletenessReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    target_source_count: Decimal
    covered_source_count: Decimal
    missing_critical_field_count: Decimal
    aggregate_coverage_ratio: Decimal
    average_parse_confidence_ratio: Decimal
    average_critical_field_completeness_score: Decimal
    average_duplicate_corroboration_score: Decimal
    average_freshness_score: Decimal
    average_authority_score: Decimal
    average_completeness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScrapingCoverageCompletenessReasonCodeCount, ...]
    rows: tuple[ResearchSourceScrapingCoverageCompletenessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingCoverageCompletenessReport:
            raise TypeError(
                "ResearchSourceScrapingCoverageCompletenessReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingCoverageCompletenessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "target_source_count",
            "covered_source_count",
            "missing_critical_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_coverage_ratio",
            "average_parse_confidence_ratio",
            "average_critical_field_completeness_score",
            "average_duplicate_corroboration_score",
            "average_freshness_score",
            "average_authority_score",
            "average_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scraping_coverage_completeness_report_payload(self)


def build_research_source_scraping_coverage_completeness_report(
    inputs: Iterable[ResearchSourceScrapingCoverageCompletenessInput],
    *,
    config: ResearchSourceScrapingCoverageCompletenessConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingCoverageCompletenessReport:
    if type(config) is not ResearchSourceScrapingCoverageCompletenessConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScrapingCoverageCompletenessConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.collected_at > generated_at:
            raise ValueError("collected_at cannot be after generated_at")

    rows = tuple(
        _row_from_input(item, row_number=index, config=config, generated_at=generated_at)
        for index, item in enumerate(normalized_inputs, start=1)
    )
    input_count = _count_decimal(len(normalized_inputs))
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    target_source_count = _sum_decimal(row.target_source_count for row in rows)
    covered_source_count = _sum_decimal(row.covered_source_count for row in rows)

    return ResearchSourceScrapingCoverageCompletenessReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=watch_count + block_count,
        target_source_count=target_source_count,
        covered_source_count=covered_source_count,
        missing_critical_field_count=_sum_decimal(
            (row.missing_critical_field_count for row in rows),
        ),
        aggregate_coverage_ratio=_safe_ratio(covered_source_count, target_source_count),
        average_parse_confidence_ratio=_average(
            (row.parse_confidence_ratio for row in rows),
        ),
        average_critical_field_completeness_score=_average(
            (row.critical_field_completeness_score for row in rows),
        ),
        average_duplicate_corroboration_score=_average(
            (row.duplicate_corroboration_score for row in rows),
        ),
        average_freshness_score=_average(row.freshness_score for row in rows),
        average_authority_score=_average(row.authority_score for row in rows),
        average_completeness_score=_average(row.completeness_score for row in rows),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        rows=rows,
    )


def research_source_scraping_coverage_completeness_report_payload(
    report: ResearchSourceScrapingCoverageCompletenessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScrapingCoverageCompletenessReport:
        raise ValueError(
            "report must be exactly ResearchSourceScrapingCoverageCompletenessReport",
        )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scraping_coverage_completeness_report_digest(
    report: ResearchSourceScrapingCoverageCompletenessReport,
) -> str:
    payload = research_source_scraping_coverage_completeness_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scraping_coverage_completeness_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        _report_from_public_payload(payload)
        return True
    except (TypeError, ValueError):
        return False


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScrapingCoverageCompletenessInput],
) -> tuple[ResearchSourceScrapingCoverageCompletenessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScrapingCoverageCompletenessInput:
            raise ValueError(
                "inputs must contain ResearchSourceScrapingCoverageCompletenessInput",
            )
        _require_hard_flags("input", item)
    return tuple(sorted(normalized, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScrapingCoverageCompletenessInput,
) -> tuple[int, str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        TOOL_FAMILY_SORT[item.tool_family],
        item.collected_at.isoformat(),
        item.target_source_count,
        item.covered_source_count,
        item.parse_confidence_ratio,
        item.critical_field_count,
        item.missing_critical_field_count,
        item.duplicate_corroboration_count,
        item.required_duplicate_corroboration_count,
        item.authority_score,
    )


def _row_from_input(
    item: ResearchSourceScrapingCoverageCompletenessInput,
    *,
    row_number: int,
    config: ResearchSourceScrapingCoverageCompletenessConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingCoverageCompletenessRow:
    collection_age_seconds = _duration_seconds(item.collected_at, generated_at)
    coverage_ratio = _safe_ratio(item.covered_source_count, item.target_source_count)
    critical_field_completeness_score = _safe_ratio(
        item.critical_field_count - item.missing_critical_field_count,
        item.critical_field_count,
    )
    duplicate_corroboration_score = min(
        _safe_ratio(
            item.duplicate_corroboration_count,
            item.required_duplicate_corroboration_count,
        ),
        ONE,
    )
    freshness_score = _freshness_score(collection_age_seconds, config)
    completeness_score = _quantize(
        coverage_ratio * config.target_coverage_weight
        + item.parse_confidence_ratio * config.parse_confidence_weight
        + critical_field_completeness_score * config.critical_field_weight
        + duplicate_corroboration_score * config.duplicate_corroboration_weight
        + freshness_score * config.freshness_weight
        + item.authority_score * config.authority_weight,
    )
    reason_codes = _row_reason_codes(
        coverage_ratio=coverage_ratio,
        parse_confidence_ratio=item.parse_confidence_ratio,
        critical_field_completeness_score=critical_field_completeness_score,
        duplicate_corroboration_score=duplicate_corroboration_score,
        freshness_score=freshness_score,
        authority_score=item.authority_score,
        completeness_score=completeness_score,
        config=config,
    )

    return ResearchSourceScrapingCoverageCompletenessRow(
        row_index=_count_decimal(row_number),
        tool_family=item.tool_family,
        collection_age_seconds=collection_age_seconds,
        target_source_count=item.target_source_count,
        covered_source_count=item.covered_source_count,
        coverage_ratio=coverage_ratio,
        parse_confidence_ratio=item.parse_confidence_ratio,
        critical_field_completeness_score=critical_field_completeness_score,
        missing_critical_field_count=item.missing_critical_field_count,
        duplicate_corroboration_score=duplicate_corroboration_score,
        freshness_score=freshness_score,
        authority_score=item.authority_score,
        completeness_score=completeness_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    coverage_ratio: Decimal,
    parse_confidence_ratio: Decimal,
    critical_field_completeness_score: Decimal,
    duplicate_corroboration_score: Decimal,
    freshness_score: Decimal,
    authority_score: Decimal,
    completeness_score: Decimal,
    config: ResearchSourceScrapingCoverageCompletenessConfig,
) -> tuple[str, ...]:
    block_reason_codes: list[str] = []
    if coverage_ratio < config.min_coverage_watch_ratio:
        block_reason_codes.append("coverage_below_watch_threshold")
    if parse_confidence_ratio < config.min_parse_confidence_watch_ratio:
        block_reason_codes.append("parse_confidence_below_watch_threshold")
    if critical_field_completeness_score < config.min_critical_field_completeness_watch_ratio:
        block_reason_codes.append("critical_field_completeness_below_watch_threshold")
    if duplicate_corroboration_score < config.min_duplicate_corroboration_watch_ratio:
        block_reason_codes.append("duplicate_corroboration_below_watch_threshold")
    if freshness_score < config.min_freshness_watch_score:
        block_reason_codes.append("freshness_below_watch_threshold")
    if authority_score < config.min_authority_watch_score:
        block_reason_codes.append("authority_below_watch_threshold")
    if completeness_score < config.min_completeness_watch_score:
        block_reason_codes.append("completeness_score_below_watch_threshold")
    if block_reason_codes:
        return _normalize_reason_codes("reason_codes", tuple(block_reason_codes))

    watch_reason_codes: list[str] = []
    if coverage_ratio < config.min_coverage_pass_ratio:
        watch_reason_codes.append("coverage_below_target")
    if parse_confidence_ratio < config.min_parse_confidence_pass_ratio:
        watch_reason_codes.append("parse_confidence_below_pass_threshold")
    if critical_field_completeness_score < config.min_critical_field_completeness_pass_ratio:
        watch_reason_codes.append("critical_field_completeness_below_pass_threshold")
    if duplicate_corroboration_score < config.min_duplicate_corroboration_pass_ratio:
        watch_reason_codes.append("duplicate_corroboration_below_pass_threshold")
    if freshness_score < config.min_freshness_pass_score:
        watch_reason_codes.append("freshness_below_pass_threshold")
    if authority_score < config.min_authority_pass_score:
        watch_reason_codes.append("authority_below_pass_threshold")
    if completeness_score < config.min_completeness_pass_score:
        watch_reason_codes.append("completeness_score_below_pass_threshold")
    if watch_reason_codes:
        return _normalize_reason_codes("reason_codes", tuple(watch_reason_codes))
    return (PASS_REASON,)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceScrapingCoverageCompletenessRow, ...]) -> str:
    if not rows:
        return "block"
    statuses = {row.status for row in rows}
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScrapingCoverageCompletenessRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    if status == "pass":
        return (PASS_REASON,)
    reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    terminal_reason = BLOCK_REASON if status == "block" else WATCH_REASON
    return _normalize_reason_codes("reason_codes", (*reason_codes, terminal_reason))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScrapingCoverageCompletenessReasonCodeCount, ...]:
    counter = Counter(reason_codes)
    return tuple(
        ResearchSourceScrapingCoverageCompletenessReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _normalize_reason_code_counts(
    values: tuple[ResearchSourceScrapingCoverageCompletenessReasonCodeCount, ...],
) -> tuple[ResearchSourceScrapingCoverageCompletenessReasonCodeCount, ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in values:
        if type(item) is not ResearchSourceScrapingCoverageCompletenessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScrapingCoverageCompletenessReasonCodeCount",
            )
    return tuple(sorted(values, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)))


def _normalize_rows(
    values: tuple[ResearchSourceScrapingCoverageCompletenessRow, ...],
) -> tuple[ResearchSourceScrapingCoverageCompletenessRow, ...]:
    if not isinstance(values, tuple):
        raise ValueError("rows must be a tuple")
    for item in values:
        if type(item) is not ResearchSourceScrapingCoverageCompletenessRow:
            raise ValueError(
                "rows must contain ResearchSourceScrapingCoverageCompletenessRow",
            )
    return values


def _validate_report_consistency(
    report: ResearchSourceScrapingCoverageCompletenessReport,
) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.pass_count != _count_decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.attention_count != report.watch_count + report.block_count:
        raise ValueError("attention_count must match watch_count plus block_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    target_source_count = _sum_decimal(row.target_source_count for row in report.rows)
    covered_source_count = _sum_decimal(row.covered_source_count for row in report.rows)
    if report.target_source_count != target_source_count:
        raise ValueError("target_source_count must match rows")
    if report.covered_source_count != covered_source_count:
        raise ValueError("covered_source_count must match rows")
    if report.missing_critical_field_count != _sum_decimal(
        (row.missing_critical_field_count for row in report.rows),
    ):
        raise ValueError("missing_critical_field_count must match rows")
    if report.aggregate_coverage_ratio != _safe_ratio(
        covered_source_count,
        target_source_count,
    ):
        raise ValueError("aggregate_coverage_ratio must match rows")
    expected_averages = {
        "average_parse_confidence_ratio": _average(
            (row.parse_confidence_ratio for row in report.rows),
        ),
        "average_critical_field_completeness_score": _average(
            (row.critical_field_completeness_score for row in report.rows),
        ),
        "average_duplicate_corroboration_score": _average(
            (row.duplicate_corroboration_score for row in report.rows),
        ),
        "average_freshness_score": _average(row.freshness_score for row in report.rows),
        "average_authority_score": _average(row.authority_score for row in report.rows),
        "average_completeness_score": _average(
            (row.completeness_score for row in report.rows),
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _freshness_score(
    collection_age_seconds: Decimal,
    config: ResearchSourceScrapingCoverageCompletenessConfig,
) -> Decimal:
    if collection_age_seconds <= config.fresh_collection_max_age_seconds:
        return ONE
    if collection_age_seconds >= config.stale_collection_block_age_seconds:
        return ZERO
    stale_window = (
        config.stale_collection_block_age_seconds
        - config.fresh_collection_max_age_seconds
    )
    stale_age = collection_age_seconds - config.fresh_collection_max_age_seconds
    return _quantize(ONE - _safe_ratio(stale_age, stale_window))


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    return _quantize(Decimal(str(delta.total_seconds())))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(sum(normalized, ZERO) / Decimal(len(normalized)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty private string")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_ordered_threshold(
    label: str,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
) -> None:
    if watch_threshold > pass_threshold:
        raise ValueError(f"{label} watch threshold must not exceed pass threshold")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    for value in values:
        _require_reason_code(field_name, value)
    seen = set(values)
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _report_digest(report: ResearchSourceScrapingCoverageCompletenessReport) -> str:
    unsigned = asdict(report)
    unsigned.pop("derived_validation_digest", None)
    payload = _json_ready(unsigned)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
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


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    _reject_float_values(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScrapingCoverageCompletenessReport:
    _require_payload_key_set(
        "payload",
        payload,
        tuple(field.name for field in fields(ResearchSourceScrapingCoverageCompletenessReport)),
    )
    return ResearchSourceScrapingCoverageCompletenessReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        input_count=_payload_decimal("input_count", payload["input_count"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        attention_count=_payload_decimal("attention_count", payload["attention_count"]),
        target_source_count=_payload_decimal(
            "target_source_count",
            payload["target_source_count"],
        ),
        covered_source_count=_payload_decimal(
            "covered_source_count",
            payload["covered_source_count"],
        ),
        missing_critical_field_count=_payload_decimal(
            "missing_critical_field_count",
            payload["missing_critical_field_count"],
        ),
        aggregate_coverage_ratio=_payload_decimal(
            "aggregate_coverage_ratio",
            payload["aggregate_coverage_ratio"],
        ),
        average_parse_confidence_ratio=_payload_decimal(
            "average_parse_confidence_ratio",
            payload["average_parse_confidence_ratio"],
        ),
        average_critical_field_completeness_score=_payload_decimal(
            "average_critical_field_completeness_score",
            payload["average_critical_field_completeness_score"],
        ),
        average_duplicate_corroboration_score=_payload_decimal(
            "average_duplicate_corroboration_score",
            payload["average_duplicate_corroboration_score"],
        ),
        average_freshness_score=_payload_decimal(
            "average_freshness_score",
            payload["average_freshness_score"],
        ),
        average_authority_score=_payload_decimal(
            "average_authority_score",
            payload["average_authority_score"],
        ),
        average_completeness_score=_payload_decimal(
            "average_completeness_score",
            payload["average_completeness_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=_payload_reason_code_counts(payload["reason_code_counts"]),
        rows=_payload_rows(payload["rows"]),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _payload_rows(
    values: object,
) -> tuple[ResearchSourceScrapingCoverageCompletenessRow, ...]:
    if type(values) is not list:
        raise ValueError("rows must be a JSON array")
    return tuple(_payload_row(value) for value in values)


def _payload_row(value: object) -> ResearchSourceScrapingCoverageCompletenessRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_key_set(
        "row",
        value,
        tuple(field.name for field in fields(ResearchSourceScrapingCoverageCompletenessRow)),
    )
    return ResearchSourceScrapingCoverageCompletenessRow(
        row_index=_payload_decimal("row_index", value["row_index"]),
        tool_family=_payload_string("tool_family", value["tool_family"]),
        collection_age_seconds=_payload_decimal(
            "collection_age_seconds",
            value["collection_age_seconds"],
        ),
        target_source_count=_payload_decimal(
            "target_source_count",
            value["target_source_count"],
        ),
        covered_source_count=_payload_decimal(
            "covered_source_count",
            value["covered_source_count"],
        ),
        coverage_ratio=_payload_decimal("coverage_ratio", value["coverage_ratio"]),
        parse_confidence_ratio=_payload_decimal(
            "parse_confidence_ratio",
            value["parse_confidence_ratio"],
        ),
        critical_field_completeness_score=_payload_decimal(
            "critical_field_completeness_score",
            value["critical_field_completeness_score"],
        ),
        missing_critical_field_count=_payload_decimal(
            "missing_critical_field_count",
            value["missing_critical_field_count"],
        ),
        duplicate_corroboration_score=_payload_decimal(
            "duplicate_corroboration_score",
            value["duplicate_corroboration_score"],
        ),
        freshness_score=_payload_decimal("freshness_score", value["freshness_score"]),
        authority_score=_payload_decimal("authority_score", value["authority_score"]),
        completeness_score=_payload_decimal(
            "completeness_score",
            value["completeness_score"],
        ),
        status=_payload_string("status", value["status"]),
        reason_codes=_payload_string_tuple("reason_codes", value["reason_codes"]),
        paper_only=_payload_bool("paper_only", value["paper_only"]),
        report_only=_payload_bool("report_only", value["report_only"]),
        readonly=_payload_bool("readonly", value["readonly"]),
    )


def _payload_reason_code_counts(
    values: object,
) -> tuple[ResearchSourceScrapingCoverageCompletenessReasonCodeCount, ...]:
    if type(values) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    return tuple(_payload_reason_code_count(value) for value in values)


def _payload_reason_code_count(
    value: object,
) -> ResearchSourceScrapingCoverageCompletenessReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_payload_key_set(
        "reason_code_count",
        value,
        tuple(
            field.name
            for field in fields(ResearchSourceScrapingCoverageCompletenessReasonCodeCount)
        ),
    )
    return ResearchSourceScrapingCoverageCompletenessReasonCodeCount(
        reason_code=_payload_string("reason_code", value["reason_code"]),
        count=_payload_decimal("count", value["count"]),
        paper_only=_payload_bool("paper_only", value["paper_only"]),
        report_only=_payload_bool("report_only", value["report_only"]),
        readonly=_payload_bool("readonly", value["readonly"]),
    )


def _require_payload_key_set(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if set(payload) != set(expected_keys):
        raise ValueError(f"{label} keys must match public report schema")


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(_payload_string(field_name, item) for item in value)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_payload(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, (list, tuple)):
        for value in payload:
            _reject_unsafe_public_payload(label, value)
        return
    if isinstance(payload, str):
        _reject_unsafe_public_string(label, payload)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    compact_normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        compact_fragment = re.sub(r"[^a-z0-9]+", "", fragment)
        if fragment in normalized or compact_fragment in compact_normalized:
            raise ValueError(f"unsafe public payload surface in {label}: {value}")


def _reject_float_values(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("public payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_float_values(item)
    if isinstance(value, list):
        for item in value:
            _reject_float_values(item)


for _class in (
    ResearchSourceScrapingCoverageCompletenessConfig,
    ResearchSourceScrapingCoverageCompletenessInput,
    ResearchSourceScrapingCoverageCompletenessRow,
    ResearchSourceScrapingCoverageCompletenessReasonCodeCount,
    ResearchSourceScrapingCoverageCompletenessReport,
):
    for _field in fields(_class):
        if _class is ResearchSourceScrapingCoverageCompletenessInput and (
            _field.name == "private_collection_ref"
        ):
            continue
        _reject_unsafe_public_string(f"{_class.__name__}.{_field.name}", _field.name)
