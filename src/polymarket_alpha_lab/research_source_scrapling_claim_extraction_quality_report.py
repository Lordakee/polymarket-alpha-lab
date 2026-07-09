"""Pure report-only Scrapling claim extraction quality reducer.

Callers provide already-sanitized extraction telemetry. This module performs no
database, network, wallet, order, sizing, auth, or trading work and exposes only
a deterministic public report with redacted row labels, Decimal-only numerics,
and SHA-256 digest validation.
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


DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_EXTRACTION_QUALITY_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-claim-extraction-quality-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "scrapling_claim_extraction_no_inputs"
PASS_REASON = "scrapling_claim_extraction_quality_pass"
WATCH_REASON = "scrapling_claim_extraction_quality_watch"
BLOCK_REASON = "scrapling_claim_extraction_quality_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "extraction_success_rate_block",
    "extraction_success_rate_watch",
    "extraction_age_block",
    "extraction_age_watch",
    "claim_acceptance_rate_block",
    "claim_acceptance_rate_watch",
    "required_field_coverage_block",
    "required_field_coverage_watch",
    "parser_confidence_block",
    "parser_confidence_watch",
    "normalization_block",
    "normalization_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "duplicate_pressure_block",
    "duplicate_pressure_watch",
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
    "sizing",
    "recommend",
)

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "max_extraction_age_seconds",
        "average_extraction_success_rate",
        "average_extraction_freshness_score",
        "average_claim_acceptance_rate",
        "average_required_field_coverage_rate",
        "average_parser_confidence_score",
        "average_normalization_score",
        "average_contradiction_pressure_score",
        "average_duplicate_pressure_score",
        "average_extraction_quality_score",
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
REPORT_PAYLOAD_UNSIGNED_KEYS = REPORT_PAYLOAD_KEYS - frozenset(
    ("derived_validation_digest",),
)
REPORT_COUNT_PAYLOAD_FIELDS = (
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
)
REPORT_AVERAGE_PAYLOAD_FIELDS = (
    "average_extraction_success_rate",
    "average_extraction_freshness_score",
    "average_claim_acceptance_rate",
    "average_required_field_coverage_rate",
    "average_parser_confidence_score",
    "average_normalization_score",
    "average_contradiction_pressure_score",
    "average_duplicate_pressure_score",
    "average_extraction_quality_score",
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "row_label",
        "extraction_age_seconds",
        "extraction_success_rate",
        "extraction_freshness_score",
        "claim_acceptance_rate",
        "required_field_coverage_rate",
        "parser_confidence_score",
        "normalization_score",
        "contradiction_pressure_score",
        "duplicate_pressure_score",
        "extraction_quality_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
STATUS_REASON_CODES = frozenset((PASS_REASON, WATCH_REASON, BLOCK_REASON))

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_EXTRACTION_QUALITY_REPORT_CONFIG_VERSION",
    "ResearchSourceScraplingClaimExtractionQualityConfig",
    "ResearchSourceScraplingClaimExtractionQualityInput",
    "ResearchSourceScraplingClaimExtractionQualityReasonCodeCount",
    "ResearchSourceScraplingClaimExtractionQualityReport",
    "ResearchSourceScraplingClaimExtractionQualityRow",
    "STATUSES",
    "build_research_source_scrapling_claim_extraction_quality_report",
    "research_source_scrapling_claim_extraction_quality_report_digest",
    "research_source_scrapling_claim_extraction_quality_report_payload",
    "validate_research_source_scrapling_claim_extraction_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimExtractionQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_EXTRACTION_QUALITY_REPORT_CONFIG_VERSION
    )
    fresh_extraction_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_extraction_block_age_seconds: Decimal = Decimal("86400.000000")
    min_extraction_success_pass_ratio: Decimal = Decimal("0.900000")
    min_extraction_success_watch_ratio: Decimal = Decimal("0.650000")
    min_claim_acceptance_pass_ratio: Decimal = Decimal("0.800000")
    min_claim_acceptance_watch_ratio: Decimal = Decimal("0.500000")
    min_required_field_coverage_pass_ratio: Decimal = Decimal("0.900000")
    min_required_field_coverage_watch_ratio: Decimal = Decimal("0.700000")
    min_parser_confidence_pass_ratio: Decimal = Decimal("0.850000")
    min_parser_confidence_watch_ratio: Decimal = Decimal("0.600000")
    min_normalization_pass_ratio: Decimal = Decimal("0.850000")
    min_normalization_watch_ratio: Decimal = Decimal("0.600000")
    max_contradiction_watch_pressure: Decimal = Decimal("0.100000")
    max_contradiction_block_pressure: Decimal = Decimal("0.250000")
    max_duplicate_watch_pressure: Decimal = Decimal("0.200000")
    max_duplicate_block_pressure: Decimal = Decimal("0.500000")
    min_quality_pass_score: Decimal = Decimal("0.800000")
    min_quality_watch_score: Decimal = Decimal("0.500000")
    extraction_success_weight: Decimal = Decimal("0.160000")
    freshness_weight: Decimal = Decimal("0.140000")
    claim_acceptance_weight: Decimal = Decimal("0.160000")
    required_field_coverage_weight: Decimal = Decimal("0.150000")
    parser_confidence_weight: Decimal = Decimal("0.140000")
    normalization_weight: Decimal = Decimal("0.100000")
    contradiction_weight: Decimal = Decimal("0.075000")
    duplicate_weight: Decimal = Decimal("0.075000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimExtractionQualityConfig:
            raise TypeError(
                "ResearchSourceScraplingClaimExtractionQualityConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingClaimExtractionQualityConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_EXTRACTION_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_extraction_max_age_seconds",
            "stale_extraction_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_extraction_max_age_seconds >= self.stale_extraction_block_age_seconds:
            raise ValueError(
                "fresh_extraction_max_age_seconds must be below "
                "stale_extraction_block_age_seconds",
            )
        for field_name in (
            "min_extraction_success_pass_ratio",
            "min_extraction_success_watch_ratio",
            "min_claim_acceptance_pass_ratio",
            "min_claim_acceptance_watch_ratio",
            "min_required_field_coverage_pass_ratio",
            "min_required_field_coverage_watch_ratio",
            "min_parser_confidence_pass_ratio",
            "min_parser_confidence_watch_ratio",
            "min_normalization_pass_ratio",
            "min_normalization_watch_ratio",
            "max_contradiction_watch_pressure",
            "max_contradiction_block_pressure",
            "max_duplicate_watch_pressure",
            "max_duplicate_block_pressure",
            "min_quality_pass_score",
            "min_quality_watch_score",
            "extraction_success_weight",
            "freshness_weight",
            "claim_acceptance_weight",
            "required_field_coverage_weight",
            "parser_confidence_weight",
            "normalization_weight",
            "contradiction_weight",
            "duplicate_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_pass(
            "extraction success",
            self.min_extraction_success_watch_ratio,
            self.min_extraction_success_pass_ratio,
        )
        _require_watch_not_above_pass(
            "claim acceptance",
            self.min_claim_acceptance_watch_ratio,
            self.min_claim_acceptance_pass_ratio,
        )
        _require_watch_not_above_pass(
            "required field coverage",
            self.min_required_field_coverage_watch_ratio,
            self.min_required_field_coverage_pass_ratio,
        )
        _require_watch_not_above_pass(
            "parser confidence",
            self.min_parser_confidence_watch_ratio,
            self.min_parser_confidence_pass_ratio,
        )
        _require_watch_not_above_pass(
            "normalization",
            self.min_normalization_watch_ratio,
            self.min_normalization_pass_ratio,
        )
        _require_watch_not_above_pass(
            "quality",
            self.min_quality_watch_score,
            self.min_quality_pass_score,
        )
        if self.max_contradiction_watch_pressure > self.max_contradiction_block_pressure:
            raise ValueError(
                "contradiction watch pressure must not exceed block pressure",
            )
        if self.max_duplicate_watch_pressure > self.max_duplicate_block_pressure:
            raise ValueError("duplicate watch pressure must not exceed block pressure")
        weight_sum = _quantize(
            self.extraction_success_weight
            + self.freshness_weight
            + self.claim_acceptance_weight
            + self.required_field_coverage_weight
            + self.parser_confidence_weight
            + self.normalization_weight
            + self.contradiction_weight
            + self.duplicate_weight,
        )
        if weight_sum != ONE:
            raise ValueError("quality score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimExtractionQualityInput:
    private_candidate_ref: str
    extracted_at: datetime
    extraction_attempt_count: Decimal
    extraction_success_count: Decimal
    claim_span_count: Decimal
    accepted_claim_span_count: Decimal
    required_claim_field_count: Decimal
    populated_claim_field_count: Decimal
    parser_confidence_ratio: Decimal
    claim_normalization_ratio: Decimal
    contradiction_flag_count: Decimal
    duplicate_claim_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimExtractionQualityInput:
            raise TypeError(
                "ResearchSourceScraplingClaimExtractionQualityInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingClaimExtractionQualityInput,
            "input",
        )
        _require_private_string("private_candidate_ref", self.private_candidate_ref)
        object.__setattr__(self, "extracted_at", _as_utc("extracted_at", self.extracted_at))
        for field_name in (
            "extraction_success_count",
            "accepted_claim_span_count",
            "populated_claim_field_count",
            "contradiction_flag_count",
            "duplicate_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "extraction_attempt_count",
            "claim_span_count",
            "required_claim_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("parser_confidence_ratio", "claim_normalization_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.extraction_success_count > self.extraction_attempt_count:
            raise ValueError(
                "extraction_success_count must not exceed extraction_attempt_count",
            )
        if self.accepted_claim_span_count > self.claim_span_count:
            raise ValueError("accepted_claim_span_count must not exceed claim_span_count")
        if self.populated_claim_field_count > self.required_claim_field_count:
            raise ValueError(
                "populated_claim_field_count must not exceed required_claim_field_count",
            )
        if self.contradiction_flag_count > self.claim_span_count:
            raise ValueError("contradiction_flag_count must not exceed claim_span_count")
        if self.duplicate_claim_count > self.claim_span_count:
            raise ValueError("duplicate_claim_count must not exceed claim_span_count")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimExtractionQualityRow:
    row_label: str
    extraction_age_seconds: Decimal
    extraction_success_rate: Decimal
    extraction_freshness_score: Decimal
    claim_acceptance_rate: Decimal
    required_field_coverage_rate: Decimal
    parser_confidence_score: Decimal
    normalization_score: Decimal
    contradiction_pressure_score: Decimal
    duplicate_pressure_score: Decimal
    extraction_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimExtractionQualityRow:
            raise TypeError(
                "ResearchSourceScraplingClaimExtractionQualityRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingClaimExtractionQualityRow, "row")
        _require_public_identifier("row_label", self.row_label)
        object.__setattr__(
            self,
            "extraction_age_seconds",
            _normalize_nonnegative_decimal(
                "extraction_age_seconds",
                self.extraction_age_seconds,
            ),
        )
        for field_name in (
            "extraction_success_rate",
            "extraction_freshness_score",
            "claim_acceptance_rate",
            "required_field_coverage_rate",
            "parser_confidence_score",
            "normalization_score",
            "contradiction_pressure_score",
            "duplicate_pressure_score",
            "extraction_quality_score",
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
class ResearchSourceScraplingClaimExtractionQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimExtractionQualityReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingClaimExtractionQualityReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingClaimExtractionQualityReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimExtractionQualityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_extraction_age_seconds: Decimal
    average_extraction_success_rate: Decimal
    average_extraction_freshness_score: Decimal
    average_claim_acceptance_rate: Decimal
    average_required_field_coverage_rate: Decimal
    average_parser_confidence_score: Decimal
    average_normalization_score: Decimal
    average_contradiction_pressure_score: Decimal
    average_duplicate_pressure_score: Decimal
    average_extraction_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraplingClaimExtractionQualityReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraplingClaimExtractionQualityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimExtractionQualityReport:
            raise TypeError(
                "ResearchSourceScraplingClaimExtractionQualityReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingClaimExtractionQualityReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_EXTRACTION_QUALITY_REPORT_CONFIG_VERSION
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
            "max_extraction_age_seconds",
            _normalize_nonnegative_decimal(
                "max_extraction_age_seconds",
                self.max_extraction_age_seconds,
            ),
        )
        for field_name in (
            "average_extraction_success_rate",
            "average_extraction_freshness_score",
            "average_claim_acceptance_rate",
            "average_required_field_coverage_rate",
            "average_parser_confidence_score",
            "average_normalization_score",
            "average_contradiction_pressure_score",
            "average_duplicate_pressure_score",
            "average_extraction_quality_score",
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
        return research_source_scrapling_claim_extraction_quality_report_payload(self)


def build_research_source_scrapling_claim_extraction_quality_report(
    inputs: Iterable[ResearchSourceScraplingClaimExtractionQualityInput],
    *,
    config: ResearchSourceScraplingClaimExtractionQualityConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingClaimExtractionQualityReport:
    if type(config) is not ResearchSourceScraplingClaimExtractionQualityConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScraplingClaimExtractionQualityConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.extracted_at > generated_at:
            raise ValueError("extracted_at cannot be after generated_at")
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
    attention_count = watch_count + block_count
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)
    return ResearchSourceScraplingClaimExtractionQualityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized_inputs)),
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=attention_count,
        max_extraction_age_seconds=max(
            (row.extraction_age_seconds for row in rows),
            default=ZERO,
        ),
        average_extraction_success_rate=_average(
            row.extraction_success_rate for row in rows
        ),
        average_extraction_freshness_score=_average(
            row.extraction_freshness_score for row in rows
        ),
        average_claim_acceptance_rate=_average(
            row.claim_acceptance_rate for row in rows
        ),
        average_required_field_coverage_rate=_average(
            row.required_field_coverage_rate for row in rows
        ),
        average_parser_confidence_score=_average(
            row.parser_confidence_score for row in rows
        ),
        average_normalization_score=_average(row.normalization_score for row in rows),
        average_contradiction_pressure_score=_average(
            row.contradiction_pressure_score for row in rows
        ),
        average_duplicate_pressure_score=_average(
            row.duplicate_pressure_score for row in rows
        ),
        average_extraction_quality_score=_average(
            row.extraction_quality_score for row in rows
        ),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scrapling_claim_extraction_quality_report_payload(
    report: ResearchSourceScraplingClaimExtractionQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraplingClaimExtractionQualityReport:
        raise ValueError(
            "report must be exactly ResearchSourceScraplingClaimExtractionQualityReport",
        )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    _validate_report_payload_schema(payload, require_digest=True)
    return payload


def research_source_scrapling_claim_extraction_quality_report_digest(
    report: ResearchSourceScraplingClaimExtractionQualityReport,
) -> str:
    payload = research_source_scrapling_claim_extraction_quality_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scrapling_claim_extraction_quality_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
        _validate_report_payload_schema(payload, require_digest=True)
        digest = payload["derived_validation_digest"]
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        return sha256(encoded).hexdigest() == digest
    except (TypeError, ValueError):
        return False


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScraplingClaimExtractionQualityInput],
) -> tuple[ResearchSourceScraplingClaimExtractionQualityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScraplingClaimExtractionQualityInput:
            raise ValueError(
                "inputs must contain ResearchSourceScraplingClaimExtractionQualityInput",
            )
        _require_hard_flags("input", item)
    return tuple(sorted(normalized, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScraplingClaimExtractionQualityInput,
) -> tuple[str, str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        item.private_candidate_ref,
        item.extracted_at.isoformat(),
        item.extraction_attempt_count,
        item.extraction_success_count,
        item.claim_span_count,
        item.accepted_claim_span_count,
        item.required_claim_field_count,
        item.populated_claim_field_count,
        item.parser_confidence_ratio,
        item.claim_normalization_ratio,
        item.contradiction_flag_count,
        item.duplicate_claim_count,
    )


def _row_from_input(
    item: ResearchSourceScraplingClaimExtractionQualityInput,
    *,
    row_number: int,
    config: ResearchSourceScraplingClaimExtractionQualityConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingClaimExtractionQualityRow:
    extraction_age_seconds = _age_seconds(generated_at, item.extracted_at)
    extraction_success_rate = _safe_ratio(
        item.extraction_success_count,
        item.extraction_attempt_count,
    )
    freshness_score = _freshness_score(extraction_age_seconds, config)
    claim_acceptance_rate = _safe_ratio(
        item.accepted_claim_span_count,
        item.claim_span_count,
    )
    required_field_coverage_rate = _safe_ratio(
        item.populated_claim_field_count,
        item.required_claim_field_count,
    )
    contradiction_pressure_score = min(
        ONE,
        _safe_ratio(item.contradiction_flag_count, item.claim_span_count),
    )
    duplicate_pressure_score = min(
        ONE,
        _safe_ratio(item.duplicate_claim_count, item.claim_span_count),
    )
    quality_score = _quantize(
        extraction_success_rate * config.extraction_success_weight
        + freshness_score * config.freshness_weight
        + claim_acceptance_rate * config.claim_acceptance_weight
        + required_field_coverage_rate * config.required_field_coverage_weight
        + item.parser_confidence_ratio * config.parser_confidence_weight
        + item.claim_normalization_ratio * config.normalization_weight
        + (ONE - contradiction_pressure_score) * config.contradiction_weight
        + (ONE - duplicate_pressure_score) * config.duplicate_weight,
    )
    reason_codes = _row_reason_codes(
        extraction_success_rate=extraction_success_rate,
        freshness_score=freshness_score,
        extraction_age_seconds=extraction_age_seconds,
        claim_acceptance_rate=claim_acceptance_rate,
        required_field_coverage_rate=required_field_coverage_rate,
        parser_confidence_score=item.parser_confidence_ratio,
        normalization_score=item.claim_normalization_ratio,
        contradiction_pressure_score=contradiction_pressure_score,
        duplicate_pressure_score=duplicate_pressure_score,
        config=config,
    )
    status = _row_status(reason_codes, quality_score, config)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*reason_codes, _status_reason(status)),
    )
    return ResearchSourceScraplingClaimExtractionQualityRow(
        row_label=f"redacted-scrapling-claim-extraction-{row_number:06d}",
        extraction_age_seconds=extraction_age_seconds,
        extraction_success_rate=extraction_success_rate,
        extraction_freshness_score=freshness_score,
        claim_acceptance_rate=claim_acceptance_rate,
        required_field_coverage_rate=required_field_coverage_rate,
        parser_confidence_score=item.parser_confidence_ratio,
        normalization_score=item.claim_normalization_ratio,
        contradiction_pressure_score=contradiction_pressure_score,
        duplicate_pressure_score=duplicate_pressure_score,
        extraction_quality_score=quality_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _freshness_score(
    extraction_age_seconds: Decimal,
    config: ResearchSourceScraplingClaimExtractionQualityConfig,
) -> Decimal:
    if extraction_age_seconds <= config.fresh_extraction_max_age_seconds:
        return ONE
    if extraction_age_seconds >= config.stale_extraction_block_age_seconds:
        return ZERO
    stale_window = (
        config.stale_extraction_block_age_seconds
        - config.fresh_extraction_max_age_seconds
    )
    stale_progress = _safe_ratio(
        extraction_age_seconds - config.fresh_extraction_max_age_seconds,
        stale_window,
    )
    return _quantize(ONE - stale_progress)


def _row_reason_codes(
    *,
    extraction_success_rate: Decimal,
    freshness_score: Decimal,
    extraction_age_seconds: Decimal,
    claim_acceptance_rate: Decimal,
    required_field_coverage_rate: Decimal,
    parser_confidence_score: Decimal,
    normalization_score: Decimal,
    contradiction_pressure_score: Decimal,
    duplicate_pressure_score: Decimal,
    config: ResearchSourceScraplingClaimExtractionQualityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if extraction_success_rate < config.min_extraction_success_watch_ratio:
        reason_codes.append("extraction_success_rate_block")
    elif extraction_success_rate < config.min_extraction_success_pass_ratio:
        reason_codes.append("extraction_success_rate_watch")
    if extraction_age_seconds >= config.stale_extraction_block_age_seconds:
        reason_codes.append("extraction_age_block")
    elif freshness_score < ONE:
        reason_codes.append("extraction_age_watch")
    if claim_acceptance_rate < config.min_claim_acceptance_watch_ratio:
        reason_codes.append("claim_acceptance_rate_block")
    elif claim_acceptance_rate < config.min_claim_acceptance_pass_ratio:
        reason_codes.append("claim_acceptance_rate_watch")
    if required_field_coverage_rate < config.min_required_field_coverage_watch_ratio:
        reason_codes.append("required_field_coverage_block")
    elif required_field_coverage_rate < config.min_required_field_coverage_pass_ratio:
        reason_codes.append("required_field_coverage_watch")
    if parser_confidence_score < config.min_parser_confidence_watch_ratio:
        reason_codes.append("parser_confidence_block")
    elif parser_confidence_score < config.min_parser_confidence_pass_ratio:
        reason_codes.append("parser_confidence_watch")
    if normalization_score < config.min_normalization_watch_ratio:
        reason_codes.append("normalization_block")
    elif normalization_score < config.min_normalization_pass_ratio:
        reason_codes.append("normalization_watch")
    if contradiction_pressure_score >= config.max_contradiction_block_pressure:
        reason_codes.append("contradiction_pressure_block")
    elif contradiction_pressure_score >= config.max_contradiction_watch_pressure:
        reason_codes.append("contradiction_pressure_watch")
    if duplicate_pressure_score >= config.max_duplicate_block_pressure:
        reason_codes.append("duplicate_pressure_block")
    elif duplicate_pressure_score >= config.max_duplicate_watch_pressure:
        reason_codes.append("duplicate_pressure_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(
    reason_codes: tuple[str, ...],
    quality_score: Decimal,
    config: ResearchSourceScraplingClaimExtractionQualityConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if quality_score < config.min_quality_watch_score:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if quality_score < config.min_quality_pass_score:
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


def _report_status(rows: tuple[ResearchSourceScraplingClaimExtractionQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingClaimExtractionQualityRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScraplingClaimExtractionQualityReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchSourceScraplingClaimExtractionQualityReasonCodeCount(
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
    rows: tuple[ResearchSourceScraplingClaimExtractionQualityRow, ...],
) -> tuple[ResearchSourceScraplingClaimExtractionQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraplingClaimExtractionQualityRow:
            raise ValueError(
                "rows must contain ResearchSourceScraplingClaimExtractionQualityRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceScraplingClaimExtractionQualityRow,
) -> tuple[int, str]:
    return (STATUS_WEIGHT[row.status], row.row_label)


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraplingClaimExtractionQualityReasonCodeCount, ...],
) -> tuple[ResearchSourceScraplingClaimExtractionQualityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceScraplingClaimExtractionQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraplingClaimExtractionQualityReasonCodeCount",
            )
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_report_consistency(
    report: ResearchSourceScraplingClaimExtractionQualityReport,
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
    if report.status != _report_status(report.rows):
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows and status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.max_extraction_age_seconds != max(
        (row.extraction_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_extraction_age_seconds must match rows")
    expected_averages = {
        "average_extraction_success_rate": _average(
            row.extraction_success_rate for row in report.rows
        ),
        "average_extraction_freshness_score": _average(
            row.extraction_freshness_score for row in report.rows
        ),
        "average_claim_acceptance_rate": _average(
            row.claim_acceptance_rate for row in report.rows
        ),
        "average_required_field_coverage_rate": _average(
            row.required_field_coverage_rate for row in report.rows
        ),
        "average_parser_confidence_score": _average(
            row.parser_confidence_score for row in report.rows
        ),
        "average_normalization_score": _average(
            row.normalization_score for row in report.rows
        ),
        "average_contradiction_pressure_score": _average(
            row.contradiction_pressure_score for row in report.rows
        ),
        "average_duplicate_pressure_score": _average(
            row.duplicate_pressure_score for row in report.rows
        ),
        "average_extraction_quality_score": _average(
            row.extraction_quality_score for row in report.rows
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


def _age_seconds(generated_at: datetime, extracted_at: datetime) -> Decimal:
    delta = generated_at - extracted_at
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            Decimal(delta.days * 86400 + delta.seconds)
            + Decimal(delta.microseconds) / MICROSECOND_DIVISOR,
        )


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized == ZERO:
        return ZERO
    return normalized


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


def _require_watch_not_above_pass(
    label: str,
    watch_value: Decimal,
    pass_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{label} watch threshold must not exceed pass threshold")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    _reject_unsafe_public_text(field_name, value)


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


def _report_digest(report: ResearchSourceScraplingClaimExtractionQualityReport) -> str:
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


def _validate_report_payload_schema(
    payload: dict[str, Any],
    *,
    require_digest: bool,
) -> None:
    expected_keys = REPORT_PAYLOAD_KEYS if require_digest else REPORT_PAYLOAD_UNSIGNED_KEYS
    _require_payload_keys("payload", payload, expected_keys)
    if require_digest:
        _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    config_version = _payload_public_identifier("config_version", payload["config_version"])
    if (
        config_version
        != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_EXTRACTION_QUALITY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    count_values = {
        field_name: _payload_nonnegative_count(field_name, payload[field_name])
        for field_name in REPORT_COUNT_PAYLOAD_FIELDS
    }
    average_values = {
        field_name: _payload_probability(field_name, payload[field_name])
        for field_name in REPORT_AVERAGE_PAYLOAD_FIELDS
    }
    normalized = ResearchSourceScraplingClaimExtractionQualityReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=config_version,
        input_count=count_values["input_count"],
        row_count=count_values["row_count"],
        pass_count=count_values["pass_count"],
        watch_count=count_values["watch_count"],
        block_count=count_values["block_count"],
        attention_count=count_values["attention_count"],
        max_extraction_age_seconds=_payload_nonnegative_decimal(
            "max_extraction_age_seconds",
            payload["max_extraction_age_seconds"],
        ),
        average_extraction_success_rate=average_values["average_extraction_success_rate"],
        average_extraction_freshness_score=average_values[
            "average_extraction_freshness_score"
        ],
        average_claim_acceptance_rate=average_values["average_claim_acceptance_rate"],
        average_required_field_coverage_rate=average_values[
            "average_required_field_coverage_rate"
        ],
        average_parser_confidence_score=average_values["average_parser_confidence_score"],
        average_normalization_score=average_values["average_normalization_score"],
        average_contradiction_pressure_score=average_values[
            "average_contradiction_pressure_score"
        ],
        average_duplicate_pressure_score=average_values["average_duplicate_pressure_score"],
        average_extraction_quality_score=average_values[
            "average_extraction_quality_score"
        ],
        status=_payload_status("status", payload["status"]),
        reason_codes=_payload_reason_codes("reason_codes", payload["reason_codes"]),
        reason_code_counts=tuple(
            _payload_reason_code_count(item)
            for item in _payload_list("reason_code_counts", payload["reason_code_counts"])
        ),
        rows=tuple(_payload_row(item) for item in _payload_list("rows", payload["rows"])),
        paper_only=_payload_hard_flag("paper_only", payload["paper_only"]),
        report_only=_payload_hard_flag("report_only", payload["report_only"]),
        readonly=_payload_hard_flag("readonly", payload["readonly"]),
    )
    expected = _json_ready(asdict(normalized))
    expected.pop("derived_validation_digest", None)
    observed = dict(payload)
    observed.pop("derived_validation_digest", None)
    if observed != expected:
        raise ValueError("payload must use deterministic public schema")


def _payload_row(payload: Any) -> ResearchSourceScraplingClaimExtractionQualityRow:
    _require_payload_keys("row", payload, ROW_PAYLOAD_KEYS)
    row_label = _payload_public_identifier("row_label", payload["row_label"])
    status = _payload_status("status", payload["status"])
    reason_codes = _payload_reason_codes("reason_codes", payload["reason_codes"])
    expected_status_reason = _status_reason(status)
    unexpected_status_reasons = STATUS_REASON_CODES - frozenset((expected_status_reason,))
    if expected_status_reason not in reason_codes or any(
        reason_code in reason_codes for reason_code in unexpected_status_reasons
    ):
        raise ValueError("row reason_codes must match status")
    return ResearchSourceScraplingClaimExtractionQualityRow(
        row_label=row_label,
        extraction_age_seconds=_payload_nonnegative_decimal(
            "extraction_age_seconds",
            payload["extraction_age_seconds"],
        ),
        extraction_success_rate=_payload_probability(
            "extraction_success_rate",
            payload["extraction_success_rate"],
        ),
        extraction_freshness_score=_payload_probability(
            "extraction_freshness_score",
            payload["extraction_freshness_score"],
        ),
        claim_acceptance_rate=_payload_probability(
            "claim_acceptance_rate",
            payload["claim_acceptance_rate"],
        ),
        required_field_coverage_rate=_payload_probability(
            "required_field_coverage_rate",
            payload["required_field_coverage_rate"],
        ),
        parser_confidence_score=_payload_probability(
            "parser_confidence_score",
            payload["parser_confidence_score"],
        ),
        normalization_score=_payload_probability(
            "normalization_score",
            payload["normalization_score"],
        ),
        contradiction_pressure_score=_payload_probability(
            "contradiction_pressure_score",
            payload["contradiction_pressure_score"],
        ),
        duplicate_pressure_score=_payload_probability(
            "duplicate_pressure_score",
            payload["duplicate_pressure_score"],
        ),
        extraction_quality_score=_payload_probability(
            "extraction_quality_score",
            payload["extraction_quality_score"],
        ),
        status=status,
        reason_codes=reason_codes,
        paper_only=_payload_hard_flag("paper_only", payload["paper_only"]),
        report_only=_payload_hard_flag("report_only", payload["report_only"]),
        readonly=_payload_hard_flag("readonly", payload["readonly"]),
    )


def _payload_reason_code_count(
    payload: Any,
) -> ResearchSourceScraplingClaimExtractionQualityReasonCodeCount:
    _require_payload_keys("reason_code_count", payload, REASON_CODE_COUNT_PAYLOAD_KEYS)
    _require_reason_code("reason_code", payload["reason_code"])
    return ResearchSourceScraplingClaimExtractionQualityReasonCodeCount(
        reason_code=payload["reason_code"],
        count=_payload_positive_count("count", payload["count"]),
        paper_only=_payload_hard_flag("paper_only", payload["paper_only"]),
        report_only=_payload_hard_flag("report_only", payload["report_only"]),
        readonly=_payload_hard_flag("readonly", payload["readonly"]),
    )


def _require_payload_keys(
    label: str,
    value: Any,
    expected_keys: frozenset[str],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} schema keys must match")


def _payload_list(field_name: str, value: Any) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _payload_hard_flag(field_name: str, value: Any) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_public_identifier(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public identifier")
    _require_public_identifier(field_name, value)
    return value


def _payload_status(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    _require_status(field_name, value)
    return value


def _payload_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    reason_codes = tuple(_payload_list(field_name, value))
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if reason_codes != _normalize_reason_codes(field_name, reason_codes):
        raise ValueError(f"{field_name} must be canonical")
    return reason_codes


def _payload_datetime(field_name: str, value: Any) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC ISO datetime string")
    return normalized


def _payload_positive_count(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_positive_count)


def _payload_nonnegative_count(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_count)


def _payload_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_decimal)


def _payload_probability(field_name: str, value: Any) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_probability)


def _payload_decimal(
    field_name: str,
    value: Any,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except (ArithmeticError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public surface")
