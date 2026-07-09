"""Pure report-only source scraper signal freshness index reducer.

Callers provide already-sanitized scraper signal telemetry. This module performs
no database, network, scraping, trading, wallet, order, or live operations; it
only reduces local typed inputs into a deterministic public report with redacted
row labels, Decimal-only numerics, and SHA-256 digest validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPER_SIGNAL_FRESHNESS_INDEX_REPORT_CONFIG_VERSION = (
    "research-source-scraper-signal-freshness-index-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
AUTHORITY_TIER_SCORES = {
    "tier_1": Decimal("1.000000"),
    "tier_2": Decimal("0.750000"),
    "tier_3": Decimal("0.500000"),
    "tier_4": Decimal("0.250000"),
}

NO_INPUTS_REASON = "signal_freshness_no_inputs"
PASS_REASON = "signal_freshness_index_pass"
WATCH_REASON = "signal_freshness_index_watch"
BLOCK_REASON = "signal_freshness_index_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "scrape_recency_block",
    "scrape_recency_watch",
    "parser_confidence_block",
    "parser_confidence_watch",
    "authority_tier_block",
    "authority_tier_watch",
    "duplicate_corroboration_block",
    "duplicate_corroboration_watch",
    "missing_fields_block",
    "missing_fields_watch",
    "fallback_coverage_block",
    "fallback_coverage_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ROW_LABEL_RE = re.compile(r"^redacted-scraper-signal-freshness-[0-9]{6}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "allocation",
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "slug",
    "question",
    "source_url",
    "source url",
    "source_text",
    "source text",
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
    "position_size",
    "position size",
    "recommend",
    "sizing",
)

REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "max_scrape_age_seconds",
        "average_scrape_recency_score",
        "average_parser_confidence_score",
        "average_authority_score",
        "average_duplicate_corroboration_score",
        "average_field_completeness_score",
        "average_fallback_coverage_score",
        "average_signal_freshness_index",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSIGNED_REPORT_PAYLOAD_FIELDS = REPORT_PAYLOAD_FIELDS - {
    "derived_validation_digest",
}
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "row_label",
        "scrape_age_seconds",
        "scrape_recency_score",
        "parser_confidence_score",
        "authority_tier",
        "authority_score",
        "duplicate_corroboration_score",
        "field_completeness_score",
        "missing_field_count",
        "fallback_coverage_score",
        "signal_freshness_index",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPER_SIGNAL_FRESHNESS_INDEX_REPORT_CONFIG_VERSION",
    "ResearchSourceScraperSignalFreshnessIndexConfig",
    "ResearchSourceScraperSignalFreshnessIndexInput",
    "ResearchSourceScraperSignalFreshnessIndexReasonCodeCount",
    "ResearchSourceScraperSignalFreshnessIndexReport",
    "ResearchSourceScraperSignalFreshnessIndexRow",
    "STATUSES",
    "build_research_source_scraper_signal_freshness_index_report",
    "research_source_scraper_signal_freshness_index_report_digest",
    "research_source_scraper_signal_freshness_index_report_payload",
    "validate_research_source_scraper_signal_freshness_index_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraperSignalFreshnessIndexConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPER_SIGNAL_FRESHNESS_INDEX_REPORT_CONFIG_VERSION
    )
    fresh_scrape_max_age_seconds: Decimal = Decimal("1800.000000")
    stale_scrape_block_age_seconds: Decimal = Decimal("19800.000000")
    min_parser_confidence_pass_ratio: Decimal = Decimal("0.850000")
    min_parser_confidence_watch_ratio: Decimal = Decimal("0.600000")
    min_authority_pass_score: Decimal = Decimal("0.750000")
    min_authority_watch_score: Decimal = Decimal("0.500000")
    min_signal_freshness_pass_index: Decimal = Decimal("0.800000")
    min_signal_freshness_watch_index: Decimal = Decimal("0.500000")
    scrape_recency_weight: Decimal = Decimal("0.300000")
    parser_confidence_weight: Decimal = Decimal("0.250000")
    authority_weight: Decimal = Decimal("0.150000")
    duplicate_corroboration_weight: Decimal = Decimal("0.100000")
    field_completeness_weight: Decimal = Decimal("0.100000")
    fallback_coverage_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperSignalFreshnessIndexConfig:
            raise TypeError(
                "ResearchSourceScraperSignalFreshnessIndexConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperSignalFreshnessIndexConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPER_SIGNAL_FRESHNESS_INDEX_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_scrape_max_age_seconds",
            "stale_scrape_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_scrape_max_age_seconds >= self.stale_scrape_block_age_seconds:
            raise ValueError(
                "fresh_scrape_max_age_seconds must be below "
                "stale_scrape_block_age_seconds",
            )
        for field_name in (
            "min_parser_confidence_pass_ratio",
            "min_parser_confidence_watch_ratio",
            "min_authority_pass_score",
            "min_authority_watch_score",
            "min_signal_freshness_pass_index",
            "min_signal_freshness_watch_index",
            "scrape_recency_weight",
            "parser_confidence_weight",
            "authority_weight",
            "duplicate_corroboration_weight",
            "field_completeness_weight",
            "fallback_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.min_parser_confidence_watch_ratio > self.min_parser_confidence_pass_ratio:
            raise ValueError(
                "parser confidence watch threshold must not exceed pass threshold",
            )
        if self.min_authority_watch_score > self.min_authority_pass_score:
            raise ValueError("authority watch threshold must not exceed pass threshold")
        if self.min_signal_freshness_watch_index > self.min_signal_freshness_pass_index:
            raise ValueError("signal freshness watch threshold must not exceed pass threshold")
        weight_sum = _quantize(
            self.scrape_recency_weight
            + self.parser_confidence_weight
            + self.authority_weight
            + self.duplicate_corroboration_weight
            + self.field_completeness_weight
            + self.fallback_coverage_weight,
        )
        if weight_sum != ONE:
            raise ValueError("signal freshness weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraperSignalFreshnessIndexInput:
    private_signal_ref: str
    scraped_at: datetime
    parser_confidence_ratio: Decimal
    authority_tier: str
    duplicate_corroboration_count: Decimal
    required_duplicate_corroboration_count: Decimal
    expected_field_count: Decimal
    missing_field_count: Decimal
    fallback_observed_count: Decimal
    fallback_required_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperSignalFreshnessIndexInput:
            raise TypeError(
                "ResearchSourceScraperSignalFreshnessIndexInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperSignalFreshnessIndexInput, "input")
        _require_private_string("private_signal_ref", self.private_signal_ref)
        object.__setattr__(self, "scraped_at", _as_utc("scraped_at", self.scraped_at))
        object.__setattr__(
            self,
            "parser_confidence_ratio",
            _normalize_probability("parser_confidence_ratio", self.parser_confidence_ratio),
        )
        _require_member("authority_tier", self.authority_tier, tuple(AUTHORITY_TIER_SCORES))
        for field_name in (
            "duplicate_corroboration_count",
            "fallback_observed_count",
            "missing_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_duplicate_corroboration_count",
            "expected_field_count",
            "fallback_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if self.missing_field_count > self.expected_field_count:
            raise ValueError("missing_field_count must not exceed expected_field_count")
        if self.fallback_observed_count > self.fallback_required_count:
            raise ValueError(
                "fallback_observed_count must not exceed fallback_required_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraperSignalFreshnessIndexRow:
    row_label: str
    scrape_age_seconds: Decimal
    scrape_recency_score: Decimal
    parser_confidence_score: Decimal
    authority_tier: str
    authority_score: Decimal
    duplicate_corroboration_score: Decimal
    field_completeness_score: Decimal
    missing_field_count: Decimal
    fallback_coverage_score: Decimal
    signal_freshness_index: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperSignalFreshnessIndexRow:
            raise TypeError(
                "ResearchSourceScraperSignalFreshnessIndexRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperSignalFreshnessIndexRow, "row")
        _require_public_identifier("row_label", self.row_label)
        if not ROW_LABEL_RE.fullmatch(self.row_label):
            raise ValueError("row_label must use the redacted report row format")
        object.__setattr__(
            self,
            "scrape_age_seconds",
            _normalize_nonnegative_decimal("scrape_age_seconds", self.scrape_age_seconds),
        )
        for field_name in (
            "scrape_recency_score",
            "parser_confidence_score",
            "authority_score",
            "duplicate_corroboration_score",
            "field_completeness_score",
            "fallback_coverage_score",
            "signal_freshness_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
        )
        _require_member("authority_tier", self.authority_tier, tuple(AUTHORITY_TIER_SCORES))
        if self.authority_score != AUTHORITY_TIER_SCORES[self.authority_tier]:
            raise ValueError("authority_score must match authority_tier")
        object.__setattr__(
            self,
            "missing_field_count",
            _normalize_nonnegative_count("missing_field_count", self.missing_field_count),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        status_reasons = tuple(
            reason_code
            for reason_code in self.reason_codes
            if reason_code in (PASS_REASON, WATCH_REASON, BLOCK_REASON)
        )
        if status_reasons != (_status_reason(self.status),):
            raise ValueError("status reason must match status")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraperSignalFreshnessIndexReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperSignalFreshnessIndexReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraperSignalFreshnessIndexReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraperSignalFreshnessIndexReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraperSignalFreshnessIndexReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_scrape_age_seconds: Decimal
    average_scrape_recency_score: Decimal
    average_parser_confidence_score: Decimal
    average_authority_score: Decimal
    average_duplicate_corroboration_score: Decimal
    average_field_completeness_score: Decimal
    average_fallback_coverage_score: Decimal
    average_signal_freshness_index: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraperSignalFreshnessIndexReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraperSignalFreshnessIndexRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperSignalFreshnessIndexReport:
            raise TypeError(
                "ResearchSourceScraperSignalFreshnessIndexReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperSignalFreshnessIndexReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPER_SIGNAL_FRESHNESS_INDEX_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_scrape_age_seconds",
            _normalize_nonnegative_decimal(
                "max_scrape_age_seconds",
                self.max_scrape_age_seconds,
            ),
        )
        for field_name in (
            "average_scrape_recency_score",
            "average_parser_confidence_score",
            "average_authority_score",
            "average_duplicate_corroboration_score",
            "average_field_completeness_score",
            "average_fallback_coverage_score",
            "average_signal_freshness_index",
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
        return research_source_scraper_signal_freshness_index_report_payload(self)


def build_research_source_scraper_signal_freshness_index_report(
    inputs: Iterable[ResearchSourceScraperSignalFreshnessIndexInput],
    *,
    config: ResearchSourceScraperSignalFreshnessIndexConfig,
    generated_at: datetime,
) -> ResearchSourceScraperSignalFreshnessIndexReport:
    if type(config) is not ResearchSourceScraperSignalFreshnessIndexConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScraperSignalFreshnessIndexConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.scraped_at > generated_at:
            raise ValueError("scraped_at cannot be after generated_at")

    rows = tuple(
        _row_from_input(
            item,
            row_number=index,
            config=config,
            generated_at=generated_at,
        )
        for index, item in enumerate(normalized_inputs, start=1)
    )
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    return ResearchSourceScraperSignalFreshnessIndexReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=watch_count + block_count,
        max_scrape_age_seconds=max(
            (row.scrape_age_seconds for row in rows),
            default=ZERO,
        ),
        average_scrape_recency_score=_average(row.scrape_recency_score for row in rows),
        average_parser_confidence_score=_average(
            (row.parser_confidence_score for row in rows),
        ),
        average_authority_score=_average(row.authority_score for row in rows),
        average_duplicate_corroboration_score=_average(
            (row.duplicate_corroboration_score for row in rows),
        ),
        average_field_completeness_score=_average(
            (row.field_completeness_score for row in rows),
        ),
        average_fallback_coverage_score=_average(
            (row.fallback_coverage_score for row in rows),
        ),
        average_signal_freshness_index=_average(
            (row.signal_freshness_index for row in rows),
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scraper_signal_freshness_index_report_payload(
    report: ResearchSourceScraperSignalFreshnessIndexReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraperSignalFreshnessIndexReport:
        raise ValueError(
            "report must be exactly ResearchSourceScraperSignalFreshnessIndexReport",
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


def research_source_scraper_signal_freshness_index_report_digest(
    report: ResearchSourceScraperSignalFreshnessIndexReport,
) -> str:
    payload = research_source_scraper_signal_freshness_index_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scraper_signal_freshness_index_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str or not DIGEST_RE.fullmatch(digest):
            return False
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest() == digest
    except (DecimalException, TypeError, ValueError):
        return False


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScraperSignalFreshnessIndexInput],
) -> tuple[ResearchSourceScraperSignalFreshnessIndexInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScraperSignalFreshnessIndexInput:
            raise ValueError(
                "inputs must contain ResearchSourceScraperSignalFreshnessIndexInput",
            )
        _require_hard_flags("input", item)
    return tuple(sorted(normalized, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScraperSignalFreshnessIndexInput,
) -> tuple[str, str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        item.private_signal_ref,
        item.scraped_at.isoformat(),
        item.parser_confidence_ratio,
        item.authority_tier,
        item.duplicate_corroboration_count,
        item.required_duplicate_corroboration_count,
        item.expected_field_count,
        item.missing_field_count,
        item.fallback_observed_count,
        item.fallback_required_count,
    )


def _row_from_input(
    item: ResearchSourceScraperSignalFreshnessIndexInput,
    *,
    row_number: int,
    config: ResearchSourceScraperSignalFreshnessIndexConfig,
    generated_at: datetime,
) -> ResearchSourceScraperSignalFreshnessIndexRow:
    scrape_age_seconds = _age_seconds(generated_at, item.scraped_at)
    scrape_recency_score = _scrape_recency_score(scrape_age_seconds, config)
    authority_score = AUTHORITY_TIER_SCORES[item.authority_tier]
    duplicate_score = min(
        ONE,
        _safe_ratio(
            item.duplicate_corroboration_count,
            item.required_duplicate_corroboration_count,
        ),
    )
    field_score = _quantize(
        ONE - _safe_ratio(item.missing_field_count, item.expected_field_count),
    )
    fallback_score = min(
        ONE,
        _safe_ratio(item.fallback_observed_count, item.fallback_required_count),
    )
    signal_index = _quantize(
        scrape_recency_score * config.scrape_recency_weight
        + item.parser_confidence_ratio * config.parser_confidence_weight
        + authority_score * config.authority_weight
        + duplicate_score * config.duplicate_corroboration_weight
        + field_score * config.field_completeness_weight
        + fallback_score * config.fallback_coverage_weight,
    )
    reason_codes = _row_reason_codes(
        scrape_age_seconds=scrape_age_seconds,
        scrape_recency_score=scrape_recency_score,
        parser_confidence_score=item.parser_confidence_ratio,
        authority_score=authority_score,
        duplicate_corroboration_score=duplicate_score,
        missing_field_count=item.missing_field_count,
        expected_field_count=item.expected_field_count,
        fallback_coverage_score=fallback_score,
        config=config,
    )
    status = _row_status(reason_codes, signal_index, config)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*reason_codes, _status_reason(status)),
    )
    return ResearchSourceScraperSignalFreshnessIndexRow(
        row_label=f"redacted-scraper-signal-freshness-{row_number:06d}",
        scrape_age_seconds=scrape_age_seconds,
        scrape_recency_score=scrape_recency_score,
        parser_confidence_score=item.parser_confidence_ratio,
        authority_tier=item.authority_tier,
        authority_score=authority_score,
        duplicate_corroboration_score=duplicate_score,
        field_completeness_score=field_score,
        missing_field_count=item.missing_field_count,
        fallback_coverage_score=fallback_score,
        signal_freshness_index=signal_index,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _scrape_recency_score(
    scrape_age_seconds: Decimal,
    config: ResearchSourceScraperSignalFreshnessIndexConfig,
) -> Decimal:
    if scrape_age_seconds <= config.fresh_scrape_max_age_seconds:
        return ONE
    if scrape_age_seconds >= config.stale_scrape_block_age_seconds:
        return ZERO
    stale_window = (
        config.stale_scrape_block_age_seconds - config.fresh_scrape_max_age_seconds
    )
    stale_progress = _safe_ratio(
        scrape_age_seconds - config.fresh_scrape_max_age_seconds,
        stale_window,
    )
    return _quantize(ONE - stale_progress)


def _row_reason_codes(
    *,
    scrape_age_seconds: Decimal,
    scrape_recency_score: Decimal,
    parser_confidence_score: Decimal,
    authority_score: Decimal,
    duplicate_corroboration_score: Decimal,
    missing_field_count: Decimal,
    expected_field_count: Decimal,
    fallback_coverage_score: Decimal,
    config: ResearchSourceScraperSignalFreshnessIndexConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if scrape_age_seconds >= config.stale_scrape_block_age_seconds:
        reason_codes.append("scrape_recency_block")
    elif scrape_recency_score < ONE:
        reason_codes.append("scrape_recency_watch")

    if parser_confidence_score < config.min_parser_confidence_watch_ratio:
        reason_codes.append("parser_confidence_block")
    elif parser_confidence_score < config.min_parser_confidence_pass_ratio:
        reason_codes.append("parser_confidence_watch")

    if authority_score < config.min_authority_watch_score:
        reason_codes.append("authority_tier_block")
    elif authority_score < config.min_authority_pass_score:
        reason_codes.append("authority_tier_watch")

    if duplicate_corroboration_score < HALF:
        reason_codes.append("duplicate_corroboration_block")
    elif duplicate_corroboration_score < ONE:
        reason_codes.append("duplicate_corroboration_watch")

    if missing_field_count == expected_field_count:
        reason_codes.append("missing_fields_block")
    elif missing_field_count > ZERO:
        reason_codes.append("missing_fields_watch")

    if fallback_coverage_score < HALF:
        reason_codes.append("fallback_coverage_block")
    elif fallback_coverage_score < ONE:
        reason_codes.append("fallback_coverage_watch")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(
    reason_codes: tuple[str, ...],
    signal_index: Decimal,
    config: ResearchSourceScraperSignalFreshnessIndexConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if signal_index < config.min_signal_freshness_watch_index:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if signal_index < config.min_signal_freshness_pass_index:
        return "watch"
    return "pass"


def _status_reason(status: str) -> str:
    if status == "pass":
        return PASS_REASON
    if status == "watch":
        return WATCH_REASON
    if status == "block":
        return BLOCK_REASON
    raise ValueError("status must be pass, watch, or block")


def _report_status(rows: tuple[ResearchSourceScraperSignalFreshnessIndexRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraperSignalFreshnessIndexRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScraperSignalFreshnessIndexReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchSourceScraperSignalFreshnessIndexReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: tuple[ResearchSourceScraperSignalFreshnessIndexRow, ...],
) -> tuple[ResearchSourceScraperSignalFreshnessIndexRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraperSignalFreshnessIndexRow:
            raise ValueError(
                "rows must contain ResearchSourceScraperSignalFreshnessIndexRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceScraperSignalFreshnessIndexRow) -> tuple[int, str]:
    return (STATUS_WEIGHT[row.status], row.row_label)


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraperSignalFreshnessIndexReasonCodeCount, ...],
) -> tuple[ResearchSourceScraperSignalFreshnessIndexReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceScraperSignalFreshnessIndexReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraperSignalFreshnessIndexReasonCodeCount",
            )
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_report_consistency(
    report: ResearchSourceScraperSignalFreshnessIndexReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
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
        raise ValueError("attention_count must match watch and block counts")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows and status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.max_scrape_age_seconds != max(
        (row.scrape_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_scrape_age_seconds must match rows")
    expected_averages = {
        "average_scrape_recency_score": _average(
            (row.scrape_recency_score for row in report.rows),
        ),
        "average_parser_confidence_score": _average(
            (row.parser_confidence_score for row in report.rows),
        ),
        "average_authority_score": _average(row.authority_score for row in report.rows),
        "average_duplicate_corroboration_score": _average(
            (row.duplicate_corroboration_score for row in report.rows),
        ),
        "average_field_completeness_score": _average(
            (row.field_completeness_score for row in report.rows),
        ),
        "average_fallback_coverage_score": _average(
            (row.fallback_coverage_score for row in report.rows),
        ),
        "average_signal_freshness_index": _average(
            (row.signal_freshness_index for row in report.rows),
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized)


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _safe_ratio(sum(normalized, ZERO), _count_decimal(len(normalized)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, scraped_at: datetime) -> Decimal:
    delta = generated_at - scraped_at
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / MICROSECOND_DIVISOR,
        )


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > 2048:
        raise ValueError(f"{field_name} must not exceed 2048 characters")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, STATUSES)


def _require_reason_code(field_name: str, value: object) -> str:
    return _require_member(field_name, value, REASON_CODE_SEQUENCE)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _report_digest(report: ResearchSourceScraperSignalFreshnessIndexReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report digest payload must be a JSON object")
    _require_exact_payload_keys(
        "unsigned report payload",
        payload,
        UNSIGNED_REPORT_PAYLOAD_FIELDS,
    )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    report = _report_from_public_payload(payload)
    canonical_payload = _json_ready(asdict(report))
    if canonical_payload != payload:
        raise ValueError("payload must use the canonical public schema")
    _reject_unsafe_public_payload(
        "payload",
        canonical_payload,
        allow_json_containers=True,
    )
    json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraperSignalFreshnessIndexReport:
    _require_exact_payload_keys("report payload", payload, REPORT_PAYLOAD_FIELDS)
    reason_codes = _payload_string_tuple("reason_codes", payload["reason_codes"])
    reason_code_counts = _payload_reason_code_counts(payload["reason_code_counts"])
    rows = _payload_rows(payload["rows"])
    return ResearchSourceScraperSignalFreshnessIndexReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        input_count=_payload_decimal("input_count", payload["input_count"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        attention_count=_payload_decimal("attention_count", payload["attention_count"]),
        max_scrape_age_seconds=_payload_decimal(
            "max_scrape_age_seconds",
            payload["max_scrape_age_seconds"],
        ),
        average_scrape_recency_score=_payload_decimal(
            "average_scrape_recency_score",
            payload["average_scrape_recency_score"],
        ),
        average_parser_confidence_score=_payload_decimal(
            "average_parser_confidence_score",
            payload["average_parser_confidence_score"],
        ),
        average_authority_score=_payload_decimal(
            "average_authority_score",
            payload["average_authority_score"],
        ),
        average_duplicate_corroboration_score=_payload_decimal(
            "average_duplicate_corroboration_score",
            payload["average_duplicate_corroboration_score"],
        ),
        average_field_completeness_score=_payload_decimal(
            "average_field_completeness_score",
            payload["average_field_completeness_score"],
        ),
        average_fallback_coverage_score=_payload_decimal(
            "average_fallback_coverage_score",
            payload["average_fallback_coverage_score"],
        ),
        average_signal_freshness_index=_payload_decimal(
            "average_signal_freshness_index",
            payload["average_signal_freshness_index"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _payload_rows(
    value: object,
) -> tuple[ResearchSourceScraperSignalFreshnessIndexRow, ...]:
    values = _payload_list("rows", value)
    rows: list[ResearchSourceScraperSignalFreshnessIndexRow] = []
    for index, item in enumerate(values):
        label = f"rows[{index}]"
        _require_exact_payload_keys(label, item, ROW_PAYLOAD_FIELDS)
        rows.append(
            ResearchSourceScraperSignalFreshnessIndexRow(
                row_label=_payload_string("row_label", item["row_label"]),
                scrape_age_seconds=_payload_decimal(
                    "scrape_age_seconds",
                    item["scrape_age_seconds"],
                ),
                scrape_recency_score=_payload_decimal(
                    "scrape_recency_score",
                    item["scrape_recency_score"],
                ),
                parser_confidence_score=_payload_decimal(
                    "parser_confidence_score",
                    item["parser_confidence_score"],
                ),
                authority_tier=_payload_string(
                    "authority_tier",
                    item["authority_tier"],
                ),
                authority_score=_payload_decimal(
                    "authority_score",
                    item["authority_score"],
                ),
                duplicate_corroboration_score=_payload_decimal(
                    "duplicate_corroboration_score",
                    item["duplicate_corroboration_score"],
                ),
                field_completeness_score=_payload_decimal(
                    "field_completeness_score",
                    item["field_completeness_score"],
                ),
                missing_field_count=_payload_decimal(
                    "missing_field_count",
                    item["missing_field_count"],
                ),
                fallback_coverage_score=_payload_decimal(
                    "fallback_coverage_score",
                    item["fallback_coverage_score"],
                ),
                signal_freshness_index=_payload_decimal(
                    "signal_freshness_index",
                    item["signal_freshness_index"],
                ),
                status=_payload_string("status", item["status"]),
                reason_codes=_payload_string_tuple(
                    "reason_codes",
                    item["reason_codes"],
                ),
                paper_only=_payload_true("paper_only", item["paper_only"]),
                report_only=_payload_true("report_only", item["report_only"]),
                readonly=_payload_true("readonly", item["readonly"]),
            ),
        )
    return tuple(rows)


def _payload_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceScraperSignalFreshnessIndexReasonCodeCount, ...]:
    values = _payload_list("reason_code_counts", value)
    counts: list[ResearchSourceScraperSignalFreshnessIndexReasonCodeCount] = []
    for index, item in enumerate(values):
        label = f"reason_code_counts[{index}]"
        _require_exact_payload_keys(label, item, REASON_CODE_COUNT_PAYLOAD_FIELDS)
        counts.append(
            ResearchSourceScraperSignalFreshnessIndexReasonCodeCount(
                reason_code=_payload_string("reason_code", item["reason_code"]),
                count=_payload_decimal("count", item["count"]),
                paper_only=_payload_true("paper_only", item["paper_only"]),
                report_only=_payload_true("report_only", item["report_only"]),
                readonly=_payload_true("readonly", item["readonly"]),
            ),
        )
    return tuple(counts)


def _require_exact_payload_keys(
    label: str,
    value: object,
    expected_keys: frozenset[str],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    actual_keys = frozenset(value)
    if actual_keys != expected_keys:
        raise ValueError(f"{label} fields must match the public schema")


def _payload_list(label: str, value: object) -> list[dict[str, Any]]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a JSON array")
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{label} entries must be JSON objects")
    return value


def _payload_string_tuple(label: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a JSON array")
    return tuple(
        _payload_string(f"{label}[{index}]", item)
        for index, item in enumerate(value)
    )


def _payload_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    return value


def _payload_decimal(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{label} must be finite")
    return decimal_value


def _payload_datetime(label: str, value: object) -> datetime:
    text = _payload_string(label, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO datetime") from exc
    return _as_utc(label, parsed)


def _payload_true(label: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{label} must be True")
    return True


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")
