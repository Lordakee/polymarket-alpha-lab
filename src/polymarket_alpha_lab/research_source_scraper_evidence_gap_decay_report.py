"""Pure report-only source scraper evidence gap decay reducer.

Callers provide already-sanitized scraper evidence telemetry. This module does
not read databases, call networks, touch wallets, size positions, create orders,
or recommend execution. It only returns a deterministic public report with
redacted row labels, Decimal-only numerics, and SHA-256 payload validation.
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


DEFAULT_RESEARCH_SOURCE_SCRAPER_EVIDENCE_GAP_DECAY_REPORT_CONFIG_VERSION = (
    "research-source-scraper-evidence-gap-decay-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
SCRAPER_FAMILIES = ("agent_reach", "generic", "scrapling")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

NO_INPUTS_REASON = "scraper_evidence_gap_decay_no_inputs"
PASS_REASON = "scraper_evidence_gap_decay_pass"
WATCH_REASON = "scraper_evidence_gap_decay_watch"
BLOCK_REASON = "scraper_evidence_gap_decay_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "evidence_age_decay_block",
    "evidence_age_decay_watch",
    "coverage_gap_block",
    "coverage_gap_watch",
    "primary_evidence_gap_block",
    "primary_evidence_gap_watch",
    "parser_confidence_gap_block",
    "parser_confidence_gap_watch",
    "recheck_gap_block",
    "recheck_gap_watch",
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
    "wallet",
    "order",
    "trade",
    "live",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPER_EVIDENCE_GAP_DECAY_REPORT_CONFIG_VERSION",
    "ResearchSourceScraperEvidenceGapDecayConfig",
    "ResearchSourceScraperEvidenceGapDecayInput",
    "ResearchSourceScraperEvidenceGapDecayReasonCodeCount",
    "ResearchSourceScraperEvidenceGapDecayReport",
    "ResearchSourceScraperEvidenceGapDecayRow",
    "STATUSES",
    "build_research_source_scraper_evidence_gap_decay_report",
    "research_source_scraper_evidence_gap_decay_report_digest",
    "research_source_scraper_evidence_gap_decay_report_payload",
    "validate_research_source_scraper_evidence_gap_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraperEvidenceGapDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPER_EVIDENCE_GAP_DECAY_REPORT_CONFIG_VERSION
    )
    fresh_evidence_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_block_age_seconds: Decimal = Decimal("86400.000000")
    recheck_due_after_seconds: Decimal = Decimal("7200.000000")
    recheck_block_after_seconds: Decimal = Decimal("86400.000000")
    min_coverage_pass_ratio: Decimal = Decimal("0.900000")
    min_coverage_watch_ratio: Decimal = Decimal("0.650000")
    min_primary_coverage_pass_ratio: Decimal = Decimal("0.800000")
    min_primary_coverage_watch_ratio: Decimal = Decimal("0.500000")
    min_parser_confidence_pass_ratio: Decimal = Decimal("0.850000")
    min_parser_confidence_watch_ratio: Decimal = Decimal("0.600000")
    watch_gap_decay_score: Decimal = Decimal("0.350000")
    block_gap_decay_score: Decimal = Decimal("0.700000")
    evidence_age_weight: Decimal = Decimal("0.300000")
    coverage_gap_weight: Decimal = Decimal("0.300000")
    primary_gap_weight: Decimal = Decimal("0.200000")
    parser_gap_weight: Decimal = Decimal("0.100000")
    recheck_gap_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperEvidenceGapDecayConfig:
            raise TypeError(
                "ResearchSourceScraperEvidenceGapDecayConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperEvidenceGapDecayConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPER_EVIDENCE_GAP_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_evidence_max_age_seconds",
            "stale_evidence_block_age_seconds",
            "recheck_due_after_seconds",
            "recheck_block_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_evidence_max_age_seconds >= self.stale_evidence_block_age_seconds:
            raise ValueError(
                "fresh_evidence_max_age_seconds must be below "
                "stale_evidence_block_age_seconds",
            )
        if self.recheck_due_after_seconds >= self.recheck_block_after_seconds:
            raise ValueError(
                "recheck_due_after_seconds must be below recheck_block_after_seconds",
            )
        for field_name in (
            "min_coverage_pass_ratio",
            "min_coverage_watch_ratio",
            "min_primary_coverage_pass_ratio",
            "min_primary_coverage_watch_ratio",
            "min_parser_confidence_pass_ratio",
            "min_parser_confidence_watch_ratio",
            "watch_gap_decay_score",
            "block_gap_decay_score",
            "evidence_age_weight",
            "coverage_gap_weight",
            "primary_gap_weight",
            "parser_gap_weight",
            "recheck_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.min_coverage_watch_ratio > self.min_coverage_pass_ratio:
            raise ValueError("coverage watch threshold must not exceed pass threshold")
        if (
            self.min_primary_coverage_watch_ratio
            > self.min_primary_coverage_pass_ratio
        ):
            raise ValueError(
                "primary coverage watch threshold must not exceed pass threshold",
            )
        if (
            self.min_parser_confidence_watch_ratio
            > self.min_parser_confidence_pass_ratio
        ):
            raise ValueError(
                "parser confidence watch threshold must not exceed pass threshold",
            )
        if self.block_gap_decay_score <= self.watch_gap_decay_score:
            raise ValueError("block_gap_decay_score must exceed watch_gap_decay_score")
        with localcontext(DECIMAL_CONTEXT):
            weight_sum = _quantize(
                self.evidence_age_weight
                + self.coverage_gap_weight
                + self.primary_gap_weight
                + self.parser_gap_weight
                + self.recheck_gap_weight,
            )
        if weight_sum != ONE:
            raise ValueError("gap decay weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraperEvidenceGapDecayInput:
    private_evidence_ref: str
    scraper_family: str
    observed_at: datetime
    last_rechecked_at: datetime
    expected_evidence_count: Decimal
    observed_evidence_count: Decimal
    primary_evidence_count: Decimal
    parser_confidence_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperEvidenceGapDecayInput:
            raise TypeError(
                "ResearchSourceScraperEvidenceGapDecayInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperEvidenceGapDecayInput, "input")
        _require_private_string("private_evidence_ref", self.private_evidence_ref)
        _require_member("scraper_family", self.scraper_family, SCRAPER_FAMILIES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_rechecked_at",
            _as_utc("last_rechecked_at", self.last_rechecked_at),
        )
        object.__setattr__(
            self,
            "expected_evidence_count",
            _normalize_positive_count(
                "expected_evidence_count",
                self.expected_evidence_count,
            ),
        )
        for field_name in ("observed_evidence_count", "primary_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "parser_confidence_ratio",
            _normalize_probability("parser_confidence_ratio", self.parser_confidence_ratio),
        )
        if self.observed_evidence_count > self.expected_evidence_count:
            raise ValueError(
                "observed_evidence_count must not exceed expected_evidence_count",
            )
        if self.primary_evidence_count > self.observed_evidence_count:
            raise ValueError(
                "primary_evidence_count must not exceed observed_evidence_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraperEvidenceGapDecayRow:
    row_label: str
    scraper_family: str
    evidence_age_seconds: Decimal
    recheck_age_seconds: Decimal
    coverage_ratio: Decimal
    primary_coverage_ratio: Decimal
    parser_confidence_ratio: Decimal
    evidence_age_decay_score: Decimal
    coverage_gap_score: Decimal
    primary_evidence_gap_score: Decimal
    parser_confidence_gap_score: Decimal
    recheck_gap_score: Decimal
    gap_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperEvidenceGapDecayRow:
            raise TypeError(
                "ResearchSourceScraperEvidenceGapDecayRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperEvidenceGapDecayRow, "row")
        _require_public_identifier("row_label", self.row_label)
        _require_member("scraper_family", self.scraper_family, SCRAPER_FAMILIES)
        for field_name in ("evidence_age_seconds", "recheck_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_ratio",
            "primary_coverage_ratio",
            "parser_confidence_ratio",
            "evidence_age_decay_score",
            "coverage_gap_score",
            "primary_evidence_gap_score",
            "parser_confidence_gap_score",
            "recheck_gap_score",
            "gap_decay_score",
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
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraperEvidenceGapDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperEvidenceGapDecayReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraperEvidenceGapDecayReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraperEvidenceGapDecayReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraperEvidenceGapDecayReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    max_evidence_age_seconds: Decimal
    max_recheck_age_seconds: Decimal
    average_coverage_ratio: Decimal
    average_primary_coverage_ratio: Decimal
    average_parser_confidence_ratio: Decimal
    average_gap_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraperEvidenceGapDecayReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraperEvidenceGapDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraperEvidenceGapDecayReport:
            raise TypeError(
                "ResearchSourceScraperEvidenceGapDecayReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraperEvidenceGapDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPER_EVIDENCE_GAP_DECAY_REPORT_CONFIG_VERSION
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
        for field_name in ("max_evidence_age_seconds", "max_recheck_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_coverage_ratio",
            "average_primary_coverage_ratio",
            "average_parser_confidence_ratio",
            "average_gap_decay_score",
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
        return research_source_scraper_evidence_gap_decay_report_payload(self)


_ROW_SCHEMA = tuple(field.name for field in fields(ResearchSourceScraperEvidenceGapDecayRow))
_REASON_CODE_COUNT_SCHEMA = tuple(
    field.name for field in fields(ResearchSourceScraperEvidenceGapDecayReasonCodeCount)
)
_REPORT_SCHEMA = tuple(
    field.name for field in fields(ResearchSourceScraperEvidenceGapDecayReport)
)
_UNSIGNED_REPORT_SCHEMA = tuple(
    field_name for field_name in _REPORT_SCHEMA if field_name != "derived_validation_digest"
)


def build_research_source_scraper_evidence_gap_decay_report(
    inputs: Iterable[ResearchSourceScraperEvidenceGapDecayInput],
    *,
    config: ResearchSourceScraperEvidenceGapDecayConfig,
    generated_at: datetime,
) -> ResearchSourceScraperEvidenceGapDecayReport:
    config = _revalidate_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        if item.last_rechecked_at > generated_at:
            raise ValueError("last_rechecked_at cannot be after generated_at")

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
    attention_count = _add_decimal(watch_count, block_count)
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)

    return ResearchSourceScraperEvidenceGapDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        row_count=_count_decimal(len(rows)),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_count=attention_count,
        max_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in rows),
            default=ZERO,
        ),
        max_recheck_age_seconds=max(
            (row.recheck_age_seconds for row in rows),
            default=ZERO,
        ),
        average_coverage_ratio=_average(row.coverage_ratio for row in rows),
        average_primary_coverage_ratio=_average(
            (row.primary_coverage_ratio for row in rows),
        ),
        average_parser_confidence_ratio=_average(
            (row.parser_confidence_ratio for row in rows),
        ),
        average_gap_decay_score=_average(row.gap_decay_score for row in rows),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, status),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scraper_evidence_gap_decay_report_payload(
    report: ResearchSourceScraperEvidenceGapDecayReport,
) -> dict[str, Any]:
    report = _revalidate_report(report)
    payload = _canonical_report_payload(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scraper_evidence_gap_decay_report_digest(
    report: ResearchSourceScraperEvidenceGapDecayReport,
) -> str:
    payload = research_source_scraper_evidence_gap_decay_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_scraper_evidence_gap_decay_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        report = _report_from_payload(payload)
        return _values_match_exact(payload, _canonical_report_payload(report))
    except (TypeError, ValueError):
        return False


def _normalize_inputs(
    inputs: Iterable[ResearchSourceScraperEvidenceGapDecayInput],
) -> tuple[ResearchSourceScraperEvidenceGapDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for item in normalized:
        _revalidate_input(item)
    return tuple(sorted((_revalidate_input(item) for item in normalized), key=_input_sort_key))


def _input_sort_key(
    item: ResearchSourceScraperEvidenceGapDecayInput,
) -> tuple[str, str, str, str, Decimal, Decimal, Decimal, Decimal]:
    return (
        item.private_evidence_ref,
        item.scraper_family,
        item.observed_at.isoformat(),
        item.last_rechecked_at.isoformat(),
        item.expected_evidence_count,
        item.observed_evidence_count,
        item.primary_evidence_count,
        item.parser_confidence_ratio,
    )


def _row_from_input(
    item: ResearchSourceScraperEvidenceGapDecayInput,
    *,
    row_number: int,
    config: ResearchSourceScraperEvidenceGapDecayConfig,
    generated_at: datetime,
) -> ResearchSourceScraperEvidenceGapDecayRow:
    evidence_age_seconds = _age_seconds(generated_at, item.observed_at)
    recheck_age_seconds = _age_seconds(generated_at, item.last_rechecked_at)
    coverage_ratio = _safe_ratio(item.observed_evidence_count, item.expected_evidence_count)
    primary_coverage_ratio = _safe_ratio(
        item.primary_evidence_count,
        item.expected_evidence_count,
    )
    evidence_age_decay_score = _age_decay_score(
        evidence_age_seconds,
        fresh_after=config.fresh_evidence_max_age_seconds,
        block_after=config.stale_evidence_block_age_seconds,
    )
    coverage_gap_score = _subtract_from_one(coverage_ratio)
    primary_gap_score = _subtract_from_one(primary_coverage_ratio)
    parser_gap_score = _subtract_from_one(item.parser_confidence_ratio)
    recheck_gap_score = _age_decay_score(
        recheck_age_seconds,
        fresh_after=config.recheck_due_after_seconds,
        block_after=config.recheck_block_after_seconds,
    )
    gap_decay_score = _weighted_gap_decay_score(
        evidence_age_decay_score=evidence_age_decay_score,
        coverage_gap_score=coverage_gap_score,
        primary_gap_score=primary_gap_score,
        parser_gap_score=parser_gap_score,
        recheck_gap_score=recheck_gap_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_age_decay_score=evidence_age_decay_score,
        coverage_ratio=coverage_ratio,
        primary_coverage_ratio=primary_coverage_ratio,
        parser_confidence_ratio=item.parser_confidence_ratio,
        recheck_gap_score=recheck_gap_score,
        gap_decay_score=gap_decay_score,
        config=config,
    )
    status = _row_status(reason_codes, gap_decay_score, config)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*reason_codes, _status_reason(status)),
    )
    return ResearchSourceScraperEvidenceGapDecayRow(
        row_label=f"redacted-evidence-gap-decay-{row_number:06d}",
        scraper_family=item.scraper_family,
        evidence_age_seconds=evidence_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        coverage_ratio=coverage_ratio,
        primary_coverage_ratio=primary_coverage_ratio,
        parser_confidence_ratio=item.parser_confidence_ratio,
        evidence_age_decay_score=evidence_age_decay_score,
        coverage_gap_score=coverage_gap_score,
        primary_evidence_gap_score=primary_gap_score,
        parser_confidence_gap_score=parser_gap_score,
        recheck_gap_score=recheck_gap_score,
        gap_decay_score=gap_decay_score,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _age_decay_score(
    age_seconds: Decimal,
    *,
    fresh_after: Decimal,
    block_after: Decimal,
) -> Decimal:
    if age_seconds <= fresh_after:
        return ZERO
    if age_seconds >= block_after:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _safe_ratio(age_seconds - fresh_after, block_after - fresh_after)


def _row_reason_codes(
    *,
    evidence_age_decay_score: Decimal,
    coverage_ratio: Decimal,
    primary_coverage_ratio: Decimal,
    parser_confidence_ratio: Decimal,
    recheck_gap_score: Decimal,
    gap_decay_score: Decimal,
    config: ResearchSourceScraperEvidenceGapDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_age_decay_score == ONE:
        reason_codes.append("evidence_age_decay_block")
    elif evidence_age_decay_score > ZERO:
        reason_codes.append("evidence_age_decay_watch")

    if coverage_ratio < config.min_coverage_watch_ratio:
        reason_codes.append("coverage_gap_block")
    elif coverage_ratio < config.min_coverage_pass_ratio:
        reason_codes.append("coverage_gap_watch")

    if primary_coverage_ratio < config.min_primary_coverage_watch_ratio:
        reason_codes.append("primary_evidence_gap_block")
    elif primary_coverage_ratio < config.min_primary_coverage_pass_ratio:
        reason_codes.append("primary_evidence_gap_watch")

    if parser_confidence_ratio < config.min_parser_confidence_watch_ratio:
        reason_codes.append("parser_confidence_gap_block")
    elif parser_confidence_ratio < config.min_parser_confidence_pass_ratio:
        reason_codes.append("parser_confidence_gap_watch")

    if recheck_gap_score == ONE:
        reason_codes.append("recheck_gap_block")
    elif recheck_gap_score > ZERO:
        reason_codes.append("recheck_gap_watch")

    if not reason_codes and gap_decay_score >= config.watch_gap_decay_score:
        reason_codes.append("coverage_gap_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(
    reason_codes: tuple[str, ...],
    gap_decay_score: Decimal,
    config: ResearchSourceScraperEvidenceGapDecayConfig,
) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if gap_decay_score >= config.block_gap_decay_score:
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if gap_decay_score >= config.watch_gap_decay_score:
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


def _report_status(rows: tuple[ResearchSourceScraperEvidenceGapDecayRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraperEvidenceGapDecayRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, BLOCK_REASON)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes.add(_status_reason(status))
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceScraperEvidenceGapDecayRow, ...],
    status: str,
) -> tuple[ResearchSourceScraperEvidenceGapDecayReasonCodeCount, ...]:
    if not rows:
        counts = Counter(_report_reason_codes(rows, status))
    else:
        counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
        counts[_status_reason(status)] += 1
    return tuple(
        ResearchSourceScraperEvidenceGapDecayReasonCodeCount(
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
    rows: tuple[ResearchSourceScraperEvidenceGapDecayRow, ...],
) -> tuple[ResearchSourceScraperEvidenceGapDecayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    revalidated = tuple(_revalidate_row(row) for row in normalized)
    if len({row.row_label for row in revalidated}) != len(revalidated):
        raise ValueError("rows must have unique row_label values")
    return tuple(sorted(revalidated, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceScraperEvidenceGapDecayRow) -> tuple[int, str, str]:
    return (STATUS_WEIGHT[row.status], row.row_label, row.scraper_family)


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraperEvidenceGapDecayReasonCodeCount, ...],
) -> tuple[ResearchSourceScraperEvidenceGapDecayReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    revalidated = tuple(_revalidate_reason_code_count(count) for count in normalized)
    if len({count.reason_code for count in revalidated}) != len(revalidated):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return tuple(
        sorted(
            revalidated,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _validate_report_consistency(
    report: ResearchSourceScraperEvidenceGapDecayReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be in deterministic order")
    if report.reason_code_counts != tuple(
        sorted(
            report.reason_code_counts,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must be in deterministic order")
    for row in report.rows:
        _validate_row_consistency(row)
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.attention_count != _add_decimal(
        report.watch_count,
        report.block_count,
    ):
        raise ValueError("attention_count must match watch and block counts")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows and status")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.status):
        raise ValueError("reason_code_counts must match rows and status")
    if report.max_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.max_recheck_age_seconds != max(
        (row.recheck_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_recheck_age_seconds must match rows")
    expected_averages = {
        "average_coverage_ratio": _average(row.coverage_ratio for row in report.rows),
        "average_primary_coverage_ratio": _average(
            (row.primary_coverage_ratio for row in report.rows),
        ),
        "average_parser_confidence_ratio": _average(
            (row.parser_confidence_ratio for row in report.rows),
        ),
        "average_gap_decay_score": _average(row.gap_decay_score for row in report.rows),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _validate_row_consistency(row: ResearchSourceScraperEvidenceGapDecayRow) -> None:
    config = _CANONICAL_CONFIG
    expected_evidence_age_decay_score = _age_decay_score(
        row.evidence_age_seconds,
        fresh_after=config.fresh_evidence_max_age_seconds,
        block_after=config.stale_evidence_block_age_seconds,
    )
    expected_coverage_gap_score = _subtract_from_one(row.coverage_ratio)
    expected_primary_gap_score = _subtract_from_one(row.primary_coverage_ratio)
    expected_parser_gap_score = _subtract_from_one(row.parser_confidence_ratio)
    expected_recheck_gap_score = _age_decay_score(
        row.recheck_age_seconds,
        fresh_after=config.recheck_due_after_seconds,
        block_after=config.recheck_block_after_seconds,
    )
    expected_gap_decay_score = _weighted_gap_decay_score(
        evidence_age_decay_score=expected_evidence_age_decay_score,
        coverage_gap_score=expected_coverage_gap_score,
        primary_gap_score=expected_primary_gap_score,
        parser_gap_score=expected_parser_gap_score,
        recheck_gap_score=expected_recheck_gap_score,
        config=config,
    )
    expected_reason_codes = _row_reason_codes(
        evidence_age_decay_score=expected_evidence_age_decay_score,
        coverage_ratio=row.coverage_ratio,
        primary_coverage_ratio=row.primary_coverage_ratio,
        parser_confidence_ratio=row.parser_confidence_ratio,
        recheck_gap_score=expected_recheck_gap_score,
        gap_decay_score=expected_gap_decay_score,
        config=config,
    )
    expected_status = _row_status(expected_reason_codes, expected_gap_decay_score, config)
    expected_reason_codes = _normalize_reason_codes(
        "reason_codes",
        (*expected_reason_codes, _status_reason(expected_status)),
    )
    expected_values = {
        "evidence_age_decay_score": expected_evidence_age_decay_score,
        "coverage_gap_score": expected_coverage_gap_score,
        "primary_evidence_gap_score": expected_primary_gap_score,
        "parser_confidence_gap_score": expected_parser_gap_score,
        "recheck_gap_score": expected_recheck_gap_score,
        "gap_decay_score": expected_gap_decay_score,
        "status": expected_status,
        "reason_codes": expected_reason_codes,
    }
    for field_name, expected_value in expected_values.items():
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match row evidence")


def _subtract_from_one(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(ONE - value)


def _revalidate_config(
    config: object,
) -> ResearchSourceScraperEvidenceGapDecayConfig:
    rebuilt = _rebuild_public_dataclass(
        config,
        ResearchSourceScraperEvidenceGapDecayConfig,
        "config",
    )
    if not _values_match_exact(rebuilt, _CANONICAL_CONFIG):
        raise ValueError("config must match the supported canonical configuration")
    return rebuilt


def _revalidate_input(
    value: object,
) -> ResearchSourceScraperEvidenceGapDecayInput:
    return _rebuild_public_dataclass(
        value,
        ResearchSourceScraperEvidenceGapDecayInput,
        "input",
    )


def _revalidate_row(
    value: object,
) -> ResearchSourceScraperEvidenceGapDecayRow:
    return _rebuild_public_dataclass(
        value,
        ResearchSourceScraperEvidenceGapDecayRow,
        "row",
    )


def _revalidate_reason_code_count(
    value: object,
) -> ResearchSourceScraperEvidenceGapDecayReasonCodeCount:
    return _rebuild_public_dataclass(
        value,
        ResearchSourceScraperEvidenceGapDecayReasonCodeCount,
        "reason count",
    )


def _revalidate_report(
    value: object,
) -> ResearchSourceScraperEvidenceGapDecayReport:
    return _rebuild_public_dataclass(
        value,
        ResearchSourceScraperEvidenceGapDecayReport,
        "report",
    )


def _rebuild_public_dataclass(
    value: object,
    expected_type: type[Any],
    label: str,
) -> Any:
    _require_exact_type(value, expected_type, label)
    rebuilt = expected_type(
        **{field.name: getattr(value, field.name) for field in fields(expected_type)},
    )
    if not _values_match_exact(value, rebuilt):
        raise ValueError(f"{label} must remain canonically normalized")
    return rebuilt


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
        return _safe_ratio(sum(normalized, ZERO), _count_decimal(len(normalized)))


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


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _weighted_gap_decay_score(
    *,
    evidence_age_decay_score: Decimal,
    coverage_gap_score: Decimal,
    primary_gap_score: Decimal,
    parser_gap_score: Decimal,
    recheck_gap_score: Decimal,
    config: ResearchSourceScraperEvidenceGapDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            evidence_age_decay_score * config.evidence_age_weight
            + coverage_gap_score * config.coverage_gap_weight
            + primary_gap_score * config.primary_gap_weight
            + parser_gap_score * config.parser_gap_weight
            + recheck_gap_score * config.recheck_gap_weight,
        )


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    return ZERO if normalized.is_zero() else normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_raw_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_raw_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    _require_raw_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _normalize_nonnegative_count(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    _require_raw_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        if value != value.to_integral_value():
            raise ValueError(f"{field_name} must be a whole number")
    return _quantize(value)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    _require_raw_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value)


def _require_raw_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_raw_decimal(field_name, value)
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


def _report_digest(report: ResearchSourceScraperEvidenceGapDecayReport) -> str:
    payload = _canonical_report_payload(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _validate_unsigned_report_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _canonical_report_payload(
    report: ResearchSourceScraperEvidenceGapDecayReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


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
    _validate_safe_public_value(ready, label=label)


def _validate_safe_public_value(value: Any, *, label: str = "payload") -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _validate_safe_public_value(item, label=key)
        return
    if type(value) is list:
        for item in value:
            _validate_safe_public_value(item, label=label)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numerics must be Decimal strings")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    normalized = value.casefold()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not expose unsafe public payload text")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _validate_report_mapping(payload, include_digest=True)


def _validate_unsigned_report_payload(payload: dict[str, Any]) -> None:
    _validate_report_mapping(payload, include_digest=False)


def _validate_report_mapping(payload: dict[str, Any], *, include_digest: bool) -> None:
    expected_schema = _REPORT_SCHEMA if include_digest else _UNSIGNED_REPORT_SCHEMA
    _require_mapping_schema(payload, expected_schema, "report payload")
    _validate_datetime_payload("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_SOURCE_SCRAPER_EVIDENCE_GAP_DECAY_REPORT_CONFIG_VERSION
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
        _decimal_from_payload(field_name, payload[field_name], _normalize_nonnegative_count)
    for field_name in ("max_evidence_age_seconds", "max_recheck_age_seconds"):
        _decimal_from_payload(
            field_name,
            payload[field_name],
            _normalize_nonnegative_decimal,
        )
    for field_name in (
        "average_coverage_ratio",
        "average_primary_coverage_ratio",
        "average_parser_confidence_ratio",
        "average_gap_decay_score",
    ):
        _decimal_from_payload(field_name, payload[field_name], _normalize_probability)
    _require_status("status", payload["status"])
    _reason_codes_from_payload("reason_codes", payload["reason_codes"])
    _reason_code_counts_from_payload(payload["reason_code_counts"])
    _rows_from_payload(payload["rows"])
    if include_digest:
        _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _validate_safe_public_value(payload)


def _require_mapping_schema(
    value: object,
    schema: tuple[str, ...],
    label: str,
) -> None:
    if type(value) is not dict or tuple(value) != schema:
        raise ValueError(f"{label} must use the canonical schema and key order")


def _validate_datetime_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must use canonical UTC ISO-8601")
    return normalized


def _decimal_from_payload(
    field_name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be canonically quantized")
    return normalized


def _reason_codes_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    normalized = _normalize_reason_codes(field_name, tuple(value))
    if tuple(value) != normalized:
        raise ValueError(f"{field_name} must be in canonical order")
    return normalized


def _reason_code_counts_from_payload(
    value: object,
) -> tuple[ResearchSourceScraperEvidenceGapDecayReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    result = []
    for item in value:
        _require_mapping_schema(item, _REASON_CODE_COUNT_SCHEMA, "reason code count")
        result.append(
            ResearchSourceScraperEvidenceGapDecayReasonCodeCount(
                reason_code=item["reason_code"],
                count=_decimal_from_payload(
                    "count",
                    item["count"],
                    _normalize_positive_count,
                ),
                paper_only=item["paper_only"],
                report_only=item["report_only"],
                readonly=item["readonly"],
            ),
        )
    normalized = _normalize_reason_code_counts(tuple(result))
    if tuple(result) != normalized:
        raise ValueError("reason_code_counts must be in canonical order")
    return normalized


def _rows_from_payload(
    value: object,
) -> tuple[ResearchSourceScraperEvidenceGapDecayRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a JSON array")
    result = []
    for item in value:
        _require_mapping_schema(item, _ROW_SCHEMA, "row")
        result.append(
            ResearchSourceScraperEvidenceGapDecayRow(
                row_label=item["row_label"],
                scraper_family=item["scraper_family"],
                evidence_age_seconds=_decimal_from_payload(
                    "evidence_age_seconds",
                    item["evidence_age_seconds"],
                    _normalize_nonnegative_decimal,
                ),
                recheck_age_seconds=_decimal_from_payload(
                    "recheck_age_seconds",
                    item["recheck_age_seconds"],
                    _normalize_nonnegative_decimal,
                ),
                coverage_ratio=_decimal_from_payload(
                    "coverage_ratio",
                    item["coverage_ratio"],
                    _normalize_probability,
                ),
                primary_coverage_ratio=_decimal_from_payload(
                    "primary_coverage_ratio",
                    item["primary_coverage_ratio"],
                    _normalize_probability,
                ),
                parser_confidence_ratio=_decimal_from_payload(
                    "parser_confidence_ratio",
                    item["parser_confidence_ratio"],
                    _normalize_probability,
                ),
                evidence_age_decay_score=_decimal_from_payload(
                    "evidence_age_decay_score",
                    item["evidence_age_decay_score"],
                    _normalize_probability,
                ),
                coverage_gap_score=_decimal_from_payload(
                    "coverage_gap_score",
                    item["coverage_gap_score"],
                    _normalize_probability,
                ),
                primary_evidence_gap_score=_decimal_from_payload(
                    "primary_evidence_gap_score",
                    item["primary_evidence_gap_score"],
                    _normalize_probability,
                ),
                parser_confidence_gap_score=_decimal_from_payload(
                    "parser_confidence_gap_score",
                    item["parser_confidence_gap_score"],
                    _normalize_probability,
                ),
                recheck_gap_score=_decimal_from_payload(
                    "recheck_gap_score",
                    item["recheck_gap_score"],
                    _normalize_probability,
                ),
                gap_decay_score=_decimal_from_payload(
                    "gap_decay_score",
                    item["gap_decay_score"],
                    _normalize_probability,
                ),
                status=item["status"],
                reason_codes=_reason_codes_from_payload(
                    "reason_codes",
                    item["reason_codes"],
                ),
                paper_only=item["paper_only"],
                report_only=item["report_only"],
                readonly=item["readonly"],
            ),
        )
    normalized = _normalize_rows(tuple(result))
    if tuple(result) != normalized:
        raise ValueError("rows must be in canonical order")
    return normalized


def _report_from_payload(payload: dict[str, Any]) -> ResearchSourceScraperEvidenceGapDecayReport:
    _validate_public_payload(payload)
    report = ResearchSourceScraperEvidenceGapDecayReport(
        generated_at=_validate_datetime_payload("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        input_count=_decimal_from_payload(
            "input_count",
            payload["input_count"],
            _normalize_nonnegative_count,
        ),
        row_count=_decimal_from_payload(
            "row_count",
            payload["row_count"],
            _normalize_nonnegative_count,
        ),
        pass_count=_decimal_from_payload(
            "pass_count",
            payload["pass_count"],
            _normalize_nonnegative_count,
        ),
        watch_count=_decimal_from_payload(
            "watch_count",
            payload["watch_count"],
            _normalize_nonnegative_count,
        ),
        block_count=_decimal_from_payload(
            "block_count",
            payload["block_count"],
            _normalize_nonnegative_count,
        ),
        attention_count=_decimal_from_payload(
            "attention_count",
            payload["attention_count"],
            _normalize_nonnegative_count,
        ),
        max_evidence_age_seconds=_decimal_from_payload(
            "max_evidence_age_seconds",
            payload["max_evidence_age_seconds"],
            _normalize_nonnegative_decimal,
        ),
        max_recheck_age_seconds=_decimal_from_payload(
            "max_recheck_age_seconds",
            payload["max_recheck_age_seconds"],
            _normalize_nonnegative_decimal,
        ),
        average_coverage_ratio=_decimal_from_payload(
            "average_coverage_ratio",
            payload["average_coverage_ratio"],
            _normalize_probability,
        ),
        average_primary_coverage_ratio=_decimal_from_payload(
            "average_primary_coverage_ratio",
            payload["average_primary_coverage_ratio"],
            _normalize_probability,
        ),
        average_parser_confidence_ratio=_decimal_from_payload(
            "average_parser_confidence_ratio",
            payload["average_parser_confidence_ratio"],
            _normalize_probability,
        ),
        average_gap_decay_score=_decimal_from_payload(
            "average_gap_decay_score",
            payload["average_gap_decay_score"],
            _normalize_probability,
        ),
        status=payload["status"],
        reason_codes=_reason_codes_from_payload("reason_codes", payload["reason_codes"]),
        reason_code_counts=_reason_code_counts_from_payload(payload["reason_code_counts"]),
        rows=_rows_from_payload(payload["rows"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if not _values_match_exact(payload, _canonical_report_payload(report)):
        raise ValueError("report payload must be canonical")
    return report


def _values_match_exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is Decimal:
        return left.as_tuple() == right.as_tuple()
    if type(left) is datetime:
        return left == right and left.isoformat() == right.isoformat()
    if is_dataclass(left) and not isinstance(left, type):
        return all(
            _values_match_exact(getattr(left, field.name), getattr(right, field.name))
            for field in fields(left)
        )
    if type(left) is dict:
        return tuple(left) == tuple(right) and all(
            _values_match_exact(left[key], right[key]) for key in left
        )
    if type(left) in (tuple, list):
        return len(left) == len(right) and all(
            _values_match_exact(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


_CANONICAL_CONFIG = ResearchSourceScraperEvidenceGapDecayConfig()
