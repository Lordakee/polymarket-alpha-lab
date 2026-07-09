"""Pure report-only source disagreement routing for analyst review."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_REPORT_CONFIG_VERSION = (
    "research-source-authority-freshness-disagreement-router-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_source_authority_freshness_disagreement_router_empty"
CLEAR_REASON = "research_source_authority_freshness_disagreement_router_clear"
LOW_AUTHORITY_WATCH_REASON = (
    "research_source_authority_freshness_disagreement_router_low_authority_watch"
)
LOW_AUTHORITY_BLOCK_REASON = (
    "research_source_authority_freshness_disagreement_router_low_authority_block"
)
STALE_FRESHNESS_WATCH_REASON = (
    "research_source_authority_freshness_disagreement_router_stale_freshness_watch"
)
STALE_FRESHNESS_BLOCK_REASON = (
    "research_source_authority_freshness_disagreement_router_stale_freshness_block"
)
THIN_CORROBORATION_WATCH_REASON = (
    "research_source_authority_freshness_disagreement_router_thin_corroboration_watch"
)
THIN_CORROBORATION_BLOCK_REASON = (
    "research_source_authority_freshness_disagreement_router_thin_corroboration_block"
)
LOW_EXTRACTION_CONFIDENCE_WATCH_REASON = (
    "research_source_authority_freshness_disagreement_router_"
    "low_extraction_confidence_watch"
)
LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON = (
    "research_source_authority_freshness_disagreement_router_"
    "low_extraction_confidence_block"
)
CONFLICT_PRESSURE_WATCH_REASON = (
    "research_source_authority_freshness_disagreement_router_conflict_pressure_watch"
)
CONFLICT_PRESSURE_BLOCK_REASON = (
    "research_source_authority_freshness_disagreement_router_conflict_pressure_block"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_AUTHORITY_BLOCK_REASON,
    STALE_FRESHNESS_BLOCK_REASON,
    THIN_CORROBORATION_BLOCK_REASON,
    LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
    CONFLICT_PRESSURE_BLOCK_REASON,
    LOW_AUTHORITY_WATCH_REASON,
    STALE_FRESHNESS_WATCH_REASON,
    THIN_CORROBORATION_WATCH_REASON,
    LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
    CONFLICT_PRESSURE_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

AUTHORITY_TIER_SCORES = (
    ("official", Decimal("1.000000")),
    ("primary", Decimal("0.850000")),
    ("secondary", Decimal("0.650000")),
    ("tertiary", Decimal("0.400000")),
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "recommendation",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "candidate-",
    "candidate_id",
    "market-",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "token",
    "wallet",
    "order",
    "trade",
    "live_surface",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessDisagreementRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_REPORT_CONFIG_VERSION
    )
    authority_watch_floor: Decimal = Decimal("0.700000")
    authority_block_floor: Decimal = Decimal("0.500000")
    freshness_watch_lag_seconds: Decimal = Decimal("1800.000000")
    freshness_block_lag_seconds: Decimal = Decimal("3600.000000")
    corroboration_watch_breadth: Decimal = Decimal("2.000000")
    corroboration_block_breadth: Decimal = Decimal("0.000000")
    extraction_confidence_watch_floor: Decimal = Decimal("0.800000")
    extraction_confidence_block_floor: Decimal = Decimal("0.600000")
    conflict_watch_pressure: Decimal = Decimal("0.300000")
    conflict_block_pressure: Decimal = Decimal("0.600000")
    authority_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.200000")
    corroboration_weight: Decimal = Decimal("0.200000")
    extraction_weight: Decimal = Decimal("0.200000")
    conflict_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessDisagreementRouterConfig:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessDisagreementRouterConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessDisagreementRouterConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceAuthorityFreshnessDisagreementRouterConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "authority_watch_floor",
            "authority_block_floor",
            "extraction_confidence_watch_floor",
            "extraction_confidence_block_floor",
            "conflict_watch_pressure",
            "conflict_block_pressure",
            "authority_weight",
            "freshness_weight",
            "corroboration_weight",
            "extraction_weight",
            "conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_watch_lag_seconds",
            "freshness_block_lag_seconds",
            "corroboration_watch_breadth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_block_breadth",
            _require_nonnegative_decimal(
                "corroboration_block_breadth",
                self.corroboration_block_breadth,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessDisagreementRouterInput:
    disagreement_bucket: str
    authority_tier: str
    freshness_lag_seconds: Decimal
    corroboration_breadth_count: Decimal
    extraction_confidence_score: Decimal
    conflict_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessDisagreementRouterInput:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessDisagreementRouterInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessDisagreementRouterInput:
            raise ValueError(
                "input must be exactly "
                "ResearchSourceAuthorityFreshnessDisagreementRouterInput",
            )
        object.__setattr__(
            self,
            "disagreement_bucket",
            _require_public_bucket("disagreement_bucket", self.disagreement_bucket),
        )
        _require_authority_tier("authority_tier", self.authority_tier)
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _require_nonnegative_decimal(
                "freshness_lag_seconds",
                self.freshness_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroboration_breadth_count",
            _require_nonnegative_whole_decimal(
                "corroboration_breadth_count",
                self.corroboration_breadth_count,
            ),
        )
        for field_name in ("extraction_confidence_score", "conflict_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessDisagreementRouterRow:
    disagreement_bucket: str
    authority_tier: str
    authority_tier_score: Decimal
    authority_band: str
    freshness_lag_seconds: Decimal
    freshness_band: str
    corroboration_breadth_count: Decimal
    corroboration_breadth_score: Decimal
    extraction_confidence_score: Decimal
    conflict_pressure_score: Decimal
    router_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessDisagreementRouterRow:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessDisagreementRouterRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessDisagreementRouterRow:
            raise ValueError(
                "row must be exactly ResearchSourceAuthorityFreshnessDisagreementRouterRow",
            )
        object.__setattr__(
            self,
            "disagreement_bucket",
            _require_public_bucket("disagreement_bucket", self.disagreement_bucket),
        )
        _require_authority_tier("authority_tier", self.authority_tier)
        for field_name in (
            "authority_tier_score",
            "corroboration_breadth_score",
            "extraction_confidence_score",
            "conflict_pressure_score",
            "router_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _require_nonnegative_decimal(
                "freshness_lag_seconds",
                self.freshness_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroboration_breadth_count",
            _require_nonnegative_whole_decimal(
                "corroboration_breadth_count",
                self.corroboration_breadth_count,
            ),
        )
        _require_authority_band("authority_band", self.authority_band)
        _require_freshness_band("freshness_band", self.freshness_band)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount
        ):
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount",
            )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessDisagreementRouterReport:
    generated_at: datetime
    config_version: str
    disagreement_count: Decimal
    pass_disagreement_count: Decimal
    watch_disagreement_count: Decimal
    block_disagreement_count: Decimal
    low_authority_count: Decimal
    stale_freshness_count: Decimal
    thin_corroboration_count: Decimal
    low_extraction_confidence_count: Decimal
    conflict_pressure_count: Decimal
    highest_router_pressure_score: Decimal
    lowest_authority_tier_score: Decimal
    oldest_freshness_lag_seconds: Decimal
    lowest_corroboration_breadth_count: Decimal
    lowest_extraction_confidence_score: Decimal
    highest_conflict_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessDisagreementRouterReport:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessDisagreementRouterReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessDisagreementRouterReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceAuthorityFreshnessDisagreementRouterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "disagreement_count",
            "pass_disagreement_count",
            "watch_disagreement_count",
            "block_disagreement_count",
            "low_authority_count",
            "stale_freshness_count",
            "thin_corroboration_count",
            "low_extraction_confidence_count",
            "conflict_pressure_count",
            "oldest_freshness_lag_seconds",
            "lowest_corroboration_breadth_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_router_pressure_score",
            "lowest_authority_tier_score",
            "lowest_extraction_confidence_score",
            "highest_conflict_pressure_score",
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
        _require_hard_flags("report", self)
        _require_or_set_digest(self)


def build_research_source_authority_freshness_disagreement_router_report(
    inputs: list[ResearchSourceAuthorityFreshnessDisagreementRouterInput]
    | tuple[ResearchSourceAuthorityFreshnessDisagreementRouterInput, ...],
    *,
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityFreshnessDisagreementRouterReport:
    if type(config) is not ResearchSourceAuthorityFreshnessDisagreementRouterConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityFreshnessDisagreementRouterConfig",
        )
    _require_hard_flags("config", config)
    rows = _router_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityFreshnessDisagreementRouterReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        disagreement_count=_count(len(rows)),
        pass_disagreement_count=_status_count(rows, "pass"),
        watch_disagreement_count=_status_count(rows, "watch"),
        block_disagreement_count=_status_count(rows, "block"),
        low_authority_count=_reason_count(
            rows,
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        stale_freshness_count=_reason_count(
            rows,
            (STALE_FRESHNESS_WATCH_REASON, STALE_FRESHNESS_BLOCK_REASON),
        ),
        thin_corroboration_count=_reason_count(
            rows,
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        low_extraction_confidence_count=_reason_count(
            rows,
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        conflict_pressure_count=_reason_count(
            rows,
            (CONFLICT_PRESSURE_WATCH_REASON, CONFLICT_PRESSURE_BLOCK_REASON),
        ),
        highest_router_pressure_score=max(
            (row.router_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_authority_tier_score=min(
            (row.authority_tier_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_freshness_lag_seconds=max(
            (row.freshness_lag_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_corroboration_breadth_count=min(
            (row.corroboration_breadth_count for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_extraction_confidence_score=min(
            (row.extraction_confidence_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_conflict_pressure_score=max(
            (row.conflict_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_authority_freshness_disagreement_router_report_payload(
    report: ResearchSourceAuthorityFreshnessDisagreementRouterReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityFreshnessDisagreementRouterReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityFreshnessDisagreementRouterReport",
        )
    validate_research_source_authority_freshness_disagreement_router_report_digest(
        report,
    )
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def research_source_authority_freshness_disagreement_router_report_digest(
    report: ResearchSourceAuthorityFreshnessDisagreementRouterReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityFreshnessDisagreementRouterReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityFreshnessDisagreementRouterReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_freshness_disagreement_router_report_digest(
    report: ResearchSourceAuthorityFreshnessDisagreementRouterReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityFreshnessDisagreementRouterReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityFreshnessDisagreementRouterReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_authority_freshness_disagreement_router_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityFreshnessDisagreementRouterInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityFreshnessDisagreementRouterInput:
            raise ValueError(
                "inputs must contain "
                "ResearchSourceAuthorityFreshnessDisagreementRouterInput",
            )
        _require_hard_flags("input", row)
        if row.disagreement_bucket in seen:
            raise ValueError("inputs must be unique by disagreement_bucket")
        seen.add(row.disagreement_bucket)
    return tuple(sorted(rows, key=lambda row: row.disagreement_bucket))


def _router_rows(
    inputs: tuple[ResearchSourceAuthorityFreshnessDisagreementRouterInput, ...],
    *,
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
) -> tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...]:
    return tuple(sorted((_router_row(row, config=config) for row in inputs), key=_row_sort_key))


def _router_row(
    row: ResearchSourceAuthorityFreshnessDisagreementRouterInput,
    *,
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
) -> ResearchSourceAuthorityFreshnessDisagreementRouterRow:
    authority_tier_score = _authority_tier_score(row.authority_tier)
    corroboration_breadth_score = _bounded_ratio(
        row.corroboration_breadth_count,
        config.corroboration_watch_breadth,
    )
    router_pressure_score = _router_pressure_score(
        authority_tier_score=authority_tier_score,
        freshness_lag_seconds=row.freshness_lag_seconds,
        corroboration_breadth_score=corroboration_breadth_score,
        extraction_confidence_score=row.extraction_confidence_score,
        conflict_pressure_score=row.conflict_pressure_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        authority_tier_score=authority_tier_score,
        config=config,
    )
    return ResearchSourceAuthorityFreshnessDisagreementRouterRow(
        disagreement_bucket=row.disagreement_bucket,
        authority_tier=row.authority_tier,
        authority_tier_score=authority_tier_score,
        authority_band=_authority_band(authority_tier_score, config=config),
        freshness_lag_seconds=row.freshness_lag_seconds,
        freshness_band=_freshness_band(row.freshness_lag_seconds, config=config),
        corroboration_breadth_count=row.corroboration_breadth_count,
        corroboration_breadth_score=corroboration_breadth_score,
        extraction_confidence_score=row.extraction_confidence_score,
        conflict_pressure_score=row.conflict_pressure_score,
        router_pressure_score=router_pressure_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityFreshnessDisagreementRouterInput,
    *,
    authority_tier_score: Decimal,
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if authority_tier_score <= config.authority_block_floor:
        reasons.append(LOW_AUTHORITY_BLOCK_REASON)
    elif authority_tier_score < config.authority_watch_floor:
        reasons.append(LOW_AUTHORITY_WATCH_REASON)
    if row.freshness_lag_seconds >= config.freshness_block_lag_seconds:
        reasons.append(STALE_FRESHNESS_BLOCK_REASON)
    elif row.freshness_lag_seconds > config.freshness_watch_lag_seconds:
        reasons.append(STALE_FRESHNESS_WATCH_REASON)
    if row.corroboration_breadth_count <= config.corroboration_block_breadth:
        reasons.append(THIN_CORROBORATION_BLOCK_REASON)
    elif row.corroboration_breadth_count < config.corroboration_watch_breadth:
        reasons.append(THIN_CORROBORATION_WATCH_REASON)
    if row.extraction_confidence_score <= config.extraction_confidence_block_floor:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON)
    elif row.extraction_confidence_score < config.extraction_confidence_watch_floor:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_WATCH_REASON)
    if row.conflict_pressure_score >= config.conflict_block_pressure:
        reasons.append(CONFLICT_PRESSURE_BLOCK_REASON)
    elif row.conflict_pressure_score >= config.conflict_watch_pressure:
        reasons.append(CONFLICT_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _router_pressure_score(
    *,
    authority_tier_score: Decimal,
    freshness_lag_seconds: Decimal,
    corroboration_breadth_score: Decimal,
    extraction_confidence_score: Decimal,
    conflict_pressure_score: Decimal,
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = ONE - authority_tier_score
        freshness_pressure = min(freshness_lag_seconds / config.freshness_block_lag_seconds, ONE)
        corroboration_gap = ONE - corroboration_breadth_score
        extraction_gap = ONE - extraction_confidence_score
        score = (
            authority_gap * config.authority_weight
            + freshness_pressure * config.freshness_weight
            + corroboration_gap * config.corroboration_weight
            + extraction_gap * config.extraction_weight
            + conflict_pressure_score * config.conflict_weight
        )
        return min(score, ONE).quantize(QUANT)


def _authority_tier_score(value: str) -> Decimal:
    for tier_name, tier_score in AUTHORITY_TIER_SCORES:
        if value == tier_name:
            return tier_score
    raise ValueError("authority_tier must be official, primary, secondary, or tertiary")


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _authority_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
) -> str:
    if value >= config.authority_watch_floor:
        return "high"
    if value <= config.authority_block_floor:
        return "low"
    return "medium"


def _freshness_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
) -> str:
    if value <= config.freshness_watch_lag_seconds:
        return "fresh"
    if value < config.freshness_block_lag_seconds:
        return "aging"
    return "stale"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...],
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
    return (CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...],
) -> tuple[ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REPORT_REASON_CODES
        if reason_code in counts
    )


def _row_sort_key(
    row: ResearchSourceAuthorityFreshnessDisagreementRouterRow,
) -> tuple[Decimal, str]:
    return (-row.router_pressure_score, row.disagreement_bucket)


def _status_count(
    rows: tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(
    config: ResearchSourceAuthorityFreshnessDisagreementRouterConfig,
) -> None:
    if config.authority_block_floor > config.authority_watch_floor:
        raise ValueError("authority_block_floor must not exceed authority_watch_floor")
    if config.freshness_watch_lag_seconds >= config.freshness_block_lag_seconds:
        raise ValueError(
            "freshness_watch_lag_seconds must be less than freshness_block_lag_seconds",
        )
    if config.corroboration_block_breadth >= config.corroboration_watch_breadth:
        raise ValueError(
            "corroboration_block_breadth must be less than corroboration_watch_breadth",
        )
    if config.extraction_confidence_block_floor > config.extraction_confidence_watch_floor:
        raise ValueError(
            "extraction_confidence_block_floor must not exceed "
            "extraction_confidence_watch_floor",
        )
    if config.conflict_watch_pressure > config.conflict_block_pressure:
        raise ValueError("conflict_watch_pressure must not exceed conflict_block_pressure")
    weight_sum = (
        config.authority_weight
        + config.freshness_weight
        + config.corroboration_weight
        + config.extraction_weight
        + config.conflict_weight
    ).quantize(QUANT)
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_row(row: ResearchSourceAuthorityFreshnessDisagreementRouterRow) -> None:
    if row.authority_tier_score != _authority_tier_score(row.authority_tier):
        raise ValueError("authority_tier_score must match authority_tier")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(
    report: ResearchSourceAuthorityFreshnessDisagreementRouterReport,
) -> None:
    if report.disagreement_count != _count(len(report.rows)):
        raise ValueError("disagreement_count must match rows")
    for status, field_name in (
        ("pass", "pass_disagreement_count"),
        ("watch", "watch_disagreement_count"),
        ("block", "block_disagreement_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        ("low_authority_count", (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON)),
        (
            "stale_freshness_count",
            (STALE_FRESHNESS_WATCH_REASON, STALE_FRESHNESS_BLOCK_REASON),
        ),
        (
            "thin_corroboration_count",
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        (
            "low_extraction_confidence_count",
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        (
            "conflict_pressure_count",
            (CONFLICT_PRESSURE_WATCH_REASON, CONFLICT_PRESSURE_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_router_pressure_score != max(
        (row.router_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_router_pressure_score must match rows")
    if report.lowest_authority_tier_score != min(
        (row.authority_tier_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_authority_tier_score must match rows")
    if report.oldest_freshness_lag_seconds != max(
        (row.freshness_lag_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_freshness_lag_seconds must match rows")
    if report.lowest_corroboration_breadth_count != min(
        (row.corroboration_breadth_count for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_corroboration_breadth_count must match rows")
    if report.lowest_extraction_confidence_score != min(
        (row.extraction_confidence_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_extraction_confidence_score must match rows")
    if report.highest_conflict_pressure_score != max(
        (row.conflict_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_conflict_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic router pressure sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityFreshnessDisagreementRouterRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityFreshnessDisagreementRouterRow:
            raise ValueError(
                "rows must contain ResearchSourceAuthorityFreshnessDisagreementRouterRow",
            )
        _require_hard_flags("row", row)
        if row.disagreement_bucket in seen:
            raise ValueError("rows must be unique by disagreement_bucket")
        seen.add(row.disagreement_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
    expected_order = tuple(reason for reason in REPORT_REASON_CODES if reason in seen)
    if tuple(item.reason_code for item in counts) != expected_order:
        raise ValueError("reason_code_counts must be deterministic")
    return counts


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
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
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_authority_tier(field_name: str, value: object) -> None:
    if type(value) is not str or value not in tuple(
        tier_name for tier_name, _tier_score in AUTHORITY_TIER_SCORES
    ):
        raise ValueError(
            f"{field_name} must be official, primary, secondary, or tertiary",
        )


def _require_authority_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("high", "medium", "low"):
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_freshness_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "aging", "stale"):
        raise ValueError(f"{field_name} must be fresh, aging, or stale")


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


def _require_public_bucket(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(char.isalnum() or char in (".", "_", "-") for char in value):
        raise ValueError(f"{field_name} must be a public bucket label")
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


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name}.{flag_name} must be True")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_or_set_digest(
    report: ResearchSourceAuthorityFreshnessDisagreementRouterReport,
) -> None:
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
    report: ResearchSourceAuthorityFreshnessDisagreementRouterReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
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
    raise ValueError("value is not JSON-ready")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("public payload contains unsafe key")
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe text")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, (float, int)):
        raise ValueError("public payload contains non-Decimal numeric value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_FRESHNESS_DISAGREEMENT_ROUTER_STATUSES",
    "ResearchSourceAuthorityFreshnessDisagreementRouterConfig",
    "ResearchSourceAuthorityFreshnessDisagreementRouterInput",
    "ResearchSourceAuthorityFreshnessDisagreementRouterReasonCodeCount",
    "ResearchSourceAuthorityFreshnessDisagreementRouterReport",
    "ResearchSourceAuthorityFreshnessDisagreementRouterRow",
    "build_research_source_authority_freshness_disagreement_router_report",
    "research_source_authority_freshness_disagreement_router_report_digest",
    "research_source_authority_freshness_disagreement_router_report_payload",
    "validate_research_source_authority_freshness_disagreement_router_public_payload",
    "validate_research_source_authority_freshness_disagreement_router_report_digest",
)
