"""Pure report-only scraper failure triage reducer for source collection.

Callers provide already-sanitized scraper telemetry. This module performs no
network, database, or scraping calls; it only produces a deterministic public
report with redacted row labels, Decimal-only numerics, and SHA-256 digest
validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPER_FAILURE_TRIAGE_REPORT_CONFIG_VERSION = (
    "research-source-scraper-failure-triage-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
AUTHORITY_TIERS = ("primary", "secondary", "tertiary", "unverified")
AUTHORITY_TIER_SCORES = {
    "primary": Decimal("1.000000"),
    "secondary": Decimal("0.600000"),
    "tertiary": Decimal("0.400000"),
    "unverified": Decimal("0.200000"),
}
AUTHORITY_TIER_PASS_SCORE = Decimal("0.800000")
AUTHORITY_TIER_WATCH_SCORE = Decimal("0.500000")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "scraper_failure_triage_no_inputs"
PASS_REASON = "scraper_failure_triage_pass"
WATCH_REASON = "scraper_failure_triage_watch"
BLOCK_REASON = "scraper_failure_triage_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "failure_rate_block",
    "failure_rate_watch",
    "freshness_block",
    "freshness_watch",
    "parse_confidence_block",
    "parse_confidence_watch",
    "authority_tier_block",
    "authority_tier_watch",
    "fallback_coverage_block",
    "fallback_coverage_watch",
    "critical_fields_missing_block",
    "critical_fields_missing_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ROW_LABEL_RE = re.compile(r"^redacted-scraper-failure-triage-[0-9]{6}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
    "max_observation_age_seconds",
    "average_failure_rate",
    "average_parse_confidence_score",
    "average_critical_field_completeness_score",
    "average_authority_score",
    "average_freshness_score",
    "average_fallback_coverage_score",
    "average_triage_score",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "row_label",
    "generated_at",
    "observed_at",
    "authority_tier",
    "scrape_attempt_count",
    "scrape_failure_count",
    "critical_field_count",
    "fallback_available_count",
    "fallback_required_count",
    "observation_age_seconds",
    "failure_rate",
    "failure_resilience_score",
    "parse_confidence_score",
    "critical_field_completeness_score",
    "authority_score",
    "freshness_score",
    "fallback_coverage_score",
    "missing_critical_field_count",
    "triage_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_FRAGMENTS = (
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
    "network",
    "database",
    "authentication",
    "authorization",
    "credential",
    "table",
    "token",
    "api_key",
    "api-key",
    "private_key",
    "private-key",
    "secret",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommend",
    "recommendation",
    "execute",
    "execution",
    "live",
)
UNSAFE_PUBLIC_STANDALONE_RE = re.compile(r"(^|[^a-z0-9])auth($|[^a-z0-9])")

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPER_FAILURE_TRIAGE_REPORT_CONFIG_VERSION",
    "ResearchSourceScraperFailureTriageConfig",
    "ResearchSourceScraperFailureTriageInput",
    "ResearchSourceScraperFailureTriageReasonCodeCount",
    "ResearchSourceScraperFailureTriageReport",
    "ResearchSourceScraperFailureTriageRow",
    "STATUSES",
    "build_research_source_scraper_failure_triage_report",
    "research_source_scraper_failure_triage_report_digest",
    "research_source_scraper_failure_triage_report_payload",
    "validate_research_source_scraper_failure_triage_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraperFailureTriageConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPER_FAILURE_TRIAGE_REPORT_CONFIG_VERSION
    )
    fresh_observation_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_observation_block_age_seconds: Decimal = Decimal("86400.000000")
    min_parse_confidence_pass_ratio: Decimal = Decimal("0.850000")
    min_parse_confidence_watch_ratio: Decimal = Decimal("0.600000")
    min_fallback_coverage_pass_ratio: Decimal = Decimal("0.750000")
    min_fallback_coverage_watch_ratio: Decimal = Decimal("0.400000")
    max_failure_rate_pass_ratio: Decimal = Decimal("0.100000")
    max_failure_rate_watch_ratio: Decimal = Decimal("0.350000")
    min_triage_pass_score: Decimal = Decimal("0.800000")
    min_triage_watch_score: Decimal = Decimal("0.500000")
    failure_rate_weight: Decimal = Decimal("0.250000")
    parse_confidence_weight: Decimal = Decimal("0.200000")
    critical_field_weight: Decimal = Decimal("0.200000")
    authority_weight: Decimal = Decimal("0.150000")
    freshness_weight: Decimal = Decimal("0.100000")
    fallback_coverage_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperFailureTriageConfig:
            raise TypeError(
                "ResearchSourceScraperFailureTriageConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperFailureTriageConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPER_FAILURE_TRIAGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        supported_numeric_fields = (
            "fresh_observation_max_age_seconds",
            "stale_observation_block_age_seconds",
            "min_parse_confidence_pass_ratio",
            "min_parse_confidence_watch_ratio",
            "min_fallback_coverage_pass_ratio",
            "min_fallback_coverage_watch_ratio",
            "max_failure_rate_pass_ratio",
            "max_failure_rate_watch_ratio",
            "min_triage_pass_score",
            "min_triage_watch_score",
            "failure_rate_weight",
            "parse_confidence_weight",
            "critical_field_weight",
            "authority_weight",
            "freshness_weight",
            "fallback_coverage_weight",
        )
        raw_supported_values = {
            field_name: getattr(self, field_name)
            for field_name in supported_numeric_fields
        }
        for field_name in (
            "fresh_observation_max_age_seconds",
            "stale_observation_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.fresh_observation_max_age_seconds
            >= self.stale_observation_block_age_seconds
        ):
            raise ValueError(
                "fresh_observation_max_age_seconds must be below "
                "stale_observation_block_age_seconds",
            )
        for field_name in (
            "min_parse_confidence_pass_ratio",
            "min_parse_confidence_watch_ratio",
            "min_fallback_coverage_pass_ratio",
            "min_fallback_coverage_watch_ratio",
            "max_failure_rate_pass_ratio",
            "max_failure_rate_watch_ratio",
            "min_triage_pass_score",
            "min_triage_watch_score",
            "failure_rate_weight",
            "parse_confidence_weight",
            "critical_field_weight",
            "authority_weight",
            "freshness_weight",
            "fallback_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.min_parse_confidence_watch_ratio
            > self.min_parse_confidence_pass_ratio
        ):
            raise ValueError(
                "parse confidence watch threshold must not exceed pass threshold",
            )
        if (
            self.min_fallback_coverage_watch_ratio
            > self.min_fallback_coverage_pass_ratio
        ):
            raise ValueError(
                "fallback coverage watch threshold must not exceed pass threshold",
            )
        if self.max_failure_rate_pass_ratio > self.max_failure_rate_watch_ratio:
            raise ValueError("failure rate pass threshold must not exceed watch threshold")
        if self.min_triage_watch_score > self.min_triage_pass_score:
            raise ValueError("triage watch threshold must not exceed pass threshold")
        weight_sum = _sum_quantized(
            (
                self.failure_rate_weight,
                self.parse_confidence_weight,
                self.critical_field_weight,
                self.authority_weight,
                self.freshness_weight,
                self.fallback_coverage_weight,
            ),
        )
        if weight_sum != ONE:
            raise ValueError("triage score weights must sum to 1")
        for field_name in supported_numeric_fields:
            expected_value = ResearchSourceScraperFailureTriageConfig.__dataclass_fields__[
                field_name
            ].default
            if raw_supported_values[field_name] != expected_value:
                raise ValueError(
                    f"{field_name} must match the supported config version",
                )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraperFailureTriageInput:
    private_collection_ref: str
    observed_at: datetime
    scrape_attempt_count: Decimal
    scrape_failure_count: Decimal
    parse_confidence_ratio: Decimal
    critical_field_count: Decimal
    missing_critical_field_count: Decimal
    authority_tier: str
    fallback_available_count: Decimal
    fallback_required_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperFailureTriageInput:
            raise TypeError(
                "ResearchSourceScraperFailureTriageInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperFailureTriageInput, "input")
        _require_private_string("private_collection_ref", self.private_collection_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "scrape_attempt_count",
            "scrape_failure_count",
            "critical_field_count",
            "missing_critical_field_count",
            "fallback_available_count",
            "fallback_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("scrape_attempt_count", "critical_field_count"):
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        if self.fallback_required_count <= ZERO:
            raise ValueError("fallback_required_count must be positive")
        object.__setattr__(
            self,
            "parse_confidence_ratio",
            _normalize_probability(
                "parse_confidence_ratio",
                self.parse_confidence_ratio,
            ),
        )
        _require_member("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        if self.scrape_failure_count > self.scrape_attempt_count:
            raise ValueError("scrape_failure_count must not exceed scrape_attempt_count")
        if self.missing_critical_field_count > self.critical_field_count:
            raise ValueError(
                "missing_critical_field_count must not exceed critical_field_count",
            )
        if self.fallback_available_count > self.fallback_required_count:
            raise ValueError(
                "fallback_available_count must not exceed fallback_required_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraperFailureTriageRow:
    row_label: str
    generated_at: datetime
    observed_at: datetime
    authority_tier: str
    scrape_attempt_count: Decimal
    scrape_failure_count: Decimal
    critical_field_count: Decimal
    fallback_available_count: Decimal
    fallback_required_count: Decimal
    observation_age_seconds: Decimal
    failure_rate: Decimal
    failure_resilience_score: Decimal
    parse_confidence_score: Decimal
    critical_field_completeness_score: Decimal
    authority_score: Decimal
    freshness_score: Decimal
    fallback_coverage_score: Decimal
    missing_critical_field_count: Decimal
    triage_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperFailureTriageRow:
            raise TypeError(
                "ResearchSourceScraperFailureTriageRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperFailureTriageRow, "row")
        _require_row_label(self.row_label)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.observed_at > self.generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        _require_member("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        for field_name in (
            "scrape_attempt_count",
            "scrape_failure_count",
            "critical_field_count",
            "missing_critical_field_count",
            "fallback_available_count",
            "fallback_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scrape_attempt_count",
            "critical_field_count",
            "fallback_required_count",
        ):
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        if self.scrape_failure_count > self.scrape_attempt_count:
            raise ValueError("scrape_failure_count must not exceed scrape_attempt_count")
        if self.missing_critical_field_count > self.critical_field_count:
            raise ValueError(
                "missing_critical_field_count must not exceed critical_field_count",
            )
        if self.fallback_available_count > self.fallback_required_count:
            raise ValueError(
                "fallback_available_count must not exceed fallback_required_count",
            )
        object.__setattr__(
            self,
            "observation_age_seconds",
            _normalize_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        for field_name in (
            "failure_rate",
            "failure_resilience_score",
            "parse_confidence_score",
            "critical_field_completeness_score",
            "authority_score",
            "freshness_score",
            "fallback_coverage_score",
            "triage_score",
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
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraperFailureTriageReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperFailureTriageReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraperFailureTriageReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraperFailureTriageReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraperFailureTriageReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_observation_age_seconds: Decimal
    average_failure_rate: Decimal
    average_parse_confidence_score: Decimal
    average_critical_field_completeness_score: Decimal
    average_authority_score: Decimal
    average_freshness_score: Decimal
    average_fallback_coverage_score: Decimal
    average_triage_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraperFailureTriageReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraperFailureTriageRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperFailureTriageReport:
            raise TypeError(
                "ResearchSourceScraperFailureTriageReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperFailureTriageReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPER_FAILURE_TRIAGE_REPORT_CONFIG_VERSION
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
            "max_observation_age_seconds",
            _normalize_nonnegative_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        for field_name in (
            "average_failure_rate",
            "average_parse_confidence_score",
            "average_critical_field_completeness_score",
            "average_authority_score",
            "average_freshness_score",
            "average_fallback_coverage_score",
            "average_triage_score",
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
        return research_source_scraper_failure_triage_report_payload(self)


def build_research_source_scraper_failure_triage_report(
    inputs: Iterable[ResearchSourceScraperFailureTriageInput],
    *,
    config: ResearchSourceScraperFailureTriageConfig,
    generated_at: datetime,
) -> ResearchSourceScraperFailureTriageReport:
    if type(config) is not ResearchSourceScraperFailureTriageConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScraperFailureTriageConfig",
        )
    config = replace(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")

    provisional_rows = tuple(
        _row_from_input(
            item,
            row_number=index,
            config=config,
            generated_at=generated_at,
        )
        for index, item in enumerate(normalized_inputs, start=1)
    )
    rows = tuple(
        replace(
            row,
            row_label=f"redacted-scraper-failure-triage-{index:06d}",
        )
        for index, row in enumerate(
            sorted(provisional_rows, key=_row_sort_key),
            start=1,
        )
    )
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    return ResearchSourceScraperFailureTriageReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=_add_decimals(watch_count, block_count),
        max_observation_age_seconds=max(
            (row.observation_age_seconds for row in rows),
            default=ZERO,
        ),
        average_failure_rate=_average(row.failure_rate for row in rows),
        average_parse_confidence_score=_average(
            (row.parse_confidence_score for row in rows),
        ),
        average_critical_field_completeness_score=_average(
            (row.critical_field_completeness_score for row in rows),
        ),
        average_authority_score=_average(row.authority_score for row in rows),
        average_freshness_score=_average(row.freshness_score for row in rows),
        average_fallback_coverage_score=_average(
            (row.fallback_coverage_score for row in rows),
        ),
        average_triage_score=_average(row.triage_score for row in rows),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scraper_failure_triage_report_payload(
    report: ResearchSourceScraperFailureTriageReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraperFailureTriageReport:
        raise ValueError(
            "report must be exactly ResearchSourceScraperFailureTriageReport",
        )
    _revalidate_report_instance(report)
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scraper_failure_triage_report_digest(
    report: ResearchSourceScraperFailureTriageReport,
) -> str:
    payload = research_source_scraper_failure_triage_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scraper_failure_triage_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_report_payload_shape(payload)
        _validate_public_payload(payload)
        report = _report_from_public_payload(payload)
        return research_source_scraper_failure_triage_report_payload(report) == payload
    except (KeyError, TypeError, ValueError):
        return False


def _validate_public_report_payload_shape(payload: dict[str, Any]) -> None:
    _require_exact_public_keys("payload", payload, _REPORT_PAYLOAD_FIELDS)

    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain objects")
        _require_exact_public_keys("payload row", row, _ROW_PAYLOAD_FIELDS)

    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("payload reason_code_counts must be a list")
    for reason_count in reason_code_counts:
        if type(reason_count) is not dict:
            raise ValueError("payload reason_code_counts must contain objects")
        _require_exact_public_keys(
            "payload reason count",
            reason_count,
            _REASON_CODE_COUNT_PAYLOAD_FIELDS,
        )


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraperFailureTriageReport:
    return ResearchSourceScraperFailureTriageReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        input_count=_public_decimal("input_count", payload["input_count"]),
        row_count=_public_decimal("row_count", payload["row_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        attention_count=_public_decimal("attention_count", payload["attention_count"]),
        max_observation_age_seconds=_public_decimal(
            "max_observation_age_seconds",
            payload["max_observation_age_seconds"],
        ),
        average_failure_rate=_public_decimal(
            "average_failure_rate",
            payload["average_failure_rate"],
        ),
        average_parse_confidence_score=_public_decimal(
            "average_parse_confidence_score",
            payload["average_parse_confidence_score"],
        ),
        average_critical_field_completeness_score=_public_decimal(
            "average_critical_field_completeness_score",
            payload["average_critical_field_completeness_score"],
        ),
        average_authority_score=_public_decimal(
            "average_authority_score",
            payload["average_authority_score"],
        ),
        average_freshness_score=_public_decimal(
            "average_freshness_score",
            payload["average_freshness_score"],
        ),
        average_fallback_coverage_score=_public_decimal(
            "average_fallback_coverage_score",
            payload["average_fallback_coverage_score"],
        ),
        average_triage_score=_public_decimal(
            "average_triage_score",
            payload["average_triage_score"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=_public_reason_code_counts(payload["reason_code_counts"]),
        rows=_public_rows(payload["rows"]),
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _public_rows(value: Any) -> tuple[ResearchSourceScraperFailureTriageRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    return tuple(
        ResearchSourceScraperFailureTriageRow(
            row_label=_public_string("row_label", row["row_label"]),
            generated_at=_public_datetime("generated_at", row["generated_at"]),
            observed_at=_public_datetime("observed_at", row["observed_at"]),
            authority_tier=_public_string("authority_tier", row["authority_tier"]),
            scrape_attempt_count=_public_decimal(
                "scrape_attempt_count",
                row["scrape_attempt_count"],
            ),
            scrape_failure_count=_public_decimal(
                "scrape_failure_count",
                row["scrape_failure_count"],
            ),
            critical_field_count=_public_decimal(
                "critical_field_count",
                row["critical_field_count"],
            ),
            fallback_available_count=_public_decimal(
                "fallback_available_count",
                row["fallback_available_count"],
            ),
            fallback_required_count=_public_decimal(
                "fallback_required_count",
                row["fallback_required_count"],
            ),
            observation_age_seconds=_public_decimal(
                "observation_age_seconds",
                row["observation_age_seconds"],
            ),
            failure_rate=_public_decimal("failure_rate", row["failure_rate"]),
            failure_resilience_score=_public_decimal(
                "failure_resilience_score",
                row["failure_resilience_score"],
            ),
            parse_confidence_score=_public_decimal(
                "parse_confidence_score",
                row["parse_confidence_score"],
            ),
            critical_field_completeness_score=_public_decimal(
                "critical_field_completeness_score",
                row["critical_field_completeness_score"],
            ),
            authority_score=_public_decimal("authority_score", row["authority_score"]),
            freshness_score=_public_decimal("freshness_score", row["freshness_score"]),
            fallback_coverage_score=_public_decimal(
                "fallback_coverage_score",
                row["fallback_coverage_score"],
            ),
            missing_critical_field_count=_public_decimal(
                "missing_critical_field_count",
                row["missing_critical_field_count"],
            ),
            triage_score=_public_decimal("triage_score", row["triage_score"]),
            status=_public_string("status", row["status"]),
            reason_codes=_public_string_tuple("reason_codes", row["reason_codes"]),
            paper_only=row["paper_only"],
            report_only=row["report_only"],
            readonly=row["readonly"],
        )
        for row in value
    )


def _public_reason_code_counts(
    value: Any,
) -> tuple[ResearchSourceScraperFailureTriageReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    return tuple(
        ResearchSourceScraperFailureTriageReasonCodeCount(
            reason_code=_public_string("reason_code", item["reason_code"]),
            count=_public_decimal("count", item["count"]),
            paper_only=item["paper_only"],
            report_only=item["report_only"],
            readonly=item["readonly"],
        )
        for item in value
    )


def _public_string_tuple(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_public_string(field_name, item) for item in value)


def _public_string(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _public_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _public_datetime(field_name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_exact_public_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(value) != expected_keys:
        raise ValueError(f"{label} fields must match the public schema")


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScraperFailureTriageInput],
) -> tuple[ResearchSourceScraperFailureTriageInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScraperFailureTriageInput:
            raise ValueError(
                "inputs must contain ResearchSourceScraperFailureTriageInput",
            )
    canonical_inputs = tuple(replace(item) for item in normalized)
    return tuple(sorted(canonical_inputs, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScraperFailureTriageInput,
) -> tuple[str, str, Decimal, Decimal, Decimal, Decimal, Decimal, str, Decimal, Decimal]:
    return (
        item.private_collection_ref,
        item.observed_at.isoformat(),
        item.scrape_attempt_count,
        item.scrape_failure_count,
        item.parse_confidence_ratio,
        item.critical_field_count,
        item.missing_critical_field_count,
        item.authority_tier,
        item.fallback_available_count,
        item.fallback_required_count,
    )


def _row_from_input(
    item: ResearchSourceScraperFailureTriageInput,
    *,
    row_number: int,
    config: ResearchSourceScraperFailureTriageConfig,
    generated_at: datetime,
) -> ResearchSourceScraperFailureTriageRow:
    observation_age_seconds = _age_seconds(generated_at, item.observed_at)
    failure_rate = _safe_ratio(item.scrape_failure_count, item.scrape_attempt_count)
    failure_resilience_score = _one_minus(failure_rate)
    freshness_score = _freshness_score(observation_age_seconds, config)
    critical_field_completeness_score = _one_minus(
        _safe_ratio(item.missing_critical_field_count, item.critical_field_count),
    )
    authority_score = _authority_score(item.authority_tier)
    fallback_coverage_score = _safe_ratio(
        item.fallback_available_count,
        item.fallback_required_count,
    )
    triage_score = _triage_score(
        failure_resilience_score=failure_resilience_score,
        parse_confidence_score=item.parse_confidence_ratio,
        critical_field_completeness_score=critical_field_completeness_score,
        authority_score=authority_score,
        freshness_score=freshness_score,
        fallback_coverage_score=fallback_coverage_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        failure_rate=failure_rate,
        observation_age_seconds=observation_age_seconds,
        freshness_score=freshness_score,
        parse_confidence_score=item.parse_confidence_ratio,
        authority_score=authority_score,
        fallback_coverage_score=fallback_coverage_score,
        missing_critical_field_count=item.missing_critical_field_count,
        critical_field_count=item.critical_field_count,
        config=config,
    )
    status = _row_status(reason_codes, triage_score, config)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*reason_codes, _status_reason(status)),
    )
    return ResearchSourceScraperFailureTriageRow(
        row_label=f"redacted-scraper-failure-triage-{row_number:06d}",
        generated_at=generated_at,
        observed_at=item.observed_at,
        authority_tier=item.authority_tier,
        scrape_attempt_count=item.scrape_attempt_count,
        scrape_failure_count=item.scrape_failure_count,
        critical_field_count=item.critical_field_count,
        fallback_available_count=item.fallback_available_count,
        fallback_required_count=item.fallback_required_count,
        observation_age_seconds=observation_age_seconds,
        failure_rate=failure_rate,
        failure_resilience_score=failure_resilience_score,
        parse_confidence_score=item.parse_confidence_ratio,
        critical_field_completeness_score=critical_field_completeness_score,
        authority_score=authority_score,
        freshness_score=freshness_score,
        fallback_coverage_score=fallback_coverage_score,
        missing_critical_field_count=item.missing_critical_field_count,
        triage_score=triage_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _freshness_score(
    observation_age_seconds: Decimal,
    config: ResearchSourceScraperFailureTriageConfig,
) -> Decimal:
    if observation_age_seconds <= config.fresh_observation_max_age_seconds:
        return ONE
    if observation_age_seconds >= config.stale_observation_block_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        stale_window = (
            config.stale_observation_block_age_seconds
            - config.fresh_observation_max_age_seconds
        )
        stale_progress = _safe_ratio(
            observation_age_seconds - config.fresh_observation_max_age_seconds,
            stale_window,
        )
        return (ONE - stale_progress).quantize(QUANTUM)


def _authority_score(authority_tier: str) -> Decimal:
    try:
        return AUTHORITY_TIER_SCORES[authority_tier]
    except KeyError as exc:
        raise ValueError("authority_tier must be a supported tier") from exc


def _row_reason_codes(
    *,
    failure_rate: Decimal,
    observation_age_seconds: Decimal,
    freshness_score: Decimal,
    parse_confidence_score: Decimal,
    authority_score: Decimal,
    fallback_coverage_score: Decimal,
    missing_critical_field_count: Decimal,
    critical_field_count: Decimal,
    config: ResearchSourceScraperFailureTriageConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if failure_rate > config.max_failure_rate_watch_ratio:
        reason_codes.append("failure_rate_block")
    elif failure_rate > config.max_failure_rate_pass_ratio:
        reason_codes.append("failure_rate_watch")

    if observation_age_seconds >= config.stale_observation_block_age_seconds:
        reason_codes.append("freshness_block")
    elif freshness_score < ONE:
        reason_codes.append("freshness_watch")

    if parse_confidence_score < config.min_parse_confidence_watch_ratio:
        reason_codes.append("parse_confidence_block")
    elif parse_confidence_score < config.min_parse_confidence_pass_ratio:
        reason_codes.append("parse_confidence_watch")

    if authority_score < AUTHORITY_TIER_WATCH_SCORE:
        reason_codes.append("authority_tier_block")
    elif authority_score < AUTHORITY_TIER_PASS_SCORE:
        reason_codes.append("authority_tier_watch")

    if fallback_coverage_score < config.min_fallback_coverage_watch_ratio:
        reason_codes.append("fallback_coverage_block")
    elif fallback_coverage_score < config.min_fallback_coverage_pass_ratio:
        reason_codes.append("fallback_coverage_watch")

    if missing_critical_field_count == critical_field_count:
        reason_codes.append("critical_fields_missing_block")
    elif missing_critical_field_count > ZERO:
        reason_codes.append("critical_fields_missing_watch")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(
    reason_codes: tuple[str, ...],
    triage_score: Decimal,
    config: ResearchSourceScraperFailureTriageConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if triage_score < config.min_triage_watch_score:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if triage_score < config.min_triage_pass_score:
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


def _report_status(rows: tuple[ResearchSourceScraperFailureTriageRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraperFailureTriageRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceScraperFailureTriageRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScraperFailureTriageReasonCodeCount, ...]:
    counts = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    for reason_code in reason_codes:
        if counts[reason_code] == 0:
            counts[reason_code] = 1
    return tuple(
        ResearchSourceScraperFailureTriageReasonCodeCount(
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
    rows: tuple[ResearchSourceScraperFailureTriageRow, ...],
) -> tuple[ResearchSourceScraperFailureTriageRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraperFailureTriageRow:
            raise ValueError("rows must contain ResearchSourceScraperFailureTriageRow")
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceScraperFailureTriageRow,
) -> tuple[object, ...]:
    return (
        STATUS_WEIGHT[row.status],
        row.triage_score,
        row.failure_resilience_score,
        row.parse_confidence_score,
        row.critical_field_completeness_score,
        row.authority_score,
        row.freshness_score,
        row.fallback_coverage_score,
        row.observation_age_seconds,
        row.missing_critical_field_count,
        row.generated_at.isoformat(),
        row.observed_at.isoformat(),
        row.scrape_attempt_count,
        row.scrape_failure_count,
        row.critical_field_count,
        row.fallback_available_count,
        row.fallback_required_count,
        row.authority_tier,
        row.reason_codes,
        row.row_label,
    )


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraperFailureTriageReasonCodeCount, ...],
) -> tuple[ResearchSourceScraperFailureTriageReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceScraperFailureTriageReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraperFailureTriageReasonCodeCount",
            )
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_report_consistency(
    report: ResearchSourceScraperFailureTriageReport,
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
    if report.attention_count != _add_decimals(
        report.watch_count,
        report.block_count,
    ):
        raise ValueError("attention_count must match watch and block counts")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows and status")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match reason_codes")
    expected_row_labels = tuple(
        f"redacted-scraper-failure-triage-{index:06d}"
        for index in range(1, len(report.rows) + 1)
    )
    if tuple(row.row_label for row in report.rows) != expected_row_labels:
        raise ValueError("row_label values must match the canonical row sequence")
    if any(row.generated_at != report.generated_at for row in report.rows):
        raise ValueError("row generated_at values must match report generated_at")
    if report.max_observation_age_seconds != max(
        (row.observation_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observation_age_seconds must match rows")
    expected_averages = {
        "average_failure_rate": _average(row.failure_rate for row in report.rows),
        "average_parse_confidence_score": _average(
            (row.parse_confidence_score for row in report.rows),
        ),
        "average_critical_field_completeness_score": _average(
            (row.critical_field_completeness_score for row in report.rows),
        ),
        "average_authority_score": _average(row.authority_score for row in report.rows),
        "average_freshness_score": _average(row.freshness_score for row in report.rows),
        "average_fallback_coverage_score": _average(
            (row.fallback_coverage_score for row in report.rows),
        ),
        "average_triage_score": _average(row.triage_score for row in report.rows),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _validate_row_consistency(
    row: ResearchSourceScraperFailureTriageRow,
) -> None:
    config = ResearchSourceScraperFailureTriageConfig()
    expected_observation_age_seconds = _age_seconds(
        row.generated_at,
        row.observed_at,
    )
    if row.observation_age_seconds != expected_observation_age_seconds:
        raise ValueError("observation_age_seconds must match timestamps")
    expected_failure_rate = _safe_ratio(
        row.scrape_failure_count,
        row.scrape_attempt_count,
    )
    if row.failure_rate != expected_failure_rate:
        raise ValueError("failure_rate must match scrape counts")
    if row.failure_resilience_score != _one_minus(row.failure_rate):
        raise ValueError("failure_resilience_score must match failure_rate")
    if row.authority_score != _authority_score(row.authority_tier):
        raise ValueError("authority_score must match authority_tier")
    expected_freshness_score = _freshness_score(
        row.observation_age_seconds,
        config,
    )
    if row.freshness_score != expected_freshness_score:
        raise ValueError("freshness_score must match observation_age_seconds")
    expected_critical_field_completeness_score = _one_minus(
        _safe_ratio(
            row.missing_critical_field_count,
            row.critical_field_count,
        ),
    )
    if (
        row.critical_field_completeness_score
        != expected_critical_field_completeness_score
    ):
        raise ValueError(
            "critical_field_completeness_score must match critical field counts",
        )
    expected_fallback_coverage_score = _safe_ratio(
        row.fallback_available_count,
        row.fallback_required_count,
    )
    if row.fallback_coverage_score != expected_fallback_coverage_score:
        raise ValueError("fallback_coverage_score must match fallback counts")
    expected_triage_score = _triage_score(
        failure_resilience_score=row.failure_resilience_score,
        parse_confidence_score=row.parse_confidence_score,
        critical_field_completeness_score=row.critical_field_completeness_score,
        authority_score=row.authority_score,
        freshness_score=row.freshness_score,
        fallback_coverage_score=row.fallback_coverage_score,
        config=config,
    )
    if row.triage_score != expected_triage_score:
        raise ValueError("triage_score must match component scores")
    expected_detail_reasons = _row_reason_codes(
        failure_rate=row.failure_rate,
        observation_age_seconds=row.observation_age_seconds,
        freshness_score=row.freshness_score,
        parse_confidence_score=row.parse_confidence_score,
        authority_score=row.authority_score,
        fallback_coverage_score=row.fallback_coverage_score,
        missing_critical_field_count=row.missing_critical_field_count,
        critical_field_count=row.critical_field_count,
        config=config,
    )
    expected_status = _row_status(
        expected_detail_reasons,
        row.triage_score,
        config,
    )
    if row.status != expected_status:
        raise ValueError("status must match derived row values")
    expected_reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*expected_detail_reasons, _status_reason(expected_status)),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match derived row values")


def _revalidate_report_instance(
    report: ResearchSourceScraperFailureTriageReport,
) -> None:
    canonical_rows = tuple(replace(row) for row in report.rows)
    canonical_reason_code_counts = tuple(
        replace(reason_count) for reason_count in report.reason_code_counts
    )
    replace(
        report,
        rows=canonical_rows,
        reason_code_counts=canonical_reason_code_counts,
    )


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
    with localcontext(DECIMAL_CONTEXT):
        return _safe_ratio(
            sum(normalized, ZERO),
            _count_decimal(len(normalized)),
        )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / MICROSECOND_DIVISOR,
        )


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _add_decimals(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left + right).quantize(QUANTUM)


def _sum_quantized(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _one_minus(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (ONE - value).quantize(QUANTUM)


def _triage_score(
    *,
    failure_resilience_score: Decimal,
    parse_confidence_score: Decimal,
    critical_field_completeness_score: Decimal,
    authority_score: Decimal,
    freshness_score: Decimal,
    fallback_coverage_score: Decimal,
    config: ResearchSourceScraperFailureTriageConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            failure_resilience_score * config.failure_rate_weight
            + parse_confidence_score * config.parse_confidence_weight
            + critical_field_completeness_score * config.critical_field_weight
            + authority_score * config.authority_weight
            + freshness_score * config.freshness_weight
            + fallback_coverage_score * config.fallback_coverage_weight
        ).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _normalize_decimal(field_name, raw_value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _normalize_decimal(field_name, raw_value)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        is_integral = raw_value == raw_value.to_integral_value()
    if not is_integral:
        raise ValueError(f"{field_name} must be a whole number")
    return _normalize_decimal(field_name, raw_value)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _normalize_decimal(field_name, raw_value)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    normalized = _quantize(value)
    if normalized.is_zero():
        return ZERO
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use negative zero")
    return value


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


def _require_private_string(field_name: str, value: str) -> None:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_identifier(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)


def _require_row_label(value: str) -> None:
    if type(value) is not str or ROW_LABEL_RE.fullmatch(value) is None:
        raise ValueError("row_label must match the canonical redacted label format")
    _reject_unsafe_public_text("row_label", value)


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: str) -> None:
    _require_member(field_name, value, STATUSES)


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    _reject_unsafe_public_text(field_name, value)


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _report_digest(report: ResearchSourceScraperFailureTriageReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _validate_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (int, float):
        raise ValueError("JSON value must not contain raw numeric values")
    if type(value) in (str, bool):
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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    ready = _json_ready(
        asdict(value) if is_dataclass(value) and not isinstance(value, type) else value,
    )
    _validate_public_payload(ready, label=label)


def _validate_public_payload(value: Any, *, label: str = "payload") -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _validate_public_payload(item, label=key)
        return
    if type(value) is list:
        for item in value:
            _validate_public_payload(item, label=label)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must not expose raw numeric values")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.casefold()
    if (
        any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
        or UNSAFE_PUBLIC_STANDALONE_RE.search(lowered) is not None
    ):
        raise ValueError(f"{label} has unsafe public surface")
