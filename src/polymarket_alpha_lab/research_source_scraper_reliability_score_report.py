"""Pure report-only source scraper reliability score reducer.

Callers provide already-sanitized collection telemetry from tools such as
Scrapling or agent-reach. This module performs no network access and returns a
deterministic public report with redacted row labels, Decimal-only numerics, and
SHA-256 digest validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPER_RELIABILITY_SCORE_REPORT_CONFIG_VERSION = (
    "research-source-scraper-reliability-score-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
COLLECTOR_FAMILIES = ("agent_reach", "generic", "scrapling")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "scraper_reliability_no_inputs"
PASS_REASON = "scraper_reliability_pass"
WATCH_REASON = "scraper_reliability_watch"
BLOCK_REASON = "scraper_reliability_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "success_rate_block",
    "success_rate_watch",
    "freshness_block",
    "freshness_watch",
    "parser_confidence_block",
    "parser_confidence_watch",
    "authority_block",
    "authority_watch",
    "duplicate_corroboration_block",
    "duplicate_corroboration_watch",
    "critical_fields_missing_block",
    "critical_fields_missing_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
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
    "table",
    "token",
    "api_key",
    "secret",
    "password",
    "credential",
    "bearer",
    "authentication",
    "authorization",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommendation",
    "execution",
    "execute",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPER_RELIABILITY_SCORE_REPORT_CONFIG_VERSION",
    "ResearchSourceScraperReliabilityScoreConfig",
    "ResearchSourceScraperReliabilityScoreInput",
    "ResearchSourceScraperReliabilityScoreReasonCodeCount",
    "ResearchSourceScraperReliabilityScoreReport",
    "ResearchSourceScraperReliabilityScoreRow",
    "STATUSES",
    "build_research_source_scraper_reliability_score_report",
    "research_source_scraper_reliability_score_report_digest",
    "research_source_scraper_reliability_score_report_payload",
    "validate_research_source_scraper_reliability_score_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraperReliabilityScoreConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPER_RELIABILITY_SCORE_REPORT_CONFIG_VERSION
    )
    fresh_collection_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_collection_block_age_seconds: Decimal = Decimal("86400.000000")
    min_success_rate_pass_ratio: Decimal = Decimal("0.900000")
    min_success_rate_watch_ratio: Decimal = Decimal("0.650000")
    min_parser_confidence_pass_ratio: Decimal = Decimal("0.850000")
    min_parser_confidence_watch_ratio: Decimal = Decimal("0.600000")
    min_authority_pass_ratio: Decimal = Decimal("0.800000")
    min_authority_watch_ratio: Decimal = Decimal("0.500000")
    min_reliability_pass_score: Decimal = Decimal("0.800000")
    min_reliability_watch_score: Decimal = Decimal("0.500000")
    success_rate_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    parser_confidence_weight: Decimal = Decimal("0.200000")
    authority_weight: Decimal = Decimal("0.150000")
    corroboration_weight: Decimal = Decimal("0.100000")
    completeness_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperReliabilityScoreConfig:
            raise TypeError(
                "ResearchSourceScraperReliabilityScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperReliabilityScoreConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPER_RELIABILITY_SCORE_REPORT_CONFIG_VERSION
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
            "min_success_rate_pass_ratio",
            "min_success_rate_watch_ratio",
            "min_parser_confidence_pass_ratio",
            "min_parser_confidence_watch_ratio",
            "min_authority_pass_ratio",
            "min_authority_watch_ratio",
            "min_reliability_pass_score",
            "min_reliability_watch_score",
            "success_rate_weight",
            "freshness_weight",
            "parser_confidence_weight",
            "authority_weight",
            "corroboration_weight",
            "completeness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.min_success_rate_watch_ratio > self.min_success_rate_pass_ratio:
            raise ValueError("success rate watch threshold must not exceed pass threshold")
        if (
            self.min_parser_confidence_watch_ratio
            > self.min_parser_confidence_pass_ratio
        ):
            raise ValueError(
                "parser confidence watch threshold must not exceed pass threshold",
            )
        if self.min_authority_watch_ratio > self.min_authority_pass_ratio:
            raise ValueError("authority watch threshold must not exceed pass threshold")
        if self.min_reliability_watch_score > self.min_reliability_pass_score:
            raise ValueError("reliability watch threshold must not exceed pass threshold")
        weight_sum = _quantize(
            self.success_rate_weight
            + self.freshness_weight
            + self.parser_confidence_weight
            + self.authority_weight
            + self.corroboration_weight
            + self.completeness_weight,
        )
        if weight_sum != ONE:
            raise ValueError("reliability score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraperReliabilityScoreInput:
    private_collection_ref: str
    collector_family: str
    collected_at: datetime
    scraper_attempt_count: Decimal
    scraper_success_count: Decimal
    parser_confidence_ratio: Decimal
    authority_score: Decimal
    duplicate_corroboration_count: Decimal
    required_corroboration_count: Decimal
    critical_field_count: Decimal
    missing_critical_field_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperReliabilityScoreInput:
            raise TypeError(
                "ResearchSourceScraperReliabilityScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperReliabilityScoreInput, "input")
        _require_private_string("private_collection_ref", self.private_collection_ref)
        _require_member("collector_family", self.collector_family, COLLECTOR_FAMILIES)
        object.__setattr__(self, "collected_at", _as_utc("collected_at", self.collected_at))
        for field_name in (
            "scraper_attempt_count",
            "scraper_success_count",
            "duplicate_corroboration_count",
            "missing_critical_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("required_corroboration_count", "critical_field_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("parser_confidence_ratio", "authority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.scraper_attempt_count == ZERO:
            raise ValueError("scraper_attempt_count must be positive")
        if self.scraper_success_count > self.scraper_attempt_count:
            raise ValueError("scraper_success_count must not exceed scraper_attempt_count")
        if self.missing_critical_field_count > self.critical_field_count:
            raise ValueError(
                "missing_critical_field_count must not exceed critical_field_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraperReliabilityScoreRow:
    row_label: str
    collector_family: str
    collection_age_seconds: Decimal
    success_rate: Decimal
    freshness_score: Decimal
    parser_confidence_score: Decimal
    authority_score: Decimal
    duplicate_corroboration_score: Decimal
    critical_field_completeness_score: Decimal
    missing_critical_field_count: Decimal
    reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperReliabilityScoreRow:
            raise TypeError(
                "ResearchSourceScraperReliabilityScoreRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperReliabilityScoreRow, "row")
        _require_public_identifier("row_label", self.row_label)
        _require_member("collector_family", self.collector_family, COLLECTOR_FAMILIES)
        object.__setattr__(
            self,
            "collection_age_seconds",
            _normalize_nonnegative_decimal(
                "collection_age_seconds",
                self.collection_age_seconds,
            ),
        )
        for field_name in (
            "success_rate",
            "freshness_score",
            "parser_confidence_score",
            "authority_score",
            "duplicate_corroboration_score",
            "critical_field_completeness_score",
            "reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_critical_field_count",
            _normalize_nonnegative_count(
                "missing_critical_field_count",
                self.missing_critical_field_count,
            ),
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
class ResearchSourceScraperReliabilityScoreReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperReliabilityScoreReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraperReliabilityScoreReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraperReliabilityScoreReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraperReliabilityScoreReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_collection_age_seconds: Decimal
    average_success_rate: Decimal
    average_freshness_score: Decimal
    average_parser_confidence_score: Decimal
    average_authority_score: Decimal
    average_duplicate_corroboration_score: Decimal
    average_critical_field_completeness_score: Decimal
    average_reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraperReliabilityScoreReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraperReliabilityScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperReliabilityScoreReport:
            raise TypeError(
                "ResearchSourceScraperReliabilityScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperReliabilityScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
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
            "max_collection_age_seconds",
            _normalize_nonnegative_decimal(
                "max_collection_age_seconds",
                self.max_collection_age_seconds,
            ),
        )
        for field_name in (
            "average_success_rate",
            "average_freshness_score",
            "average_parser_confidence_score",
            "average_authority_score",
            "average_duplicate_corroboration_score",
            "average_critical_field_completeness_score",
            "average_reliability_score",
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
        return research_source_scraper_reliability_score_report_payload(self)


def build_research_source_scraper_reliability_score_report(
    inputs: Iterable[ResearchSourceScraperReliabilityScoreInput],
    *,
    config: ResearchSourceScraperReliabilityScoreConfig,
    generated_at: datetime,
) -> ResearchSourceScraperReliabilityScoreReport:
    if type(config) is not ResearchSourceScraperReliabilityScoreConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScraperReliabilityScoreConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.collected_at > generated_at:
            raise ValueError("collected_at cannot be after generated_at")

    rows = tuple(
        _row_from_input(
            item,
            row_number=index,
            config=config,
            generated_at=generated_at,
        )
        for index, item in enumerate(normalized_inputs, start=1)
    )
    input_count = _count_decimal(len(normalized_inputs))
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    attention_count = watch_count + block_count
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    return ResearchSourceScraperReliabilityScoreReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=attention_count,
        max_collection_age_seconds=max(
            (row.collection_age_seconds for row in rows),
            default=ZERO,
        ),
        average_success_rate=_average(row.success_rate for row in rows),
        average_freshness_score=_average(row.freshness_score for row in rows),
        average_parser_confidence_score=_average(
            (row.parser_confidence_score for row in rows),
        ),
        average_authority_score=_average(row.authority_score for row in rows),
        average_duplicate_corroboration_score=_average(
            (row.duplicate_corroboration_score for row in rows),
        ),
        average_critical_field_completeness_score=_average(
            (row.critical_field_completeness_score for row in rows),
        ),
        average_reliability_score=_average(row.reliability_score for row in rows),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scraper_reliability_score_report_payload(
    report: ResearchSourceScraperReliabilityScoreReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraperReliabilityScoreReport:
        raise ValueError(
            "report must be exactly ResearchSourceScraperReliabilityScoreReport",
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


def research_source_scraper_reliability_score_report_digest(
    report: ResearchSourceScraperReliabilityScoreReport,
) -> str:
    payload = research_source_scraper_reliability_score_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scraper_reliability_score_report_payload(
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
        if sha256(encoded).hexdigest() != digest:
            return False
        report = _report_from_payload(payload)
        return research_source_scraper_reliability_score_report_payload(report) == payload
    except (KeyError, TypeError, ValueError):
        return False


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraperReliabilityScoreReport:
    _require_payload_keys(
        "report payload",
        payload,
        ResearchSourceScraperReliabilityScoreReport,
    )
    return ResearchSourceScraperReliabilityScoreReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        input_count=_payload_decimal("input_count", payload["input_count"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        attention_count=_payload_decimal("attention_count", payload["attention_count"]),
        max_collection_age_seconds=_payload_decimal(
            "max_collection_age_seconds",
            payload["max_collection_age_seconds"],
        ),
        average_success_rate=_payload_decimal(
            "average_success_rate",
            payload["average_success_rate"],
        ),
        average_freshness_score=_payload_decimal(
            "average_freshness_score",
            payload["average_freshness_score"],
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
        average_critical_field_completeness_score=_payload_decimal(
            "average_critical_field_completeness_score",
            payload["average_critical_field_completeness_score"],
        ),
        average_reliability_score=_payload_decimal(
            "average_reliability_score",
            payload["average_reliability_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=_payload_tuple(
            "reason_code_counts",
            payload["reason_code_counts"],
            _reason_code_count_from_payload,
        ),
        rows=_payload_tuple("rows", payload["rows"], _row_from_payload),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_payload(payload: dict[str, Any]) -> ResearchSourceScraperReliabilityScoreRow:
    _require_payload_keys("row payload", payload, ResearchSourceScraperReliabilityScoreRow)
    return ResearchSourceScraperReliabilityScoreRow(
        row_label=_payload_string("row_label", payload["row_label"]),
        collector_family=_payload_string("collector_family", payload["collector_family"]),
        collection_age_seconds=_payload_decimal(
            "collection_age_seconds",
            payload["collection_age_seconds"],
        ),
        success_rate=_payload_decimal("success_rate", payload["success_rate"]),
        freshness_score=_payload_decimal("freshness_score", payload["freshness_score"]),
        parser_confidence_score=_payload_decimal(
            "parser_confidence_score",
            payload["parser_confidence_score"],
        ),
        authority_score=_payload_decimal("authority_score", payload["authority_score"]),
        duplicate_corroboration_score=_payload_decimal(
            "duplicate_corroboration_score",
            payload["duplicate_corroboration_score"],
        ),
        critical_field_completeness_score=_payload_decimal(
            "critical_field_completeness_score",
            payload["critical_field_completeness_score"],
        ),
        missing_critical_field_count=_payload_decimal(
            "missing_critical_field_count",
            payload["missing_critical_field_count"],
        ),
        reliability_score=_payload_decimal(
            "reliability_score",
            payload["reliability_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _reason_code_count_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceScraperReliabilityScoreReasonCodeCount:
    _require_payload_keys(
        "reason code count payload",
        payload,
        ResearchSourceScraperReliabilityScoreReasonCodeCount,
    )
    return ResearchSourceScraperReliabilityScoreReasonCodeCount(
        reason_code=_payload_string("reason_code", payload["reason_code"]),
        count=_payload_decimal("count", payload["count"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _payload_tuple(
    field_name: str,
    value: Any,
    item_parser: Any,
) -> tuple[Any, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(item_parser(item) for item in value)


def _payload_string_tuple(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_string(field_name, item) for item in value)


def _payload_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    return Decimal(value)


def _payload_datetime(field_name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    return datetime.fromisoformat(value)


def _payload_string(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: Any) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_payload_keys(
    label: str,
    payload: Any,
    dataclass_type: type[object],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    expected_keys = {field.name for field in fields(dataclass_type)}
    if set(payload) != expected_keys:
        raise ValueError(f"{label} must match the report schema")


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScraperReliabilityScoreInput],
) -> tuple[ResearchSourceScraperReliabilityScoreInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScraperReliabilityScoreInput:
            raise ValueError(
                "inputs must contain ResearchSourceScraperReliabilityScoreInput",
            )
        _require_hard_flags("input", item)
    return tuple(sorted(normalized, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScraperReliabilityScoreInput,
) -> tuple[str, str, str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        item.private_collection_ref,
        item.collector_family,
        item.collected_at.isoformat(),
        item.scraper_attempt_count,
        item.scraper_success_count,
        item.parser_confidence_ratio,
        item.authority_score,
        item.duplicate_corroboration_count,
        item.required_corroboration_count,
        item.critical_field_count,
        item.missing_critical_field_count,
    )


def _row_from_input(
    item: ResearchSourceScraperReliabilityScoreInput,
    *,
    row_number: int,
    config: ResearchSourceScraperReliabilityScoreConfig,
    generated_at: datetime,
) -> ResearchSourceScraperReliabilityScoreRow:
    collection_age_seconds = _age_seconds(generated_at, item.collected_at)
    success_rate = _safe_ratio(item.scraper_success_count, item.scraper_attempt_count)
    freshness_score = _freshness_score(collection_age_seconds, config)
    duplicate_corroboration_score = min(
        ONE,
        _safe_ratio(
            item.duplicate_corroboration_count,
            item.required_corroboration_count,
        ),
    )
    completeness_score = _quantize(
        ONE - _safe_ratio(item.missing_critical_field_count, item.critical_field_count),
    )
    reliability_score = _quantize(
        success_rate * config.success_rate_weight
        + freshness_score * config.freshness_weight
        + item.parser_confidence_ratio * config.parser_confidence_weight
        + item.authority_score * config.authority_weight
        + duplicate_corroboration_score * config.corroboration_weight
        + completeness_score * config.completeness_weight,
    )
    reason_codes = _row_reason_codes(
        success_rate=success_rate,
        freshness_score=freshness_score,
        collection_age_seconds=collection_age_seconds,
        parser_confidence_score=item.parser_confidence_ratio,
        authority_score=item.authority_score,
        duplicate_corroboration_score=duplicate_corroboration_score,
        missing_critical_field_count=item.missing_critical_field_count,
        critical_field_count=item.critical_field_count,
        reliability_score=reliability_score,
        config=config,
    )
    status = _row_status(reason_codes, reliability_score, config)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*reason_codes, _status_reason(status)),
    )
    return ResearchSourceScraperReliabilityScoreRow(
        row_label=f"redacted-scraper-reliability-{row_number:06d}",
        collector_family=item.collector_family,
        collection_age_seconds=collection_age_seconds,
        success_rate=success_rate,
        freshness_score=freshness_score,
        parser_confidence_score=item.parser_confidence_ratio,
        authority_score=item.authority_score,
        duplicate_corroboration_score=duplicate_corroboration_score,
        critical_field_completeness_score=completeness_score,
        missing_critical_field_count=item.missing_critical_field_count,
        reliability_score=reliability_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _freshness_score(
    collection_age_seconds: Decimal,
    config: ResearchSourceScraperReliabilityScoreConfig,
) -> Decimal:
    if collection_age_seconds <= config.fresh_collection_max_age_seconds:
        return ONE
    if collection_age_seconds >= config.stale_collection_block_age_seconds:
        return ZERO
    stale_window = (
        config.stale_collection_block_age_seconds
        - config.fresh_collection_max_age_seconds
    )
    stale_progress = _safe_ratio(
        collection_age_seconds - config.fresh_collection_max_age_seconds,
        stale_window,
    )
    return _quantize(ONE - stale_progress)


def _row_reason_codes(
    *,
    success_rate: Decimal,
    freshness_score: Decimal,
    collection_age_seconds: Decimal,
    parser_confidence_score: Decimal,
    authority_score: Decimal,
    duplicate_corroboration_score: Decimal,
    missing_critical_field_count: Decimal,
    critical_field_count: Decimal,
    reliability_score: Decimal,
    config: ResearchSourceScraperReliabilityScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if success_rate < config.min_success_rate_watch_ratio:
        reason_codes.append("success_rate_block")
    elif success_rate < config.min_success_rate_pass_ratio:
        reason_codes.append("success_rate_watch")

    if collection_age_seconds >= config.stale_collection_block_age_seconds:
        reason_codes.append("freshness_block")
    elif freshness_score < ONE:
        reason_codes.append("freshness_watch")

    if parser_confidence_score < config.min_parser_confidence_watch_ratio:
        reason_codes.append("parser_confidence_block")
    elif parser_confidence_score < config.min_parser_confidence_pass_ratio:
        reason_codes.append("parser_confidence_watch")

    if authority_score < config.min_authority_watch_ratio:
        reason_codes.append("authority_block")
    elif authority_score < config.min_authority_pass_ratio:
        reason_codes.append("authority_watch")

    if duplicate_corroboration_score < Decimal("0.500000"):
        reason_codes.append("duplicate_corroboration_block")
    elif duplicate_corroboration_score < ONE:
        reason_codes.append("duplicate_corroboration_watch")

    if missing_critical_field_count == critical_field_count:
        reason_codes.append("critical_fields_missing_block")
    elif missing_critical_field_count > ZERO:
        reason_codes.append("critical_fields_missing_watch")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(
    reason_codes: tuple[str, ...],
    reliability_score: Decimal,
    config: ResearchSourceScraperReliabilityScoreConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reliability_score < config.min_reliability_watch_score:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if reliability_score < config.min_reliability_pass_score:
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


def _report_status(rows: tuple[ResearchSourceScraperReliabilityScoreRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraperReliabilityScoreRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceScraperReliabilityScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScraperReliabilityScoreReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    if rows:
        for row in rows:
            counts.update(row.reason_codes)
    else:
        counts.update(reason_codes)
    return tuple(
        ResearchSourceScraperReliabilityScoreReasonCodeCount(
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
    rows: tuple[ResearchSourceScraperReliabilityScoreRow, ...],
) -> tuple[ResearchSourceScraperReliabilityScoreRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraperReliabilityScoreRow:
            raise ValueError("rows must contain ResearchSourceScraperReliabilityScoreRow")
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceScraperReliabilityScoreRow,
) -> tuple[int, str, str]:
    return (STATUS_WEIGHT[row.status], row.row_label, row.collector_family)


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraperReliabilityScoreReasonCodeCount, ...],
) -> tuple[ResearchSourceScraperReliabilityScoreReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceScraperReliabilityScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraperReliabilityScoreReasonCodeCount",
            )
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_report_consistency(
    report: ResearchSourceScraperReliabilityScoreReport,
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
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.max_collection_age_seconds != max(
        (row.collection_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_collection_age_seconds must match rows")
    expected_averages = {
        "average_success_rate": _average(row.success_rate for row in report.rows),
        "average_freshness_score": _average(row.freshness_score for row in report.rows),
        "average_parser_confidence_score": _average(
            (row.parser_confidence_score for row in report.rows),
        ),
        "average_authority_score": _average(row.authority_score for row in report.rows),
        "average_duplicate_corroboration_score": _average(
            (row.duplicate_corroboration_score for row in report.rows),
        ),
        "average_critical_field_completeness_score": _average(
            (row.critical_field_completeness_score for row in report.rows),
        ),
        "average_reliability_score": _average(row.reliability_score for row in report.rows),
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


def _age_seconds(generated_at: datetime, collected_at: datetime) -> Decimal:
    delta = generated_at - collected_at
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
        raise ValueError(f"{field_name} must be a whole number")
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


def _require_private_string(field_name: str, value: str) -> None:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_identifier(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)


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


def _report_digest(report: ResearchSourceScraperReliabilityScoreReport) -> str:
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
    ready = _json_ready(asdict(value) if is_dataclass(value) and not isinstance(value, type) else value)
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
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public surface")
