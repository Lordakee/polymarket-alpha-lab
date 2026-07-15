"""Pure report-only scraping authority shadow gap scoring."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_SOURCE_SCRAPING_AUTHORITY_SHADOW_GAP_CONFIG_VERSION = (
    "research-source-scraping-authority-shadow-gap-v0"
)
STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_scraping_authority_shadow_gap_empty"
CLEAR_REASON = "research_source_scraping_authority_shadow_gap_clear"
AUTHORITY_BLOCK_REASON = "research_source_scraping_authority_shadow_gap_authority_block"
COUNT_BLOCK_REASON = "research_source_scraping_authority_shadow_gap_count_block"
STALE_BLOCK_REASON = "research_source_scraping_authority_shadow_gap_stale_block"
CONFLICT_BLOCK_REASON = "research_source_scraping_authority_shadow_gap_conflict_block"
FALLBACK_BLOCK_REASON = "research_source_scraping_authority_shadow_gap_fallback_block"
SCORE_BLOCK_REASON = "research_source_scraping_authority_shadow_gap_score_block"
AUTHORITY_WATCH_REASON = "research_source_scraping_authority_shadow_gap_authority_watch"
COUNT_WATCH_REASON = "research_source_scraping_authority_shadow_gap_count_watch"
STALE_WATCH_REASON = "research_source_scraping_authority_shadow_gap_stale_watch"
CONFLICT_WATCH_REASON = "research_source_scraping_authority_shadow_gap_conflict_watch"
FALLBACK_WATCH_REASON = "research_source_scraping_authority_shadow_gap_fallback_watch"
SCORE_WATCH_REASON = "research_source_scraping_authority_shadow_gap_score_watch"

ROW_REASON_CODES = (
    CLEAR_REASON,
    AUTHORITY_BLOCK_REASON,
    COUNT_BLOCK_REASON,
    STALE_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    FALLBACK_BLOCK_REASON,
    SCORE_BLOCK_REASON,
    AUTHORITY_WATCH_REASON,
    COUNT_WATCH_REASON,
    STALE_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    FALLBACK_WATCH_REASON,
    SCORE_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in ROW_REASON_CODES if reason != CLEAR_REASON
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

AUTHORITY_GAP_WEIGHT = Decimal("0.300000")
COUNT_GAP_WEIGHT = Decimal("0.200000")
FRESHNESS_WEIGHT = Decimal("0.200000")
CONFLICT_WEIGHT = Decimal("0.150000")
FALLBACK_WEIGHT = Decimal("0.150000")

CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "freshness_watch_age_seconds",
    "freshness_block_age_seconds",
    "authority_gap_watch_score",
    "authority_gap_block_score",
    "scraping_count_gap_watch_score",
    "scraping_count_gap_block_score",
    "conflict_watch_ratio",
    "conflict_block_ratio",
    "fallback_watch_ratio",
    "fallback_block_ratio",
    "shadow_gap_watch_score",
    "shadow_gap_block_score",
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
ROW_PAYLOAD_FIELDS = (
    "public_shadow_key",
    "authority_bucket",
    "scraped_authority_score",
    "shadow_authority_score",
    "scraped_authority_evidence_count",
    "shadow_authority_evidence_count",
    "freshest_authority_scrape_age_seconds",
    "authority_conflict_ratio",
    "fallback_only_ratio",
    "authority_shadow_gap_score",
    "scraping_count_gap_score",
    "freshness_pressure_score",
    "shadow_gap_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "derivation_config",
    "shadow_item_count",
    "pass_shadow_item_count",
    "watch_shadow_item_count",
    "block_shadow_item_count",
    "authority_shadow_gap_count",
    "scraping_count_gap_count",
    "stale_scrape_count",
    "conflict_pressure_count",
    "fallback_dependency_count",
    "highest_shadow_gap_score",
    "highest_authority_shadow_gap_score",
    "highest_scraping_count_gap_score",
    "oldest_authority_scrape_age_seconds",
    "average_shadow_gap_score",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_", "candidate"),
    _join_parts("candidate", "_", "id"),
    _join_parts("candidate", "-"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("market", "_", "que", "stion"),
    _join_parts("market", "-"),
    _join_parts("que", "stion"),
    _join_parts("source", "_", "u", "r", "l"),
    _join_parts("source", "_", "te", "xt"),
    _join_parts("u", "r", "l"),
    _join_parts("d", "s", "n"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tr", "ade"),
    _join_parts("h", "t", "t", "p", ":", "/", "/"),
    _join_parts("h", "t", "t", "p", "s", ":", "/", "/"),
    _join_parts("postgres", ":", "/", "/"),
    _join_parts("mysql", ":", "/", "/"),
    _join_parts("j", "d", "b", "c", ":"),
    _join_parts("live", "_", "surface"),
    _join_parts("recommend", "ation"),
    _join_parts("private"),
    _join_parts("secret"),
    _join_parts("api", "_", "key"),
    _join_parts("cre", "dential"),
)


@dataclass(frozen=True)
class ResearchSourceScrapingAuthorityShadowGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPING_AUTHORITY_SHADOW_GAP_CONFIG_VERSION
    )
    freshness_watch_age_seconds: Decimal = Decimal("3600.000000")
    freshness_block_age_seconds: Decimal = Decimal("10800.000000")
    authority_gap_watch_score: Decimal = Decimal("0.250000")
    authority_gap_block_score: Decimal = Decimal("0.500000")
    scraping_count_gap_watch_score: Decimal = Decimal("0.400000")
    scraping_count_gap_block_score: Decimal = Decimal("0.700000")
    conflict_watch_ratio: Decimal = Decimal("0.400000")
    conflict_block_ratio: Decimal = Decimal("0.750000")
    fallback_watch_ratio: Decimal = Decimal("0.400000")
    fallback_block_ratio: Decimal = Decimal("0.750000")
    shadow_gap_watch_score: Decimal = Decimal("0.350000")
    shadow_gap_block_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingAuthorityShadowGapConfig:
            raise TypeError(
                "ResearchSourceScrapingAuthorityShadowGapConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingAuthorityShadowGapConfig:
            raise ValueError(
                "config must be exactly ResearchSourceScrapingAuthorityShadowGapConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("freshness_watch_age_seconds", "freshness_block_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_gap_watch_score",
            "authority_gap_block_score",
            "scraping_count_gap_watch_score",
            "scraping_count_gap_block_score",
            "conflict_watch_ratio",
            "conflict_block_ratio",
            "fallback_watch_ratio",
            "fallback_block_ratio",
            "shadow_gap_watch_score",
            "shadow_gap_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScrapingAuthorityShadowGapInput:
    public_shadow_key: str
    authority_bucket: str
    scraped_authority_score: Decimal
    shadow_authority_score: Decimal
    scraped_authority_evidence_count: Decimal
    shadow_authority_evidence_count: Decimal
    freshest_authority_scrape_age_seconds: Decimal
    authority_conflict_ratio: Decimal
    fallback_only_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingAuthorityShadowGapInput:
            raise TypeError(
                "ResearchSourceScrapingAuthorityShadowGapInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingAuthorityShadowGapInput:
            raise ValueError(
                "input must be exactly ResearchSourceScrapingAuthorityShadowGapInput",
            )
        object.__setattr__(
            self,
            "public_shadow_key",
            _require_public_label("public_shadow_key", self.public_shadow_key),
        )
        object.__setattr__(
            self,
            "authority_bucket",
            _require_public_label("authority_bucket", self.authority_bucket),
        )
        for field_name in ("scraped_authority_score", "shadow_authority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scraped_authority_evidence_count",
            "shadow_authority_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_authority_scrape_age_seconds",
            _require_nonnegative_decimal(
                "freshest_authority_scrape_age_seconds",
                self.freshest_authority_scrape_age_seconds,
            ),
        )
        for field_name in ("authority_conflict_ratio", "fallback_only_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScrapingAuthorityShadowGapRow:
    public_shadow_key: str
    authority_bucket: str
    scraped_authority_score: Decimal
    shadow_authority_score: Decimal
    scraped_authority_evidence_count: Decimal
    shadow_authority_evidence_count: Decimal
    freshest_authority_scrape_age_seconds: Decimal
    authority_conflict_ratio: Decimal
    fallback_only_ratio: Decimal
    authority_shadow_gap_score: Decimal
    scraping_count_gap_score: Decimal
    freshness_pressure_score: Decimal
    shadow_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingAuthorityShadowGapRow:
            raise TypeError(
                "ResearchSourceScrapingAuthorityShadowGapRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingAuthorityShadowGapRow:
            raise ValueError("row must be exactly ResearchSourceScrapingAuthorityShadowGapRow")
        object.__setattr__(
            self,
            "public_shadow_key",
            _require_public_label("public_shadow_key", self.public_shadow_key),
        )
        object.__setattr__(
            self,
            "authority_bucket",
            _require_public_label("authority_bucket", self.authority_bucket),
        )
        for field_name in (
            "scraped_authority_score",
            "shadow_authority_score",
            "authority_conflict_ratio",
            "fallback_only_ratio",
            "authority_shadow_gap_score",
            "scraping_count_gap_score",
            "freshness_pressure_score",
            "shadow_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scraped_authority_evidence_count",
            "shadow_authority_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_authority_scrape_age_seconds",
            _require_nonnegative_decimal(
                "freshest_authority_scrape_age_seconds",
                self.freshest_authority_scrape_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceScrapingAuthorityShadowGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingAuthorityShadowGapReasonCodeCount:
            raise TypeError(
                "ResearchSourceScrapingAuthorityShadowGapReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingAuthorityShadowGapReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceScrapingAuthorityShadowGapReasonCodeCount",
            )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be known")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        require_paper_only_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceScrapingAuthorityShadowGapReport:
    generated_at: datetime
    config_version: str
    derivation_config: ResearchSourceScrapingAuthorityShadowGapConfig
    shadow_item_count: Decimal
    pass_shadow_item_count: Decimal
    watch_shadow_item_count: Decimal
    block_shadow_item_count: Decimal
    authority_shadow_gap_count: Decimal
    scraping_count_gap_count: Decimal
    stale_scrape_count: Decimal
    conflict_pressure_count: Decimal
    fallback_dependency_count: Decimal
    highest_shadow_gap_score: Decimal
    highest_authority_shadow_gap_score: Decimal
    highest_scraping_count_gap_score: Decimal
    oldest_authority_scrape_age_seconds: Decimal
    average_shadow_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScrapingAuthorityShadowGapReasonCodeCount, ...]
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingAuthorityShadowGapReport:
            raise TypeError(
                "ResearchSourceScrapingAuthorityShadowGapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingAuthorityShadowGapReport:
            raise ValueError(
                "report must be exactly ResearchSourceScrapingAuthorityShadowGapReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if type(self.derivation_config) is not ResearchSourceScrapingAuthorityShadowGapConfig:
            raise ValueError(
                "derivation_config must be exactly "
                "ResearchSourceScrapingAuthorityShadowGapConfig",
            )
        object.__setattr__(
            self,
            "derivation_config",
            _revalidate_exact_dataclass(
                self.derivation_config,
                ResearchSourceScrapingAuthorityShadowGapConfig,
            ),
        )
        require_paper_only_flags("derivation_config", self.derivation_config)
        if self.config_version != self.derivation_config.config_version:
            raise ValueError("config_version must match derivation_config")
        for field_name in (
            "shadow_item_count",
            "pass_shadow_item_count",
            "watch_shadow_item_count",
            "block_shadow_item_count",
            "authority_shadow_gap_count",
            "scraping_count_gap_count",
            "stale_scrape_count",
            "conflict_pressure_count",
            "fallback_dependency_count",
            "oldest_authority_scrape_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_shadow_gap_score",
            "highest_authority_shadow_gap_score",
            "highest_scraping_count_gap_score",
            "average_shadow_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)
        _require_or_set_digest(self)


def build_research_source_scraping_authority_shadow_gap_report(
    inputs: list[ResearchSourceScrapingAuthorityShadowGapInput]
    | tuple[ResearchSourceScrapingAuthorityShadowGapInput, ...],
    *,
    config: ResearchSourceScrapingAuthorityShadowGapConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingAuthorityShadowGapReport:
    if type(config) is not ResearchSourceScrapingAuthorityShadowGapConfig:
        raise ValueError(
            "config must be a ResearchSourceScrapingAuthorityShadowGapConfig",
        )
    config = _revalidate_exact_dataclass(
        config,
        ResearchSourceScrapingAuthorityShadowGapConfig,
    )
    require_paper_only_flags("config", config)
    rows = _shadow_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceScrapingAuthorityShadowGapReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        derivation_config=config,
        shadow_item_count=_count(len(rows)),
        pass_shadow_item_count=_status_count(rows, "pass"),
        watch_shadow_item_count=_status_count(rows, "watch"),
        block_shadow_item_count=_status_count(rows, "block"),
        authority_shadow_gap_count=_reason_count(
            rows,
            (AUTHORITY_WATCH_REASON, AUTHORITY_BLOCK_REASON),
        ),
        scraping_count_gap_count=_reason_count(
            rows,
            (COUNT_WATCH_REASON, COUNT_BLOCK_REASON),
        ),
        stale_scrape_count=_reason_count(rows, (STALE_WATCH_REASON, STALE_BLOCK_REASON)),
        conflict_pressure_count=_reason_count(
            rows,
            (CONFLICT_WATCH_REASON, CONFLICT_BLOCK_REASON),
        ),
        fallback_dependency_count=_reason_count(
            rows,
            (FALLBACK_WATCH_REASON, FALLBACK_BLOCK_REASON),
        ),
        highest_shadow_gap_score=_max_row_decimal(rows, "shadow_gap_score"),
        highest_authority_shadow_gap_score=_max_row_decimal(
            rows,
            "authority_shadow_gap_score",
        ),
        highest_scraping_count_gap_score=_max_row_decimal(
            rows,
            "scraping_count_gap_score",
        ),
        oldest_authority_scrape_age_seconds=_max_row_decimal(
            rows,
            "freshest_authority_scrape_age_seconds",
        ),
        average_shadow_gap_score=_average_shadow_gap_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_scraping_authority_shadow_gap_report_payload(
    report: ResearchSourceScrapingAuthorityShadowGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScrapingAuthorityShadowGapReport:
        raise ValueError("report must be a ResearchSourceScrapingAuthorityShadowGapReport")
    validate_research_source_scraping_authority_shadow_gap_report_digest(report)
    require_paper_only_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_scraping_authority_shadow_gap_public_payload(payload)
    return payload


def research_source_scraping_authority_shadow_gap_report_digest(
    report: ResearchSourceScrapingAuthorityShadowGapReport,
) -> str:
    if type(report) is not ResearchSourceScrapingAuthorityShadowGapReport:
        raise ValueError("report must be a ResearchSourceScrapingAuthorityShadowGapReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_scraping_authority_shadow_gap_report_digest(
    report: ResearchSourceScrapingAuthorityShadowGapReport,
) -> None:
    if type(report) is not ResearchSourceScrapingAuthorityShadowGapReport:
        raise ValueError("report must be a ResearchSourceScrapingAuthorityShadowGapReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_scraping_authority_shadow_gap_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    rebuilt = _report_from_public_payload(payload)
    if _json_ready(rebuilt) != payload:
        raise ValueError("public payload must use exact canonical schema")


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceScrapingAuthorityShadowGapInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    normalized_rows: list[ResearchSourceScrapingAuthorityShadowGapInput] = []
    for row in rows:
        if type(row) is not ResearchSourceScrapingAuthorityShadowGapInput:
            raise ValueError(
                "inputs must contain ResearchSourceScrapingAuthorityShadowGapInput",
            )
        row = _revalidate_exact_dataclass(
            row,
            ResearchSourceScrapingAuthorityShadowGapInput,
        )
        require_paper_only_flags("input", row)
        key = (row.authority_bucket, row.public_shadow_key)
        if key in seen:
            raise ValueError(
                "inputs must be unique by authority_bucket and public_shadow_key",
            )
        seen.add(key)
        normalized_rows.append(row)
    return tuple(
        sorted(
            normalized_rows,
            key=lambda row: (row.authority_bucket, row.public_shadow_key),
        ),
    )


def _shadow_rows(
    inputs: tuple[ResearchSourceScrapingAuthorityShadowGapInput, ...],
    *,
    config: ResearchSourceScrapingAuthorityShadowGapConfig,
) -> tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...]:
    return tuple(sorted((_shadow_row(row, config=config) for row in inputs), key=_row_sort_key))


def _shadow_row(
    row: ResearchSourceScrapingAuthorityShadowGapInput,
    *,
    config: ResearchSourceScrapingAuthorityShadowGapConfig,
) -> ResearchSourceScrapingAuthorityShadowGapRow:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = max(
            row.shadow_authority_score - row.scraped_authority_score,
            ZERO,
        ).quantize(QUANT)
    count_gap = _count_gap_score(
        scraped_count=row.scraped_authority_evidence_count,
        shadow_count=row.shadow_authority_evidence_count,
    )
    with localcontext(DECIMAL_CONTEXT):
        freshness_pressure = min(
            _ratio(
                row.freshest_authority_scrape_age_seconds,
                config.freshness_block_age_seconds,
            ),
            ONE,
        ).quantize(QUANT)
    shadow_gap = _shadow_gap_score(
        authority_shadow_gap_score=authority_gap,
        scraping_count_gap_score=count_gap,
        freshness_pressure_score=freshness_pressure,
        authority_conflict_ratio=row.authority_conflict_ratio,
        fallback_only_ratio=row.fallback_only_ratio,
    )
    reason_codes = _row_reason_codes(
        authority_shadow_gap_score=authority_gap,
        scraping_count_gap_score=count_gap,
        freshest_authority_scrape_age_seconds=row.freshest_authority_scrape_age_seconds,
        authority_conflict_ratio=row.authority_conflict_ratio,
        fallback_only_ratio=row.fallback_only_ratio,
        shadow_gap_score=shadow_gap,
        config=config,
    )
    return ResearchSourceScrapingAuthorityShadowGapRow(
        public_shadow_key=row.public_shadow_key,
        authority_bucket=row.authority_bucket,
        scraped_authority_score=row.scraped_authority_score,
        shadow_authority_score=row.shadow_authority_score,
        scraped_authority_evidence_count=row.scraped_authority_evidence_count,
        shadow_authority_evidence_count=row.shadow_authority_evidence_count,
        freshest_authority_scrape_age_seconds=row.freshest_authority_scrape_age_seconds,
        authority_conflict_ratio=row.authority_conflict_ratio,
        fallback_only_ratio=row.fallback_only_ratio,
        authority_shadow_gap_score=authority_gap,
        scraping_count_gap_score=count_gap,
        freshness_pressure_score=freshness_pressure,
        shadow_gap_score=shadow_gap,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _count_gap_score(*, scraped_count: Decimal, shadow_count: Decimal) -> Decimal:
    if shadow_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        gap = max(shadow_count - scraped_count, ZERO)
    return _ratio(gap, shadow_count)


def _shadow_gap_score(
    *,
    authority_shadow_gap_score: Decimal,
    scraping_count_gap_score: Decimal,
    freshness_pressure_score: Decimal,
    authority_conflict_ratio: Decimal,
    fallback_only_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            authority_shadow_gap_score * AUTHORITY_GAP_WEIGHT
            + scraping_count_gap_score * COUNT_GAP_WEIGHT
            + freshness_pressure_score * FRESHNESS_WEIGHT
            + authority_conflict_ratio * CONFLICT_WEIGHT
            + fallback_only_ratio * FALLBACK_WEIGHT
        ).quantize(QUANT)


def _row_reason_codes(
    *,
    authority_shadow_gap_score: Decimal,
    scraping_count_gap_score: Decimal,
    freshest_authority_scrape_age_seconds: Decimal,
    authority_conflict_ratio: Decimal,
    fallback_only_ratio: Decimal,
    shadow_gap_score: Decimal,
    config: ResearchSourceScrapingAuthorityShadowGapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if authority_shadow_gap_score >= config.authority_gap_block_score:
        reasons.append(AUTHORITY_BLOCK_REASON)
    elif authority_shadow_gap_score >= config.authority_gap_watch_score:
        reasons.append(AUTHORITY_WATCH_REASON)
    if scraping_count_gap_score >= config.scraping_count_gap_block_score:
        reasons.append(COUNT_BLOCK_REASON)
    elif scraping_count_gap_score >= config.scraping_count_gap_watch_score:
        reasons.append(COUNT_WATCH_REASON)
    if freshest_authority_scrape_age_seconds >= config.freshness_block_age_seconds:
        reasons.append(STALE_BLOCK_REASON)
    elif freshest_authority_scrape_age_seconds >= config.freshness_watch_age_seconds:
        reasons.append(STALE_WATCH_REASON)
    if authority_conflict_ratio >= config.conflict_block_ratio:
        reasons.append(CONFLICT_BLOCK_REASON)
    elif authority_conflict_ratio >= config.conflict_watch_ratio:
        reasons.append(CONFLICT_WATCH_REASON)
    if fallback_only_ratio >= config.fallback_block_ratio:
        reasons.append(FALLBACK_BLOCK_REASON)
    elif fallback_only_ratio >= config.fallback_watch_ratio:
        reasons.append(FALLBACK_WATCH_REASON)
    if shadow_gap_score >= config.shadow_gap_block_score:
        reasons.append(SCORE_BLOCK_REASON)
    elif shadow_gap_score >= config.shadow_gap_watch_score:
        reasons.append(SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason for reason in REPORT_TRIGGER_REASON_CODES if _row_has_reason(rows, reason)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...],
) -> tuple[ResearchSourceScrapingAuthorityShadowGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceScrapingAuthorityShadowGapReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourceScrapingAuthorityShadowGapReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _row_has_reason(
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...],
    reason: str,
) -> bool:
    return any(reason in row.reason_codes for row in rows)


def _row_sort_key(
    row: ResearchSourceScrapingAuthorityShadowGapRow,
) -> tuple[Decimal, str, str]:
    return (
        row.shadow_gap_score.copy_negate(),
        row.authority_bucket,
        row.public_shadow_key,
    )


def _status_count(
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _max_row_decimal(
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...],
    field_name: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return max(
            (
                _require_nonnegative_decimal(field_name, getattr(row, field_name))
                for row in rows
            ),
            default=ZERO,
        ).quantize(QUANT)


def _average_shadow_gap_score(
    rows: tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        total = sum((row.shadow_gap_score for row in rows), ZERO)
    return _ratio(total, _count(len(rows)))


def _validate_config(config: ResearchSourceScrapingAuthorityShadowGapConfig) -> None:
    if config.freshness_watch_age_seconds >= config.freshness_block_age_seconds:
        raise ValueError("freshness_watch_age_seconds must be less than freshness_block_age_seconds")
    threshold_pairs = (
        ("authority_gap_watch_score", "authority_gap_block_score"),
        ("scraping_count_gap_watch_score", "scraping_count_gap_block_score"),
        ("conflict_watch_ratio", "conflict_block_ratio"),
        ("fallback_watch_ratio", "fallback_block_ratio"),
        ("shadow_gap_watch_score", "shadow_gap_block_score"),
    )
    for watch_field, block_field in threshold_pairs:
        if getattr(config, watch_field) > getattr(config, block_field):
            raise ValueError(f"{watch_field} must not exceed {block_field}")


def _validate_row(row: ResearchSourceScrapingAuthorityShadowGapRow) -> None:
    with localcontext(DECIMAL_CONTEXT):
        expected_authority_gap = max(
            row.shadow_authority_score - row.scraped_authority_score,
            ZERO,
        ).quantize(QUANT)
    if row.authority_shadow_gap_score != expected_authority_gap:
        raise ValueError("authority_shadow_gap_score must match authority scores")
    if row.scraping_count_gap_score != _count_gap_score(
        scraped_count=row.scraped_authority_evidence_count,
        shadow_count=row.shadow_authority_evidence_count,
    ):
        raise ValueError("scraping_count_gap_score must match evidence counts")
    if row.shadow_gap_score != _shadow_gap_score(
        authority_shadow_gap_score=row.authority_shadow_gap_score,
        scraping_count_gap_score=row.scraping_count_gap_score,
        freshness_pressure_score=row.freshness_pressure_score,
        authority_conflict_ratio=row.authority_conflict_ratio,
        fallback_only_ratio=row.fallback_only_ratio,
    ):
        raise ValueError("shadow_gap_score must match row components")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(report: ResearchSourceScrapingAuthorityShadowGapReport) -> None:
    for row in report.rows:
        _validate_row_against_config(row, config=report.derivation_config)
    if report.shadow_item_count != _count(len(report.rows)):
        raise ValueError("shadow_item_count must match rows")
    for status, field_name in (
        ("pass", "pass_shadow_item_count"),
        ("watch", "watch_shadow_item_count"),
        ("block", "block_shadow_item_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        ("authority_shadow_gap_count", (AUTHORITY_WATCH_REASON, AUTHORITY_BLOCK_REASON)),
        ("scraping_count_gap_count", (COUNT_WATCH_REASON, COUNT_BLOCK_REASON)),
        ("stale_scrape_count", (STALE_WATCH_REASON, STALE_BLOCK_REASON)),
        ("conflict_pressure_count", (CONFLICT_WATCH_REASON, CONFLICT_BLOCK_REASON)),
        ("fallback_dependency_count", (FALLBACK_WATCH_REASON, FALLBACK_BLOCK_REASON)),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_shadow_gap_score != _max_row_decimal(report.rows, "shadow_gap_score"):
        raise ValueError("highest_shadow_gap_score must match rows")
    if report.highest_authority_shadow_gap_score != _max_row_decimal(
        report.rows,
        "authority_shadow_gap_score",
    ):
        raise ValueError("highest_authority_shadow_gap_score must match rows")
    if report.highest_scraping_count_gap_score != _max_row_decimal(
        report.rows,
        "scraping_count_gap_score",
    ):
        raise ValueError("highest_scraping_count_gap_score must match rows")
    if report.oldest_authority_scrape_age_seconds != _max_row_decimal(
        report.rows,
        "freshest_authority_scrape_age_seconds",
    ):
        raise ValueError("oldest_authority_scrape_age_seconds must match rows")
    if report.average_shadow_gap_score != _average_shadow_gap_score(report.rows):
        raise ValueError("average_shadow_gap_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic shadow gap sort")


def _validate_row_against_config(
    row: ResearchSourceScrapingAuthorityShadowGapRow,
    *,
    config: ResearchSourceScrapingAuthorityShadowGapConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        expected_freshness_pressure = min(
            _ratio(
                row.freshest_authority_scrape_age_seconds,
                config.freshness_block_age_seconds,
            ),
            ONE,
        ).quantize(QUANT)
    if row.freshness_pressure_score != expected_freshness_pressure:
        raise ValueError(
            "freshness_pressure_score must match freshest authority scrape age",
        )
    expected_reasons = _row_reason_codes(
        authority_shadow_gap_score=row.authority_shadow_gap_score,
        scraping_count_gap_score=row.scraping_count_gap_score,
        freshest_authority_scrape_age_seconds=row.freshest_authority_scrape_age_seconds,
        authority_conflict_ratio=row.authority_conflict_ratio,
        fallback_only_ratio=row.fallback_only_ratio,
        shadow_gap_score=row.shadow_gap_score,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row values and derivation_config")
    if row.status != _row_status(expected_reasons):
        raise ValueError("status must match row values and derivation_config")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceScrapingAuthorityShadowGapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    normalized_rows: list[ResearchSourceScrapingAuthorityShadowGapRow] = []
    for row in rows:
        if type(row) is not ResearchSourceScrapingAuthorityShadowGapRow:
            raise ValueError("rows must contain ResearchSourceScrapingAuthorityShadowGapRow")
        row = _revalidate_exact_dataclass(
            row,
            ResearchSourceScrapingAuthorityShadowGapRow,
        )
        require_paper_only_flags("row", row)
        key = (row.authority_bucket, row.public_shadow_key)
        if key in seen:
            raise ValueError(
                "rows must be unique by authority_bucket and public_shadow_key",
            )
        seen.add(key)
        normalized_rows.append(row)
    return tuple(sorted(normalized_rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceScrapingAuthorityShadowGapReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    normalized_counts: list[ResearchSourceScrapingAuthorityShadowGapReasonCodeCount] = []
    for item in counts:
        if type(item) is not ResearchSourceScrapingAuthorityShadowGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScrapingAuthorityShadowGapReasonCodeCount",
            )
        item = _revalidate_exact_dataclass(
            item,
            ResearchSourceScrapingAuthorityShadowGapReasonCodeCount,
        )
        require_paper_only_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
        normalized_counts.append(item)
    expected_order = tuple(reason for reason in REPORT_REASON_CODES if reason in seen)
    if tuple(item.reason_code for item in normalized_counts) != expected_order:
        raise ValueError("reason_code_counts must be deterministic")
    return tuple(normalized_counts)


def _revalidate_exact_dataclass(value: object, expected_type: type[Any]) -> Any:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")
    return expected_type(
        **{field.name: getattr(value, field.name) for field in fields(expected_type)},
    )


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value.is_zero():
        return ZERO
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        is_whole = value == value.to_integral_value()
    if not is_whole:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _require_nonnegative_decimal(field_name, value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(char.isalnum() or char in (".", "_", "-") for char in value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_or_set_digest(report: ResearchSourceScrapingAuthorityShadowGapReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest_from_public_payload(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _report_digest_from_public_payload(
    report: ResearchSourceScrapingAuthorityShadowGapReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceScrapingAuthorityShadowGapReport:
    _require_exact_mapping("public payload", payload, REPORT_PAYLOAD_FIELDS)
    return ResearchSourceScrapingAuthorityShadowGapReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        derivation_config=_config_from_public_payload(payload["derivation_config"]),
        shadow_item_count=_payload_decimal(
            "shadow_item_count",
            payload["shadow_item_count"],
        ),
        pass_shadow_item_count=_payload_decimal(
            "pass_shadow_item_count",
            payload["pass_shadow_item_count"],
        ),
        watch_shadow_item_count=_payload_decimal(
            "watch_shadow_item_count",
            payload["watch_shadow_item_count"],
        ),
        block_shadow_item_count=_payload_decimal(
            "block_shadow_item_count",
            payload["block_shadow_item_count"],
        ),
        authority_shadow_gap_count=_payload_decimal(
            "authority_shadow_gap_count",
            payload["authority_shadow_gap_count"],
        ),
        scraping_count_gap_count=_payload_decimal(
            "scraping_count_gap_count",
            payload["scraping_count_gap_count"],
        ),
        stale_scrape_count=_payload_decimal(
            "stale_scrape_count",
            payload["stale_scrape_count"],
        ),
        conflict_pressure_count=_payload_decimal(
            "conflict_pressure_count",
            payload["conflict_pressure_count"],
        ),
        fallback_dependency_count=_payload_decimal(
            "fallback_dependency_count",
            payload["fallback_dependency_count"],
        ),
        highest_shadow_gap_score=_payload_decimal(
            "highest_shadow_gap_score",
            payload["highest_shadow_gap_score"],
        ),
        highest_authority_shadow_gap_score=_payload_decimal(
            "highest_authority_shadow_gap_score",
            payload["highest_authority_shadow_gap_score"],
        ),
        highest_scraping_count_gap_score=_payload_decimal(
            "highest_scraping_count_gap_score",
            payload["highest_scraping_count_gap_score"],
        ),
        oldest_authority_scrape_age_seconds=_payload_decimal(
            "oldest_authority_scrape_age_seconds",
            payload["oldest_authority_scrape_age_seconds"],
        ),
        average_shadow_gap_score=_payload_decimal(
            "average_shadow_gap_score",
            payload["average_shadow_gap_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=tuple(
            _reason_code_count_from_public_payload(item)
            for item in _payload_list(
                "reason_code_counts",
                payload["reason_code_counts"],
            )
        ),
        rows=tuple(
            _row_from_public_payload(item)
            for item in _payload_list("rows", payload["rows"])
        ),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _config_from_public_payload(
    value: object,
) -> ResearchSourceScrapingAuthorityShadowGapConfig:
    payload = _require_exact_mapping(
        "derivation_config",
        value,
        CONFIG_PAYLOAD_FIELDS,
    )
    return ResearchSourceScrapingAuthorityShadowGapConfig(
        config_version=_payload_string(
            "derivation_config.config_version",
            payload["config_version"],
        ),
        freshness_watch_age_seconds=_payload_decimal(
            "derivation_config.freshness_watch_age_seconds",
            payload["freshness_watch_age_seconds"],
        ),
        freshness_block_age_seconds=_payload_decimal(
            "derivation_config.freshness_block_age_seconds",
            payload["freshness_block_age_seconds"],
        ),
        authority_gap_watch_score=_payload_decimal(
            "derivation_config.authority_gap_watch_score",
            payload["authority_gap_watch_score"],
        ),
        authority_gap_block_score=_payload_decimal(
            "derivation_config.authority_gap_block_score",
            payload["authority_gap_block_score"],
        ),
        scraping_count_gap_watch_score=_payload_decimal(
            "derivation_config.scraping_count_gap_watch_score",
            payload["scraping_count_gap_watch_score"],
        ),
        scraping_count_gap_block_score=_payload_decimal(
            "derivation_config.scraping_count_gap_block_score",
            payload["scraping_count_gap_block_score"],
        ),
        conflict_watch_ratio=_payload_decimal(
            "derivation_config.conflict_watch_ratio",
            payload["conflict_watch_ratio"],
        ),
        conflict_block_ratio=_payload_decimal(
            "derivation_config.conflict_block_ratio",
            payload["conflict_block_ratio"],
        ),
        fallback_watch_ratio=_payload_decimal(
            "derivation_config.fallback_watch_ratio",
            payload["fallback_watch_ratio"],
        ),
        fallback_block_ratio=_payload_decimal(
            "derivation_config.fallback_block_ratio",
            payload["fallback_block_ratio"],
        ),
        shadow_gap_watch_score=_payload_decimal(
            "derivation_config.shadow_gap_watch_score",
            payload["shadow_gap_watch_score"],
        ),
        shadow_gap_block_score=_payload_decimal(
            "derivation_config.shadow_gap_block_score",
            payload["shadow_gap_block_score"],
        ),
        paper_only=_payload_true(
            "derivation_config.paper_only",
            payload["paper_only"],
        ),
        report_only=_payload_true(
            "derivation_config.report_only",
            payload["report_only"],
        ),
        readonly=_payload_true(
            "derivation_config.readonly",
            payload["readonly"],
        ),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceScrapingAuthorityShadowGapReasonCodeCount:
    payload = _require_exact_mapping(
        "reason_code_count",
        value,
        REASON_CODE_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchSourceScrapingAuthorityShadowGapReasonCodeCount(
        reason_code=_payload_string("reason_code", payload["reason_code"]),
        count=_payload_decimal("count", payload["count"]),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchSourceScrapingAuthorityShadowGapRow:
    payload = _require_exact_mapping("row", value, ROW_PAYLOAD_FIELDS)
    return ResearchSourceScrapingAuthorityShadowGapRow(
        public_shadow_key=_payload_string(
            "public_shadow_key",
            payload["public_shadow_key"],
        ),
        authority_bucket=_payload_string(
            "authority_bucket",
            payload["authority_bucket"],
        ),
        scraped_authority_score=_payload_decimal(
            "scraped_authority_score",
            payload["scraped_authority_score"],
        ),
        shadow_authority_score=_payload_decimal(
            "shadow_authority_score",
            payload["shadow_authority_score"],
        ),
        scraped_authority_evidence_count=_payload_decimal(
            "scraped_authority_evidence_count",
            payload["scraped_authority_evidence_count"],
        ),
        shadow_authority_evidence_count=_payload_decimal(
            "shadow_authority_evidence_count",
            payload["shadow_authority_evidence_count"],
        ),
        freshest_authority_scrape_age_seconds=_payload_decimal(
            "freshest_authority_scrape_age_seconds",
            payload["freshest_authority_scrape_age_seconds"],
        ),
        authority_conflict_ratio=_payload_decimal(
            "authority_conflict_ratio",
            payload["authority_conflict_ratio"],
        ),
        fallback_only_ratio=_payload_decimal(
            "fallback_only_ratio",
            payload["fallback_only_ratio"],
        ),
        authority_shadow_gap_score=_payload_decimal(
            "authority_shadow_gap_score",
            payload["authority_shadow_gap_score"],
        ),
        scraping_count_gap_score=_payload_decimal(
            "scraping_count_gap_score",
            payload["scraping_count_gap_score"],
        ),
        freshness_pressure_score=_payload_decimal(
            "freshness_pressure_score",
            payload["freshness_pressure_score"],
        ),
        shadow_gap_score=_payload_decimal(
            "shadow_gap_score",
            payload["shadow_gap_score"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _require_exact_mapping(
    field_name: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must use exact canonical schema")
    if tuple(value) != expected_fields:
        raise ValueError(f"{field_name} must use exact canonical schema")
    return value


def _payload_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must use exact canonical schema")
    return value


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    return tuple(
        _payload_string(f"{field_name}[{index}]", item)
        for index, item in enumerate(_payload_list(field_name, value))
    )


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use exact canonical schema")
    return value


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = decimal_value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if value != format(normalized, ".6f") or (
        normalized.is_zero() and normalized.is_signed()
    ):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _payload_datetime(field_name: str, value: object) -> datetime:
    text = _payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is ResearchSourceScrapingAuthorityShadowGapConfig:
        return {
            "config_version": value.config_version,
            "freshness_watch_age_seconds": _json_ready(
                value.freshness_watch_age_seconds,
            ),
            "freshness_block_age_seconds": _json_ready(
                value.freshness_block_age_seconds,
            ),
            "authority_gap_watch_score": _json_ready(value.authority_gap_watch_score),
            "authority_gap_block_score": _json_ready(value.authority_gap_block_score),
            "scraping_count_gap_watch_score": _json_ready(
                value.scraping_count_gap_watch_score,
            ),
            "scraping_count_gap_block_score": _json_ready(
                value.scraping_count_gap_block_score,
            ),
            "conflict_watch_ratio": _json_ready(value.conflict_watch_ratio),
            "conflict_block_ratio": _json_ready(value.conflict_block_ratio),
            "fallback_watch_ratio": _json_ready(value.fallback_watch_ratio),
            "fallback_block_ratio": _json_ready(value.fallback_block_ratio),
            "shadow_gap_watch_score": _json_ready(value.shadow_gap_watch_score),
            "shadow_gap_block_score": _json_ready(value.shadow_gap_block_score),
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchSourceScrapingAuthorityShadowGapReasonCodeCount:
        return {
            "reason_code": value.reason_code,
            "count": _json_ready(value.count),
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchSourceScrapingAuthorityShadowGapRow:
        return {
            "public_shadow_key": value.public_shadow_key,
            "authority_bucket": value.authority_bucket,
            "scraped_authority_score": _json_ready(value.scraped_authority_score),
            "shadow_authority_score": _json_ready(value.shadow_authority_score),
            "scraped_authority_evidence_count": _json_ready(
                value.scraped_authority_evidence_count,
            ),
            "shadow_authority_evidence_count": _json_ready(
                value.shadow_authority_evidence_count,
            ),
            "freshest_authority_scrape_age_seconds": _json_ready(
                value.freshest_authority_scrape_age_seconds,
            ),
            "authority_conflict_ratio": _json_ready(value.authority_conflict_ratio),
            "fallback_only_ratio": _json_ready(value.fallback_only_ratio),
            "authority_shadow_gap_score": _json_ready(
                value.authority_shadow_gap_score,
            ),
            "scraping_count_gap_score": _json_ready(value.scraping_count_gap_score),
            "freshness_pressure_score": _json_ready(value.freshness_pressure_score),
            "shadow_gap_score": _json_ready(value.shadow_gap_score),
            "status": value.status,
            "reason_codes": _json_ready(value.reason_codes),
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchSourceScrapingAuthorityShadowGapReport:
        return {
            "generated_at": _json_ready(value.generated_at),
            "config_version": value.config_version,
            "derivation_config": _json_ready(value.derivation_config),
            "shadow_item_count": _json_ready(value.shadow_item_count),
            "pass_shadow_item_count": _json_ready(value.pass_shadow_item_count),
            "watch_shadow_item_count": _json_ready(value.watch_shadow_item_count),
            "block_shadow_item_count": _json_ready(value.block_shadow_item_count),
            "authority_shadow_gap_count": _json_ready(
                value.authority_shadow_gap_count,
            ),
            "scraping_count_gap_count": _json_ready(value.scraping_count_gap_count),
            "stale_scrape_count": _json_ready(value.stale_scrape_count),
            "conflict_pressure_count": _json_ready(value.conflict_pressure_count),
            "fallback_dependency_count": _json_ready(value.fallback_dependency_count),
            "highest_shadow_gap_score": _json_ready(value.highest_shadow_gap_score),
            "highest_authority_shadow_gap_score": _json_ready(
                value.highest_authority_shadow_gap_score,
            ),
            "highest_scraping_count_gap_score": _json_ready(
                value.highest_scraping_count_gap_score,
            ),
            "oldest_authority_scrape_age_seconds": _json_ready(
                value.oldest_authority_scrape_age_seconds,
            ),
            "average_shadow_gap_score": _json_ready(value.average_shadow_gap_score),
            "status": value.status,
            "reason_codes": _json_ready(value.reason_codes),
            "reason_code_counts": _json_ready(value.reason_code_counts),
            "rows": _json_ready(value.rows),
            "derived_validation_digest": value.derived_validation_digest,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("JSON Decimal value must not use signed zero")
        return format(value, ".6f")
    if type(value) is datetime:
        return _as_utc("JSON datetime value", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_fragment(key):
                raise ValueError("public payload contains unsafe key")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str) and _contains_unsafe_public_fragment(value):
        raise ValueError("public payload contains unsafe value")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPING_AUTHORITY_SHADOW_GAP_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceScrapingAuthorityShadowGapConfig",
    "ResearchSourceScrapingAuthorityShadowGapInput",
    "ResearchSourceScrapingAuthorityShadowGapReasonCodeCount",
    "ResearchSourceScrapingAuthorityShadowGapReport",
    "ResearchSourceScrapingAuthorityShadowGapRow",
    "build_research_source_scraping_authority_shadow_gap_report",
    "research_source_scraping_authority_shadow_gap_report_digest",
    "research_source_scraping_authority_shadow_gap_report_payload",
    "validate_research_source_scraping_authority_shadow_gap_public_payload",
    "validate_research_source_scraping_authority_shadow_gap_report_digest",
)
