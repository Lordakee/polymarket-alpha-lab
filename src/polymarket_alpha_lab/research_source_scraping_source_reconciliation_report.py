"""Report-only reconciliation reducer for sanitized scraping outputs.

Callers provide already-sanitized retrieval telemetry from scraping tools. This
module performs no collection, persistence, authentication, trading, sizing, or
network work. It returns deterministic pass/watch/block rows, a JSON-ready
public payload, and SHA-256 digest validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field as dataclass_field, fields, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPING_SOURCE_RECONCILIATION_REPORT_CONFIG_VERSION = (
    "research-source-scraping-source-reconciliation-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
RETRIEVAL_TOOLS = ("agent_reach", "generic", "scrapling")
AUTHORITY_TIERS = ("official", "primary", "secondary", "tertiary", "unknown")
AUTHORITY_TIER_SCORES = {
    "official": ONE,
    "primary": ONE,
    "secondary": Decimal("0.750000"),
    "tertiary": Decimal("0.500000"),
    "unknown": Decimal("0.250000"),
}
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "source_reconciliation_no_inputs"
PASS_REASON = "source_reconciliation_pass"
WATCH_REASON = "source_reconciliation_watch"
BLOCK_REASON = "source_reconciliation_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "freshness_block",
    "freshness_watch",
    "extraction_confidence_block",
    "extraction_confidence_watch",
    "authority_tier_block",
    "authority_tier_watch",
    "conflict_pressure_block",
    "conflict_pressure_watch",
    "fallback_coverage_block",
    "fallback_coverage_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
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
    "wallet",
    "order",
    "trade",
    "live",
    "recommendation",
    "position_size",
)

CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "fresh_extraction_max_age_seconds",
    "stale_extraction_block_age_seconds",
    "min_extraction_confidence_pass_ratio",
    "min_extraction_confidence_watch_ratio",
    "min_authority_score_pass_ratio",
    "min_authority_score_watch_ratio",
    "max_conflict_pressure_pass_ratio",
    "max_conflict_pressure_watch_ratio",
    "min_fallback_coverage_pass_ratio",
    "min_fallback_coverage_watch_ratio",
    "min_reconciliation_pass_score",
    "min_reconciliation_watch_score",
    "freshness_weight",
    "extraction_confidence_weight",
    "authority_weight",
    "conflict_pressure_weight",
    "fallback_coverage_weight",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "row_label",
    "rank",
    "retrieval_tool",
    "extraction_age_seconds",
    "freshness_score",
    "extraction_confidence_score",
    "authority_score",
    "conflict_pressure_score",
    "fallback_coverage_score",
    "reconciliation_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
    "max_extraction_age_seconds",
    "average_freshness_score",
    "average_extraction_confidence_score",
    "average_authority_score",
    "average_conflict_pressure_score",
    "average_fallback_coverage_score",
    "average_reconciliation_score",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "config",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPING_SOURCE_RECONCILIATION_REPORT_CONFIG_VERSION",
    "AUTHORITY_TIERS",
    "RETRIEVAL_TOOLS",
    "STATUSES",
    "ResearchSourceScrapingSourceReconciliationConfig",
    "ResearchSourceScrapingSourceReconciliationInput",
    "ResearchSourceScrapingSourceReconciliationReasonCodeCount",
    "ResearchSourceScrapingSourceReconciliationReport",
    "ResearchSourceScrapingSourceReconciliationRow",
    "build_research_source_scraping_source_reconciliation_report",
    "research_source_scraping_source_reconciliation_report_digest",
    "research_source_scraping_source_reconciliation_report_public_payload",
    "validate_research_source_scraping_source_reconciliation_report_public_payload",
)


@dataclass(frozen=True, slots=True)
class ResearchSourceScrapingSourceReconciliationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPING_SOURCE_RECONCILIATION_REPORT_CONFIG_VERSION
    )
    fresh_extraction_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_extraction_block_age_seconds: Decimal = Decimal("86400.000000")
    min_extraction_confidence_pass_ratio: Decimal = Decimal("0.850000")
    min_extraction_confidence_watch_ratio: Decimal = Decimal("0.600000")
    min_authority_score_pass_ratio: Decimal = Decimal("0.800000")
    min_authority_score_watch_ratio: Decimal = Decimal("0.500000")
    max_conflict_pressure_pass_ratio: Decimal = Decimal("0.200000")
    max_conflict_pressure_watch_ratio: Decimal = Decimal("0.500000")
    min_fallback_coverage_pass_ratio: Decimal = Decimal("0.800000")
    min_fallback_coverage_watch_ratio: Decimal = Decimal("0.400000")
    min_reconciliation_pass_score: Decimal = Decimal("0.800000")
    min_reconciliation_watch_score: Decimal = Decimal("0.500000")
    freshness_weight: Decimal = Decimal("0.200000")
    extraction_confidence_weight: Decimal = Decimal("0.250000")
    authority_weight: Decimal = Decimal("0.200000")
    conflict_pressure_weight: Decimal = Decimal("0.200000")
    fallback_coverage_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchSourceScrapingSourceReconciliationConfig, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchSourceScrapingSourceReconciliationConfig:
            raise TypeError(
                "ResearchSourceScrapingSourceReconciliationConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingSourceReconciliationConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPING_SOURCE_RECONCILIATION_REPORT_CONFIG_VERSION
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
        if (
            self.fresh_extraction_max_age_seconds
            >= self.stale_extraction_block_age_seconds
        ):
            raise ValueError(
                "fresh_extraction_max_age_seconds must be below "
                "stale_extraction_block_age_seconds",
            )
        for field_name in (
            "min_extraction_confidence_pass_ratio",
            "min_extraction_confidence_watch_ratio",
            "min_authority_score_pass_ratio",
            "min_authority_score_watch_ratio",
            "max_conflict_pressure_pass_ratio",
            "max_conflict_pressure_watch_ratio",
            "min_fallback_coverage_pass_ratio",
            "min_fallback_coverage_watch_ratio",
            "min_reconciliation_pass_score",
            "min_reconciliation_watch_score",
            "freshness_weight",
            "extraction_confidence_weight",
            "authority_weight",
            "conflict_pressure_weight",
            "fallback_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.min_extraction_confidence_watch_ratio
            > self.min_extraction_confidence_pass_ratio
        ):
            raise ValueError(
                "extraction confidence watch threshold must not exceed pass threshold",
            )
        if self.min_authority_score_watch_ratio > self.min_authority_score_pass_ratio:
            raise ValueError("authority watch threshold must not exceed pass threshold")
        if self.max_conflict_pressure_pass_ratio > self.max_conflict_pressure_watch_ratio:
            raise ValueError(
                "conflict pressure pass threshold must not exceed watch threshold",
            )
        if self.min_fallback_coverage_watch_ratio > self.min_fallback_coverage_pass_ratio:
            raise ValueError(
                "fallback coverage watch threshold must not exceed pass threshold",
            )
        if self.min_reconciliation_watch_score > self.min_reconciliation_pass_score:
            raise ValueError(
                "reconciliation watch threshold must not exceed pass threshold",
            )
        with localcontext(DECIMAL_CONTEXT):
            weight_sum = _quantize(
                self.freshness_weight
                + self.extraction_confidence_weight
                + self.authority_weight
                + self.conflict_pressure_weight
                + self.fallback_coverage_weight,
            )
        if weight_sum != ONE:
            raise ValueError("reconciliation weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True, slots=True)
class ResearchSourceScrapingSourceReconciliationInput:
    private_reconciliation_ref: str
    retrieval_tool: str
    captured_at: datetime
    extraction_confidence: Decimal
    authority_tier: str
    conflict_pressure: Decimal
    fallback_coverage: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchSourceScrapingSourceReconciliationInput, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchSourceScrapingSourceReconciliationInput:
            raise TypeError(
                "ResearchSourceScrapingSourceReconciliationInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingSourceReconciliationInput, "input")
        _require_private_string("private_reconciliation_ref", self.private_reconciliation_ref)
        _require_member("retrieval_tool", self.retrieval_tool, RETRIEVAL_TOOLS)
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "extraction_confidence",
            "conflict_pressure",
            "fallback_coverage",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        _require_hard_flags("input", self)


@dataclass(frozen=True, slots=True)
class ResearchSourceScrapingSourceReconciliationRow:
    row_label: str
    rank: Decimal
    retrieval_tool: str
    extraction_age_seconds: Decimal
    freshness_score: Decimal
    extraction_confidence_score: Decimal
    authority_score: Decimal
    conflict_pressure_score: Decimal
    fallback_coverage_score: Decimal
    reconciliation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchSourceScrapingSourceReconciliationRow, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchSourceScrapingSourceReconciliationRow:
            raise TypeError(
                "ResearchSourceScrapingSourceReconciliationRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingSourceReconciliationRow, "row")
        _require_public_identifier("row_label", self.row_label)
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_member("retrieval_tool", self.retrieval_tool, RETRIEVAL_TOOLS)
        object.__setattr__(
            self,
            "extraction_age_seconds",
            _normalize_nonnegative_decimal(
                "extraction_age_seconds",
                self.extraction_age_seconds,
            ),
        )
        for field_name in (
            "freshness_score",
            "extraction_confidence_score",
            "authority_score",
            "conflict_pressure_score",
            "fallback_coverage_score",
            "reconciliation_score",
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
        if self.authority_score not in AUTHORITY_TIER_SCORES.values():
            raise ValueError("authority_score must match a supported authority tier")
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True, slots=True)
class ResearchSourceScrapingSourceReconciliationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(
            ResearchSourceScrapingSourceReconciliationReasonCodeCount,
            cls,
        ).__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingSourceReconciliationReasonCodeCount:
            raise TypeError(
                "ResearchSourceScrapingSourceReconciliationReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScrapingSourceReconciliationReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True, slots=True)
class ResearchSourceScrapingSourceReconciliationReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_extraction_age_seconds: Decimal
    average_freshness_score: Decimal
    average_extraction_confidence_score: Decimal
    average_authority_score: Decimal
    average_conflict_pressure_score: Decimal
    average_fallback_coverage_score: Decimal
    average_reconciliation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScrapingSourceReconciliationReasonCodeCount, ...]
    rows: tuple[ResearchSourceScrapingSourceReconciliationRow, ...]
    config: ResearchSourceScrapingSourceReconciliationConfig = dataclass_field(
        default_factory=ResearchSourceScrapingSourceReconciliationConfig,
    )
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchSourceScrapingSourceReconciliationReport, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchSourceScrapingSourceReconciliationReport:
            raise TypeError(
                "ResearchSourceScrapingSourceReconciliationReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingSourceReconciliationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPING_SOURCE_RECONCILIATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "config", _revalidate_config(self.config))
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
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
            "average_freshness_score",
            "average_extraction_confidence_score",
            "average_authority_score",
            "average_conflict_pressure_score",
            "average_fallback_coverage_score",
            "average_reconciliation_score",
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
    def public_payload(self) -> dict[str, Any]:
        return research_source_scraping_source_reconciliation_report_public_payload(self)


def build_research_source_scraping_source_reconciliation_report(
    inputs: Iterable[ResearchSourceScrapingSourceReconciliationInput],
    *,
    config: ResearchSourceScrapingSourceReconciliationConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingSourceReconciliationReport:
    config = _revalidate_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.captured_at > generated_at:
            raise ValueError("captured_at cannot be after generated_at")
    _reject_duplicate_private_reconciliation_refs(normalized_inputs)

    provisional_rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    row_number=index,
                    config=config,
                    generated_at=generated_at,
                )
                for index, item in enumerate(normalized_inputs, start=1)
            ),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        replace(
            row,
            row_label=f"redacted-source-reconciliation-{rank:06d}",
            rank=_count_decimal(rank),
        )
        for rank, row in enumerate(provisional_rows, start=1)
    )
    input_count = _count_decimal(len(normalized_inputs))
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    with localcontext(DECIMAL_CONTEXT):
        attention_count = _quantize(watch_count + block_count)
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    return ResearchSourceScrapingSourceReconciliationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=attention_count,
        max_extraction_age_seconds=max(
            (row.extraction_age_seconds for row in rows),
            default=ZERO,
        ),
        average_freshness_score=_average(row.freshness_score for row in rows),
        average_extraction_confidence_score=_average(
            (row.extraction_confidence_score for row in rows),
        ),
        average_authority_score=_average(row.authority_score for row in rows),
        average_conflict_pressure_score=_average(
            (row.conflict_pressure_score for row in rows),
        ),
        average_fallback_coverage_score=_average(
            (row.fallback_coverage_score for row in rows),
        ),
        average_reconciliation_score=_average(row.reconciliation_score for row in rows),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        config=config,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scraping_source_reconciliation_report_public_payload(
    report: ResearchSourceScrapingSourceReconciliationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScrapingSourceReconciliationReport:
        raise ValueError(
            "report must be exactly ResearchSourceScrapingSourceReconciliationReport",
        )
    _revalidate_report_members(report)
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scraping_source_reconciliation_report_digest(
    report: ResearchSourceScrapingSourceReconciliationReport,
) -> str:
    payload = research_source_scraping_source_reconciliation_report_public_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scraping_source_reconciliation_report_public_payload(
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
    except (InvalidOperation, TypeError, ValueError):
        return False


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScrapingSourceReconciliationInput],
) -> tuple[ResearchSourceScrapingSourceReconciliationInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    revalidated = tuple(_revalidate_input(item) for item in normalized)
    return tuple(sorted(revalidated, key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScrapingSourceReconciliationInput,
) -> tuple[str, str, Decimal, str, Decimal, Decimal, str]:
    return (
        item.retrieval_tool,
        item.captured_at.isoformat(),
        item.extraction_confidence,
        item.authority_tier,
        item.conflict_pressure,
        item.fallback_coverage,
        item.private_reconciliation_ref,
    )


def _reject_duplicate_private_reconciliation_refs(
    inputs: tuple[ResearchSourceScrapingSourceReconciliationInput, ...],
) -> None:
    counts: Counter[str] = Counter(item.private_reconciliation_ref for item in inputs)
    if any(count > 1 for count in counts.values()):
        raise ValueError("private_reconciliation_ref values must be unique")


def _row_from_input(
    item: ResearchSourceScrapingSourceReconciliationInput,
    *,
    row_number: int,
    config: ResearchSourceScrapingSourceReconciliationConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingSourceReconciliationRow:
    age_seconds = _age_seconds(item.captured_at, generated_at)
    freshness_score = _freshness_score(age_seconds, config)
    extraction_confidence_score = item.extraction_confidence
    authority_score = AUTHORITY_TIER_SCORES[item.authority_tier]
    fallback_coverage_score = item.fallback_coverage
    with localcontext(DECIMAL_CONTEXT):
        conflict_pressure_score = _quantize(ONE - item.conflict_pressure)
        reconciliation_score = _quantize(
            (freshness_score * config.freshness_weight)
            + (extraction_confidence_score * config.extraction_confidence_weight)
            + (authority_score * config.authority_weight)
            + (conflict_pressure_score * config.conflict_pressure_weight)
            + (fallback_coverage_score * config.fallback_coverage_weight),
        )
    reason_codes = _row_reason_codes(
        age_seconds=age_seconds,
        extraction_confidence_score=extraction_confidence_score,
        authority_score=authority_score,
        conflict_pressure=item.conflict_pressure,
        fallback_coverage_score=fallback_coverage_score,
        config=config,
    )
    status = _status_from_reasons(reason_codes, reconciliation_score, config)
    reason_codes = _append_status_reason(reason_codes, status)
    return ResearchSourceScrapingSourceReconciliationRow(
        row_label=f"redacted-source-reconciliation-{row_number:06d}",
        rank=_count_decimal(row_number),
        retrieval_tool=item.retrieval_tool,
        extraction_age_seconds=age_seconds,
        freshness_score=freshness_score,
        extraction_confidence_score=extraction_confidence_score,
        authority_score=authority_score,
        conflict_pressure_score=conflict_pressure_score,
        fallback_coverage_score=fallback_coverage_score,
        reconciliation_score=reconciliation_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _age_seconds(captured_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - captured_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        microseconds = Decimal(delta.microseconds) / Decimal("1000000")
        age_seconds = seconds + microseconds
    return _normalize_nonnegative_decimal("extraction_age_seconds", age_seconds)


def _freshness_score(
    age_seconds: Decimal,
    config: ResearchSourceScrapingSourceReconciliationConfig,
) -> Decimal:
    if age_seconds <= config.fresh_extraction_max_age_seconds:
        return ONE
    if age_seconds >= config.stale_extraction_block_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        stale_span = (
            config.stale_extraction_block_age_seconds
            - config.fresh_extraction_max_age_seconds
        )
        remaining = config.stale_extraction_block_age_seconds - age_seconds
        freshness_score = remaining / stale_span
    return _normalize_probability("freshness_score", freshness_score)


def _row_reason_codes(
    *,
    age_seconds: Decimal,
    extraction_confidence_score: Decimal,
    authority_score: Decimal,
    conflict_pressure: Decimal,
    fallback_coverage_score: Decimal,
    config: ResearchSourceScrapingSourceReconciliationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if age_seconds >= config.stale_extraction_block_age_seconds:
        reason_codes.append("freshness_block")
    elif age_seconds > config.fresh_extraction_max_age_seconds:
        reason_codes.append("freshness_watch")
    if extraction_confidence_score < config.min_extraction_confidence_watch_ratio:
        reason_codes.append("extraction_confidence_block")
    elif extraction_confidence_score < config.min_extraction_confidence_pass_ratio:
        reason_codes.append("extraction_confidence_watch")
    if authority_score < config.min_authority_score_watch_ratio:
        reason_codes.append("authority_tier_block")
    elif authority_score < config.min_authority_score_pass_ratio:
        reason_codes.append("authority_tier_watch")
    if conflict_pressure > config.max_conflict_pressure_watch_ratio:
        reason_codes.append("conflict_pressure_block")
    elif conflict_pressure > config.max_conflict_pressure_pass_ratio:
        reason_codes.append("conflict_pressure_watch")
    if fallback_coverage_score < config.min_fallback_coverage_watch_ratio:
        reason_codes.append("fallback_coverage_block")
    elif fallback_coverage_score < config.min_fallback_coverage_pass_ratio:
        reason_codes.append("fallback_coverage_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=True)


def _status_from_reasons(
    reason_codes: tuple[str, ...],
    reconciliation_score: Decimal,
    config: ResearchSourceScrapingSourceReconciliationConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reconciliation_score < config.min_reconciliation_watch_score:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if reconciliation_score < config.min_reconciliation_pass_score:
        return "watch"
    return "pass"


def _append_status_reason(reason_codes: tuple[str, ...], status: str) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        reason_codes + (f"source_reconciliation_{status}",),
    )


def _row_sort_key(
    row: ResearchSourceScrapingSourceReconciliationRow,
) -> tuple[
    int,
    Decimal,
    str,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    tuple[str, ...],
]:
    return (
        STATUS_WEIGHT[row.status],
        row.reconciliation_score,
        row.retrieval_tool,
        row.extraction_age_seconds,
        row.freshness_score,
        row.extraction_confidence_score,
        row.authority_score,
        row.conflict_pressure_score,
        row.fallback_coverage_score,
        row.reason_codes,
    )


def _report_status(
    rows: tuple[ResearchSourceScrapingSourceReconciliationRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScrapingSourceReconciliationRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {f"source_reconciliation_{status}"}
    for row in rows:
        reason_codes.update(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceScrapingSourceReconciliationRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScrapingSourceReconciliationReasonCodeCount, ...]:
    counts: Counter[str]
    if rows:
        counts = Counter(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
        )
    else:
        counts = Counter(reason_codes)
    return tuple(
        ResearchSourceScrapingSourceReconciliationReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: _reason_order_key(item[0]),
        )
    )


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _field_values(value: object, record_type: type[object]) -> dict[str, object]:
    _require_exact_type(value, record_type, record_type.__name__)
    return {field.name: getattr(value, field.name) for field in fields(record_type)}


def _revalidate_config(
    value: object,
) -> ResearchSourceScrapingSourceReconciliationConfig:
    if type(value) is not ResearchSourceScrapingSourceReconciliationConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScrapingSourceReconciliationConfig",
        )
    return ResearchSourceScrapingSourceReconciliationConfig(
        **_field_values(value, ResearchSourceScrapingSourceReconciliationConfig),
    )


def _revalidate_input(
    value: object,
) -> ResearchSourceScrapingSourceReconciliationInput:
    if type(value) is not ResearchSourceScrapingSourceReconciliationInput:
        raise ValueError(
            "inputs must contain ResearchSourceScrapingSourceReconciliationInput",
        )
    return ResearchSourceScrapingSourceReconciliationInput(
        **_field_values(value, ResearchSourceScrapingSourceReconciliationInput),
    )


def _revalidate_row(
    value: object,
) -> ResearchSourceScrapingSourceReconciliationRow:
    if type(value) is not ResearchSourceScrapingSourceReconciliationRow:
        raise ValueError(
            "rows must contain ResearchSourceScrapingSourceReconciliationRow",
        )
    return ResearchSourceScrapingSourceReconciliationRow(
        **_field_values(value, ResearchSourceScrapingSourceReconciliationRow),
    )


def _revalidate_reason_code_count(
    value: object,
) -> ResearchSourceScrapingSourceReconciliationReasonCodeCount:
    if type(value) is not ResearchSourceScrapingSourceReconciliationReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchSourceScrapingSourceReconciliationReasonCodeCount",
        )
    return ResearchSourceScrapingSourceReconciliationReasonCodeCount(
        **_field_values(
            value,
            ResearchSourceScrapingSourceReconciliationReasonCodeCount,
        ),
    )


def _revalidate_report_members(
    report: ResearchSourceScrapingSourceReconciliationReport,
) -> None:
    _revalidate_config(report.config)
    _normalize_rows(report.rows)
    _normalize_reason_code_counts(report.reason_code_counts)


def _normalize_rows(
    rows: tuple[ResearchSourceScrapingSourceReconciliationRow, ...],
) -> tuple[ResearchSourceScrapingSourceReconciliationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    revalidated_rows = tuple(_revalidate_row(row) for row in rows)
    sorted_rows = tuple(sorted(revalidated_rows, key=_row_sort_key))
    if revalidated_rows != sorted_rows:
        raise ValueError("rows must use canonical stable order")
    if len({row.row_label for row in revalidated_rows}) != len(revalidated_rows):
        raise ValueError("rows must have unique row_label values")
    for expected_rank, row in enumerate(revalidated_rows, start=1):
        if row.rank != _count_decimal(expected_rank):
            raise ValueError("rank must match canonical row order")
        expected_label = f"redacted-source-reconciliation-{expected_rank:06d}"
        if row.row_label != expected_label:
            raise ValueError("row_label must match canonical redacted rank")
    return revalidated_rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScrapingSourceReconciliationReasonCodeCount, ...],
) -> tuple[ResearchSourceScrapingSourceReconciliationReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    revalidated_counts = tuple(_revalidate_reason_code_count(item) for item in counts)
    sorted_counts = tuple(
        sorted(revalidated_counts, key=lambda item: _reason_order_key(item.reason_code)),
    )
    if revalidated_counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted")
    return revalidated_counts


def _validate_report_consistency(
    report: ResearchSourceScrapingSourceReconciliationReport,
) -> None:
    rows = report.rows
    config = report.config
    for expected_rank, row in enumerate(rows, start=1):
        if row.rank != _count_decimal(expected_rank):
            raise ValueError("rank must match canonical row order")
        if row.row_label != f"redacted-source-reconciliation-{expected_rank:06d}":
            raise ValueError("row_label must match canonical redacted rank")
        _validate_row_consistency(row, config)
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.pass_count != _count_decimal(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    with localcontext(DECIMAL_CONTEXT):
        expected_attention_count = _quantize(report.watch_count + report.block_count)
    if report.attention_count != expected_attention_count:
        raise ValueError("attention_count must equal watch_count plus block_count")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(rows, expected_status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.max_extraction_age_seconds != max(
        (row.extraction_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_extraction_age_seconds must match rows")
    averages = {
        "average_freshness_score": _average(row.freshness_score for row in rows),
        "average_extraction_confidence_score": _average(
            (row.extraction_confidence_score for row in rows),
        ),
        "average_authority_score": _average(row.authority_score for row in rows),
        "average_conflict_pressure_score": _average(
            (row.conflict_pressure_score for row in rows),
        ),
        "average_fallback_coverage_score": _average(
            (row.fallback_coverage_score for row in rows),
        ),
        "average_reconciliation_score": _average(
            (row.reconciliation_score for row in rows),
        ),
    }
    for field_name, expected in averages.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _validate_row_consistency(
    row: ResearchSourceScrapingSourceReconciliationRow,
    config: ResearchSourceScrapingSourceReconciliationConfig,
) -> None:
    expected_freshness_score = _freshness_score(row.extraction_age_seconds, config)
    if row.freshness_score != expected_freshness_score:
        raise ValueError("freshness_score must match extraction_age_seconds")
    if row.authority_score not in AUTHORITY_TIER_SCORES.values():
        raise ValueError("authority_score must match a supported authority tier")
    with localcontext(DECIMAL_CONTEXT):
        conflict_pressure = _quantize(ONE - row.conflict_pressure_score)
        expected_reconciliation_score = _quantize(
            (row.freshness_score * config.freshness_weight)
            + (
                row.extraction_confidence_score
                * config.extraction_confidence_weight
            )
            + (row.authority_score * config.authority_weight)
            + (row.conflict_pressure_score * config.conflict_pressure_weight)
            + (row.fallback_coverage_score * config.fallback_coverage_weight),
        )
    if row.reconciliation_score != expected_reconciliation_score:
        raise ValueError("reconciliation_score must match component scores")
    expected_reason_codes = _row_reason_codes(
        age_seconds=row.extraction_age_seconds,
        extraction_confidence_score=row.extraction_confidence_score,
        authority_score=row.authority_score,
        conflict_pressure=conflict_pressure,
        fallback_coverage_score=row.fallback_coverage_score,
        config=config,
    )
    expected_status = _status_from_reasons(
        expected_reason_codes,
        expected_reconciliation_score,
        config,
    )
    expected_reason_codes = _append_status_reason(
        expected_reason_codes,
        expected_status,
    )
    if row.status != expected_status:
        raise ValueError("status must match row scores and reasons")
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row scores and status")


def _report_digest(report: ResearchSourceScrapingSourceReconciliationReport) -> str:
    payload = asdict(report)
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value {value!r}")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_canonical_dataclass_schemas()
    json.dumps(payload, sort_keys=True, separators=(",", ":"))
    _reject_raw_public_numbers(payload)
    _reject_unsafe_public_payload("payload", payload)
    report = _report_from_public_payload(payload)
    canonical_payload = _json_ready(asdict(report))
    if canonical_payload != payload:
        raise ValueError("payload must match canonical report fields")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScrapingSourceReconciliationReport:
    _require_exact_payload_keys(
        "payload",
        payload,
        REPORT_PAYLOAD_FIELDS,
    )
    reason_code_counts_value = payload["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError("reason_code_counts must be a JSON list")
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON list")
    config = _config_from_public_payload(payload["config"])
    return ResearchSourceScrapingSourceReconciliationReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_string_from_public_payload(
            "config_version",
            payload["config_version"],
        ),
        input_count=_decimal_from_public_payload("input_count", payload["input_count"]),
        row_count=_decimal_from_public_payload("row_count", payload["row_count"]),
        pass_count=_decimal_from_public_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_public_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_public_payload("block_count", payload["block_count"]),
        attention_count=_decimal_from_public_payload(
            "attention_count",
            payload["attention_count"],
        ),
        max_extraction_age_seconds=_decimal_from_public_payload(
            "max_extraction_age_seconds",
            payload["max_extraction_age_seconds"],
        ),
        average_freshness_score=_decimal_from_public_payload(
            "average_freshness_score",
            payload["average_freshness_score"],
        ),
        average_extraction_confidence_score=_decimal_from_public_payload(
            "average_extraction_confidence_score",
            payload["average_extraction_confidence_score"],
        ),
        average_authority_score=_decimal_from_public_payload(
            "average_authority_score",
            payload["average_authority_score"],
        ),
        average_conflict_pressure_score=_decimal_from_public_payload(
            "average_conflict_pressure_score",
            payload["average_conflict_pressure_score"],
        ),
        average_fallback_coverage_score=_decimal_from_public_payload(
            "average_fallback_coverage_score",
            payload["average_fallback_coverage_score"],
        ),
        average_reconciliation_score=_decimal_from_public_payload(
            "average_reconciliation_score",
            payload["average_reconciliation_score"],
        ),
        status=_string_from_public_payload("status", payload["status"]),
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_public_payload(value)
            for value in reason_code_counts_value
        ),
        rows=tuple(_row_from_public_payload(value) for value in rows_value),
        config=config,
        derived_validation_digest=_string_from_public_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_bool_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_public_payload("report_only", payload["report_only"]),
        readonly=_bool_from_public_payload("readonly", payload["readonly"]),
    )


def _config_from_public_payload(
    value: object,
) -> ResearchSourceScrapingSourceReconciliationConfig:
    if type(value) is not dict:
        raise ValueError("config must be a JSON object")
    _require_exact_payload_keys(
        "config",
        value,
        CONFIG_PAYLOAD_FIELDS,
    )
    config_values: dict[str, object] = {}
    for field_name in CONFIG_PAYLOAD_FIELDS:
        field_value = value[field_name]
        if field_name == "config_version":
            config_values[field_name] = _string_from_public_payload(
                field_name,
                field_value,
            )
        elif field_name in {"paper_only", "report_only", "readonly"}:
            config_values[field_name] = _bool_from_public_payload(
                field_name,
                field_value,
            )
        else:
            config_values[field_name] = _decimal_from_public_payload(
                field_name,
                field_value,
            )
    return ResearchSourceScrapingSourceReconciliationConfig(**config_values)


def _row_from_public_payload(
    value: object,
) -> ResearchSourceScrapingSourceReconciliationRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_exact_payload_keys(
        "row",
        value,
        ROW_PAYLOAD_FIELDS,
    )
    return ResearchSourceScrapingSourceReconciliationRow(
        row_label=_string_from_public_payload("row_label", value["row_label"]),
        rank=_decimal_from_public_payload("rank", value["rank"]),
        retrieval_tool=_string_from_public_payload(
            "retrieval_tool",
            value["retrieval_tool"],
        ),
        extraction_age_seconds=_decimal_from_public_payload(
            "extraction_age_seconds",
            value["extraction_age_seconds"],
        ),
        freshness_score=_decimal_from_public_payload(
            "freshness_score",
            value["freshness_score"],
        ),
        extraction_confidence_score=_decimal_from_public_payload(
            "extraction_confidence_score",
            value["extraction_confidence_score"],
        ),
        authority_score=_decimal_from_public_payload(
            "authority_score",
            value["authority_score"],
        ),
        conflict_pressure_score=_decimal_from_public_payload(
            "conflict_pressure_score",
            value["conflict_pressure_score"],
        ),
        fallback_coverage_score=_decimal_from_public_payload(
            "fallback_coverage_score",
            value["fallback_coverage_score"],
        ),
        reconciliation_score=_decimal_from_public_payload(
            "reconciliation_score",
            value["reconciliation_score"],
        ),
        status=_string_from_public_payload("status", value["status"]),
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            value["reason_codes"],
        ),
        paper_only=_bool_from_public_payload("paper_only", value["paper_only"]),
        report_only=_bool_from_public_payload("report_only", value["report_only"]),
        readonly=_bool_from_public_payload("readonly", value["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceScrapingSourceReconciliationReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_exact_payload_keys(
        "reason_code_count",
        value,
        REASON_CODE_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchSourceScrapingSourceReconciliationReasonCodeCount(
        reason_code=_string_from_public_payload(
            "reason_code",
            value["reason_code"],
        ),
        count=_decimal_from_public_payload("count", value["count"]),
        paper_only=_bool_from_public_payload("paper_only", value["paper_only"]),
        report_only=_bool_from_public_payload("report_only", value["report_only"]),
        readonly=_bool_from_public_payload("readonly", value["readonly"]),
    )


def _require_exact_payload_keys(
    label: str,
    payload: dict[object, object],
    expected_fields: tuple[str, ...],
) -> None:
    if tuple(payload) != expected_fields:
        raise ValueError(f"{label} must have the exact canonical schema")


def _require_canonical_dataclass_schemas() -> None:
    schemas = (
        (
            "config",
            ResearchSourceScrapingSourceReconciliationConfig,
            CONFIG_PAYLOAD_FIELDS,
        ),
        (
            "row",
            ResearchSourceScrapingSourceReconciliationRow,
            ROW_PAYLOAD_FIELDS,
        ),
        (
            "reason_code_count",
            ResearchSourceScrapingSourceReconciliationReasonCodeCount,
            REASON_CODE_COUNT_PAYLOAD_FIELDS,
        ),
        (
            "report",
            ResearchSourceScrapingSourceReconciliationReport,
            REPORT_PAYLOAD_FIELDS,
        ),
    )
    for label, record_type, expected_fields in schemas:
        if tuple(field.name for field in fields(record_type)) != expected_fields:
            raise ValueError(f"{label} dataclass must match canonical schema")


def _string_from_public_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _bool_from_public_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    text = _string_from_public_payload(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    return _as_utc(field_name, parsed)


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    text = _string_from_public_payload(field_name, value)
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc


def _reason_codes_from_public_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON list")
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
    return tuple(value)


def _reject_raw_public_numbers(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must not contain raw numeric values")
    if type(value) is dict:
        for key, item in value.items():
            _reject_raw_public_numbers(key)
            _reject_raw_public_numbers(item)
    elif type(value) is list:
        for item in value:
            _reject_raw_public_numbers(item)
    elif type(value) is not str:
        raise ValueError("public payload must contain JSON-ready values")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    rendered_values = _public_strings(value)
    for rendered in rendered_values:
        folded = rendered.casefold()
        if any(fragment in folded for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe source material")


def _public_strings(value: object) -> tuple[str, ...]:
    if type(value) is dict:
        strings: list[str] = []
        for key, item in value.items():
            strings.extend(_public_strings(key))
            strings.extend(_public_strings(item))
        return tuple(strings)
    if type(value) in (tuple, list):
        strings = []
        for item in value:
            strings.extend(_public_strings(item))
        return tuple(strings)
    if hasattr(value, "__dataclass_fields__"):
        return _public_strings(asdict(value))
    if type(value) is str:
        return (value,)
    return ()


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=_reason_order_key))


def _reason_order_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_CODE_SEQUENCE:
        return (REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    return (len(REASON_CODE_SEQUENCE), reason_code)


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must contain safe reason codes")
    if any(fragment in value.casefold() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe source material")


def _require_public_identifier(field_name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe public identifier")
    if any(fragment in value.casefold() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe source material")


def _require_private_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty private string")


def _require_member(field_name: str, value: str, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_status(field_name: str, value: str) -> None:
    _require_member(field_name, value, STATUSES)


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw)


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize(raw)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive after quantization")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return _quantize(raw)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return _quantize(raw)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    return _quantize(_require_raw_decimal(field_name, value))


def _require_raw_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("decimal value must be finite and quantizable") from exc
    if normalized.is_zero():
        return ZERO
    return normalized
