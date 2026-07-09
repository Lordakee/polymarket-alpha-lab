"""Pure report-only routing for sanitized scraped claim update latency."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping


DEFAULT_RESEARCH_SOURCE_SCRAPING_CLAIM_UPDATE_LATENCY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-source-scraping-claim-update-latency-router-report-v0"
)

RESEARCH_SOURCE_SCRAPING_CLAIM_UPDATE_LATENCY_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)

PASS_REASON = "scraping_claim_update_latency_router_pass"
EMPTY_REASON = "scraping_claim_update_latency_router_empty"
EXTRACTION_LATENCY_WATCH_REASON = (
    "scraping_claim_update_latency_router_extraction_latency_watch"
)
EXTRACTION_LATENCY_BLOCK_REASON = (
    "scraping_claim_update_latency_router_extraction_latency_block"
)
STALE_UPDATE_WATCH_REASON = "scraping_claim_update_latency_router_stale_update_watch"
STALE_UPDATE_BLOCK_REASON = "scraping_claim_update_latency_router_stale_update_block"
AUTHORITY_CONFIDENCE_WATCH_REASON = (
    "scraping_claim_update_latency_router_authority_confidence_watch"
)
AUTHORITY_CONFIDENCE_BLOCK_REASON = (
    "scraping_claim_update_latency_router_authority_confidence_block"
)
CORROBORATION_BREADTH_WATCH_REASON = (
    "scraping_claim_update_latency_router_corroboration_breadth_watch"
)
CORROBORATION_BREADTH_BLOCK_REASON = (
    "scraping_claim_update_latency_router_corroboration_breadth_block"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "scraping_claim_update_latency_router_contradiction_pressure_watch"
)
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "scraping_claim_update_latency_router_contradiction_pressure_block"
)

ROW_REASON_CODES = (
    EXTRACTION_LATENCY_BLOCK_REASON,
    STALE_UPDATE_BLOCK_REASON,
    AUTHORITY_CONFIDENCE_BLOCK_REASON,
    CORROBORATION_BREADTH_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    EXTRACTION_LATENCY_WATCH_REASON,
    STALE_UPDATE_WATCH_REASON,
    AUTHORITY_CONFIDENCE_WATCH_REASON,
    CORROBORATION_BREADTH_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, PASS_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate",
    "market_id",
    "market_slug",
    "market_question",
    "market",
    "slug",
    "question",
    "raw",
    "source_url",
    "source_text",
    "http",
    "https",
    "http://",
    "https://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order_id",
    "order",
    "trade_id",
    "trade",
    "live_trading",
    "live",
    "sizing",
    "recommendation",
    "private",
    "secret",
    "credential",
)


@dataclass(frozen=True)
class ResearchSourceScrapingClaimUpdateLatencyRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPING_CLAIM_UPDATE_LATENCY_ROUTER_REPORT_CONFIG_VERSION
    )
    extraction_latency_watch_seconds: Decimal = Decimal("120.000000")
    extraction_latency_block_seconds: Decimal = Decimal("600.000000")
    update_age_watch_seconds: Decimal = Decimal("3600.000000")
    update_age_block_seconds: Decimal = Decimal("14400.000000")
    authority_confidence_watch_floor: Decimal = Decimal("0.750000")
    authority_confidence_block_floor: Decimal = Decimal("0.500000")
    corroboration_breadth_watch_floor: Decimal = Decimal("2.000000")
    corroboration_breadth_block_floor: Decimal = Decimal("0.000000")
    contradiction_pressure_watch: Decimal = Decimal("0.300000")
    contradiction_pressure_block: Decimal = Decimal("0.700000")
    extraction_latency_weight: Decimal = Decimal("0.200000")
    update_freshness_weight: Decimal = Decimal("0.200000")
    authority_confidence_weight: Decimal = Decimal("0.200000")
    corroboration_breadth_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingClaimUpdateLatencyRouterConfig:
            raise TypeError(
                "ResearchSourceScrapingClaimUpdateLatencyRouterConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingClaimUpdateLatencyRouterConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceScrapingClaimUpdateLatencyRouterConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "extraction_latency_watch_seconds",
            "extraction_latency_block_seconds",
            "update_age_watch_seconds",
            "update_age_block_seconds",
            "corroboration_breadth_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_breadth_block_floor",
            _require_nonnegative_decimal(
                "corroboration_breadth_block_floor",
                self.corroboration_breadth_block_floor,
            ),
        )
        for field_name in (
            "authority_confidence_watch_floor",
            "authority_confidence_block_floor",
            "contradiction_pressure_watch",
            "contradiction_pressure_block",
            "extraction_latency_weight",
            "update_freshness_weight",
            "authority_confidence_weight",
            "corroboration_breadth_weight",
            "contradiction_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScrapingClaimUpdate:
    claim_update_bucket: str
    scraped_at: datetime
    extracted_at: datetime
    claim_updated_at: datetime
    authority_confidence_score: Decimal
    corroboration_breadth_count: Decimal
    contradiction_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingClaimUpdate:
            raise TypeError(
                "ResearchSourceScrapingClaimUpdate does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingClaimUpdate:
            raise ValueError(
                "update must be exactly ResearchSourceScrapingClaimUpdate",
            )
        object.__setattr__(
            self,
            "claim_update_bucket",
            _require_public_identifier("claim_update_bucket", self.claim_update_bucket),
        )
        for field_name in ("scraped_at", "extracted_at", "claim_updated_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        if self.extracted_at < self.scraped_at:
            raise ValueError("extracted_at must not be before scraped_at")
        for field_name in ("authority_confidence_score", "contradiction_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_breadth_count",
            _require_nonnegative_decimal(
                "corroboration_breadth_count",
                self.corroboration_breadth_count,
            ),
        )
        _require_hard_flags("update", self)


@dataclass(frozen=True)
class ResearchSourceScrapingClaimUpdateLatencyRouterRow:
    claim_update_bucket: str
    extraction_latency_seconds: Decimal
    update_age_seconds: Decimal
    authority_confidence_score: Decimal
    corroboration_breadth_count: Decimal
    corroboration_breadth_score: Decimal
    contradiction_pressure_score: Decimal
    router_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingClaimUpdateLatencyRouterRow:
            raise TypeError(
                "ResearchSourceScrapingClaimUpdateLatencyRouterRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingClaimUpdateLatencyRouterRow:
            raise ValueError(
                "row must be exactly ResearchSourceScrapingClaimUpdateLatencyRouterRow",
            )
        object.__setattr__(
            self,
            "claim_update_bucket",
            _require_public_identifier("claim_update_bucket", self.claim_update_bucket),
        )
        for field_name in (
            "extraction_latency_seconds",
            "update_age_seconds",
            "corroboration_breadth_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_confidence_score",
            "corroboration_breadth_score",
            "contradiction_pressure_score",
            "router_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount:
            raise TypeError(
                "ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount",
            )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceScrapingClaimUpdateLatencyRouterReport:
    generated_at: datetime
    config_version: str
    update_count: Decimal
    pass_update_count: Decimal
    watch_update_count: Decimal
    block_update_count: Decimal
    max_extraction_latency_seconds: Decimal
    oldest_update_age_seconds: Decimal
    lowest_authority_confidence_score: Decimal
    lowest_corroboration_breadth_count: Decimal
    highest_contradiction_pressure_score: Decimal
    highest_router_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceScrapingClaimUpdateLatencyRouterRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScrapingClaimUpdateLatencyRouterReport:
            raise TypeError(
                "ResearchSourceScrapingClaimUpdateLatencyRouterReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScrapingClaimUpdateLatencyRouterReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceScrapingClaimUpdateLatencyRouterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "update_count",
            "pass_update_count",
            "watch_update_count",
            "block_update_count",
            "max_extraction_latency_seconds",
            "oldest_update_age_seconds",
            "lowest_corroboration_breadth_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_authority_confidence_score",
            "highest_contradiction_pressure_score",
            "highest_router_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_public_payload(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match public payload")


def build_research_source_scraping_claim_update_latency_router_report(
    updates: tuple[ResearchSourceScrapingClaimUpdate, ...],
    *,
    config: ResearchSourceScrapingClaimUpdateLatencyRouterConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingClaimUpdateLatencyRouterReport:
    if type(config) is not ResearchSourceScrapingClaimUpdateLatencyRouterConfig:
        raise ValueError(
            "config must be a ResearchSourceScrapingClaimUpdateLatencyRouterConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _router_rows(_normalize_updates(updates), config=config, generated_at=generated_at_utc)
    return ResearchSourceScrapingClaimUpdateLatencyRouterReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        update_count=_count(len(rows)),
        pass_update_count=_status_count(rows, "pass"),
        watch_update_count=_status_count(rows, "watch"),
        block_update_count=_status_count(rows, "block"),
        max_extraction_latency_seconds=max(
            (row.extraction_latency_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_update_age_seconds=max(
            (row.update_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_authority_confidence_score=min(
            (row.authority_confidence_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_corroboration_breadth_count=min(
            (row.corroboration_breadth_count for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_pressure_score=max(
            (row.contradiction_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_router_pressure_score=max(
            (row.router_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_scraping_claim_update_latency_router_public_payload(
    report: ResearchSourceScrapingClaimUpdateLatencyRouterReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScrapingClaimUpdateLatencyRouterReport:
        raise ValueError(
            "report must be a ResearchSourceScrapingClaimUpdateLatencyRouterReport",
        )
    validate_research_source_scraping_claim_update_latency_router_digest(report)
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def validate_research_source_scraping_claim_update_latency_router_digest(
    report: ResearchSourceScrapingClaimUpdateLatencyRouterReport,
) -> None:
    if type(report) is not ResearchSourceScrapingClaimUpdateLatencyRouterReport:
        raise ValueError(
            "report must be a ResearchSourceScrapingClaimUpdateLatencyRouterReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_scraping_claim_update_latency_router_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)


def _router_rows(
    updates: tuple[ResearchSourceScrapingClaimUpdate, ...],
    *,
    config: ResearchSourceScrapingClaimUpdateLatencyRouterConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceScrapingClaimUpdateLatencyRouterRow, ...]:
    return tuple(
        sorted(
            (
                _router_row(update, config=config, generated_at=generated_at)
                for update in updates
            ),
            key=_row_sort_key,
        ),
    )


def _router_row(
    update: ResearchSourceScrapingClaimUpdate,
    *,
    config: ResearchSourceScrapingClaimUpdateLatencyRouterConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingClaimUpdateLatencyRouterRow:
    if update.scraped_at > generated_at:
        raise ValueError("scraped_at must not be after generated_at")
    if update.extracted_at > generated_at:
        raise ValueError("extracted_at must not be after generated_at")
    if update.claim_updated_at > generated_at:
        raise ValueError("claim_updated_at must not be after generated_at")
    extraction_latency_seconds = _elapsed_seconds(update.scraped_at, update.extracted_at)
    update_age_seconds = _elapsed_seconds(update.claim_updated_at, generated_at)
    corroboration_breadth_score = _bounded_ratio(
        update.corroboration_breadth_count,
        config.corroboration_breadth_watch_floor,
    )
    reason_codes = _row_reason_codes(
        extraction_latency_seconds=extraction_latency_seconds,
        update_age_seconds=update_age_seconds,
        authority_confidence_score=update.authority_confidence_score,
        corroboration_breadth_count=update.corroboration_breadth_count,
        contradiction_pressure_score=update.contradiction_pressure_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchSourceScrapingClaimUpdateLatencyRouterRow(
        claim_update_bucket=update.claim_update_bucket,
        extraction_latency_seconds=extraction_latency_seconds,
        update_age_seconds=update_age_seconds,
        authority_confidence_score=update.authority_confidence_score,
        corroboration_breadth_count=update.corroboration_breadth_count,
        corroboration_breadth_score=corroboration_breadth_score,
        contradiction_pressure_score=update.contradiction_pressure_score,
        router_pressure_score=_router_pressure_score(
            extraction_latency_seconds=extraction_latency_seconds,
            update_age_seconds=update_age_seconds,
            authority_confidence_score=update.authority_confidence_score,
            corroboration_breadth_score=corroboration_breadth_score,
            contradiction_pressure_score=update.contradiction_pressure_score,
            config=config,
            status=status,
        ),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    extraction_latency_seconds: Decimal,
    update_age_seconds: Decimal,
    authority_confidence_score: Decimal,
    corroboration_breadth_count: Decimal,
    contradiction_pressure_score: Decimal,
    config: ResearchSourceScrapingClaimUpdateLatencyRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if extraction_latency_seconds >= config.extraction_latency_block_seconds:
        reasons.append(EXTRACTION_LATENCY_BLOCK_REASON)
    elif extraction_latency_seconds >= config.extraction_latency_watch_seconds:
        reasons.append(EXTRACTION_LATENCY_WATCH_REASON)
    if update_age_seconds >= config.update_age_block_seconds:
        reasons.append(STALE_UPDATE_BLOCK_REASON)
    elif update_age_seconds >= config.update_age_watch_seconds:
        reasons.append(STALE_UPDATE_WATCH_REASON)
    if authority_confidence_score <= config.authority_confidence_block_floor:
        reasons.append(AUTHORITY_CONFIDENCE_BLOCK_REASON)
    elif authority_confidence_score < config.authority_confidence_watch_floor:
        reasons.append(AUTHORITY_CONFIDENCE_WATCH_REASON)
    if corroboration_breadth_count <= config.corroboration_breadth_block_floor:
        reasons.append(CORROBORATION_BREADTH_BLOCK_REASON)
    elif corroboration_breadth_count < config.corroboration_breadth_watch_floor:
        reasons.append(CORROBORATION_BREADTH_WATCH_REASON)
    if contradiction_pressure_score >= config.contradiction_pressure_block:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif contradiction_pressure_score >= config.contradiction_pressure_watch:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _router_pressure_score(
    *,
    extraction_latency_seconds: Decimal,
    update_age_seconds: Decimal,
    authority_confidence_score: Decimal,
    corroboration_breadth_score: Decimal,
    contradiction_pressure_score: Decimal,
    config: ResearchSourceScrapingClaimUpdateLatencyRouterConfig,
    status: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        extraction_pressure = min(
            extraction_latency_seconds / config.extraction_latency_block_seconds,
            ONE,
        )
        freshness_pressure = min(update_age_seconds / config.update_age_block_seconds, ONE)
        authority_gap = ONE - authority_confidence_score
        corroboration_gap = ONE - corroboration_breadth_score
        score = (
            extraction_pressure * config.extraction_latency_weight
            + freshness_pressure * config.update_freshness_weight
            + authority_gap * config.authority_confidence_weight
            + corroboration_gap * config.corroboration_breadth_weight
            + contradiction_pressure_score * config.contradiction_pressure_weight
        )
        if status == "pass":
            score += Decimal("0.020000")
        return min(score, ONE).quantize(QUANT)


def _report_status(
    rows: tuple[ResearchSourceScrapingClaimUpdateLatencyRouterRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScrapingClaimUpdateLatencyRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceScrapingClaimUpdateLatencyRouterRow, ...],
) -> tuple[ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _status_count(
    rows: tuple[ResearchSourceScrapingClaimUpdateLatencyRouterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_sort_key(
    row: ResearchSourceScrapingClaimUpdateLatencyRouterRow,
) -> tuple[Decimal, str]:
    return (-row.router_pressure_score, row.claim_update_bucket)


def _validate_config(
    config: ResearchSourceScrapingClaimUpdateLatencyRouterConfig,
) -> None:
    if config.extraction_latency_block_seconds <= config.extraction_latency_watch_seconds:
        raise ValueError(
            "extraction_latency_block_seconds must exceed "
            "extraction_latency_watch_seconds",
        )
    if config.update_age_block_seconds <= config.update_age_watch_seconds:
        raise ValueError("update_age_block_seconds must exceed update_age_watch_seconds")
    if config.authority_confidence_block_floor > config.authority_confidence_watch_floor:
        raise ValueError(
            "authority_confidence_block_floor must not exceed "
            "authority_confidence_watch_floor",
        )
    if config.corroboration_breadth_block_floor >= config.corroboration_breadth_watch_floor:
        raise ValueError(
            "corroboration_breadth_block_floor must be less than "
            "corroboration_breadth_watch_floor",
        )
    if config.contradiction_pressure_block < config.contradiction_pressure_watch:
        raise ValueError(
            "contradiction_pressure_block must be greater than or equal to "
            "contradiction_pressure_watch",
        )
    weight_sum = (
        config.extraction_latency_weight
        + config.update_freshness_weight
        + config.authority_confidence_weight
        + config.corroboration_breadth_weight
        + config.contradiction_pressure_weight
    ).quantize(QUANT)
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_row(row: ResearchSourceScrapingClaimUpdateLatencyRouterRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason")


def _validate_report(report: ResearchSourceScrapingClaimUpdateLatencyRouterReport) -> None:
    if report.update_count != _count(len(report.rows)):
        raise ValueError("update_count must match rows")
    for status, field_name in (
        ("pass", "pass_update_count"),
        ("watch", "watch_update_count"),
        ("block", "block_update_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.max_extraction_latency_seconds != max(
        (row.extraction_latency_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("max_extraction_latency_seconds must match rows")
    if report.oldest_update_age_seconds != max(
        (row.update_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_update_age_seconds must match rows")
    if report.lowest_authority_confidence_score != min(
        (row.authority_confidence_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_authority_confidence_score must match rows")
    if report.lowest_corroboration_breadth_count != min(
        (row.corroboration_breadth_count for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_corroboration_breadth_count must match rows")
    if report.highest_contradiction_pressure_score != max(
        (row.contradiction_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.highest_router_pressure_score != max(
        (row.router_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_router_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic router pressure sort")


def _normalize_updates(
    value: object,
) -> tuple[ResearchSourceScrapingClaimUpdate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("updates must be a list or tuple")
    updates = tuple(value)
    seen: set[str] = set()
    for update in updates:
        if type(update) is not ResearchSourceScrapingClaimUpdate:
            raise ValueError("updates must contain ResearchSourceScrapingClaimUpdate")
        _require_hard_flags("update", update)
        if update.claim_update_bucket in seen:
            raise ValueError("updates must be unique by claim_update_bucket")
        seen.add(update.claim_update_bucket)
    return tuple(sorted(updates, key=lambda update: update.claim_update_bucket))


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceScrapingClaimUpdateLatencyRouterRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceScrapingClaimUpdateLatencyRouterRow:
            raise ValueError(
                "rows must contain ResearchSourceScrapingClaimUpdateLatencyRouterRow",
            )
        _require_hard_flags("row", row)
        if row.claim_update_bucket in seen:
            raise ValueError("rows must be unique by claim_update_bucket")
        seen.add(row.claim_update_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScrapingClaimUpdateLatencyRouterReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
    return tuple(
        sorted(counts, key=lambda item: REPORT_REASON_CODES.index(item.reason_code)),
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reasons = tuple(value)
    seen: set[str] = set()
    for reason in reasons:
        if type(reason) is not str or reason not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
        if reason in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason)
    return tuple(reason for reason in allowed if reason in seen)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_SCRAPING_CLAIM_UPDATE_LATENCY_ROUTER_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _elapsed_seconds(started_at: datetime, ended_at: datetime) -> Decimal:
    elapsed = ended_at - started_at
    if elapsed.days < 0:
        raise ValueError("elapsed seconds must be nonnegative")
    elapsed_microseconds = (
        ((elapsed.days * 86400) + elapsed.seconds) * 1000000
    ) + elapsed.microseconds
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(elapsed_microseconds) / Decimal("1000000")).quantize(QUANT)


def _report_digest_from_public_payload(
    report: ResearchSourceScrapingClaimUpdateLatencyRouterReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    if digest != _payload_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


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
    if type(value) is int or type(value) is float:
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    raise ValueError("payload contains unsupported value")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError("unsafe public payload")
            _reject_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
    elif type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("unsafe public payload")
    elif type(value) in (bool, type(None)):
        return
    elif type(value) is int or type(value) is float:
        raise ValueError("unsafe public payload")
