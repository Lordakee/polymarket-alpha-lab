"""Pure report-only source authority event claim traceability reducer."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_STATUSES",
    "ResearchSourceAuthorityEventClaimTraceabilityConfig",
    "ResearchSourceAuthorityEventClaimTraceabilityInput",
    "ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount",
    "ResearchSourceAuthorityEventClaimTraceabilityReport",
    "ResearchSourceAuthorityEventClaimTraceabilityRow",
    "build_research_source_authority_event_claim_traceability_report",
    "research_source_authority_event_claim_traceability_report_digest",
    "research_source_authority_event_claim_traceability_report_payload",
    "validate_research_source_authority_event_claim_traceability_public_payload",
    "validate_research_source_authority_event_claim_traceability_report_digest",
)


DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION = (
    "research-source-authority-event-claim-traceability-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

AUTHORITY_TIERS = ("official", "primary", "secondary", "contested")

CLEAR_REASON = "research_source_authority_event_claim_traceability_clear"
LOW_AUTHORITY_WATCH_REASON = (
    "research_source_authority_event_claim_traceability_low_authority_watch"
)
LOW_AUTHORITY_BLOCK_REASON = (
    "research_source_authority_event_claim_traceability_low_authority_block"
)
LOW_TRACE_COVERAGE_WATCH_REASON = (
    "research_source_authority_event_claim_traceability_low_trace_coverage_watch"
)
LOW_TRACE_COVERAGE_BLOCK_REASON = (
    "research_source_authority_event_claim_traceability_low_trace_coverage_block"
)
STALE_SOURCE_WATCH_REASON = (
    "research_source_authority_event_claim_traceability_stale_source_watch"
)
STALE_SOURCE_BLOCK_REASON = (
    "research_source_authority_event_claim_traceability_stale_source_block"
)
CONTRADICTION_WATCH_REASON = (
    "research_source_authority_event_claim_traceability_contradiction_watch"
)
CONTRADICTION_BLOCK_REASON = (
    "research_source_authority_event_claim_traceability_contradiction_block"
)
UNRESOLVED_CLAIM_WATCH_REASON = (
    "research_source_authority_event_claim_traceability_unresolved_claim_watch"
)
UNRESOLVED_CLAIM_BLOCK_REASON = (
    "research_source_authority_event_claim_traceability_unresolved_claim_block"
)
DEEP_LINEAGE_WATCH_REASON = (
    "research_source_authority_event_claim_traceability_deep_lineage_watch"
)
DEEP_LINEAGE_BLOCK_REASON = (
    "research_source_authority_event_claim_traceability_deep_lineage_block"
)

REPORT_EMPTY_REASON = "research_source_authority_event_claim_traceability_report_empty"
REPORT_PASS_REASON = "research_source_authority_event_claim_traceability_report_pass"
REPORT_WATCH_REASON = "research_source_authority_event_claim_traceability_report_watch"
REPORT_BLOCK_REASON = "research_source_authority_event_claim_traceability_report_block"
LOW_AUTHORITY_EXCEPTION_REASON = (
    "research_source_authority_event_claim_traceability_low_authority_exception"
)
LOW_TRACE_COVERAGE_EXCEPTION_REASON = (
    "research_source_authority_event_claim_traceability_low_trace_coverage_exception"
)
STALE_SOURCE_EXCEPTION_REASON = (
    "research_source_authority_event_claim_traceability_stale_source_exception"
)
CONTRADICTION_EXCEPTION_REASON = (
    "research_source_authority_event_claim_traceability_contradiction_exception"
)
UNRESOLVED_CLAIM_EXCEPTION_REASON = (
    "research_source_authority_event_claim_traceability_unresolved_claim_exception"
)
DEEP_LINEAGE_EXCEPTION_REASON = (
    "research_source_authority_event_claim_traceability_deep_lineage_exception"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_AUTHORITY_BLOCK_REASON,
    LOW_TRACE_COVERAGE_BLOCK_REASON,
    STALE_SOURCE_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    UNRESOLVED_CLAIM_BLOCK_REASON,
    DEEP_LINEAGE_BLOCK_REASON,
    LOW_AUTHORITY_WATCH_REASON,
    LOW_TRACE_COVERAGE_WATCH_REASON,
    STALE_SOURCE_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    UNRESOLVED_CLAIM_WATCH_REASON,
    DEEP_LINEAGE_WATCH_REASON,
)
REPORT_REASON_CODES = (
    REPORT_EMPTY_REASON,
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    REPORT_BLOCK_REASON,
    LOW_AUTHORITY_EXCEPTION_REASON,
    LOW_TRACE_COVERAGE_EXCEPTION_REASON,
    STALE_SOURCE_EXCEPTION_REASON,
    CONTRADICTION_EXCEPTION_REASON,
    UNRESOLVED_CLAIM_EXCEPTION_REASON,
    DEEP_LINEAGE_EXCEPTION_REASON,
) + ROW_REASON_CODES

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table_name",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
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
    "market_question",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "private_token",
    "token",
    "wallet",
    "order",
    "trade",
    "live_surface",
    "sizing",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityEventClaimTraceabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION
    )
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.600000")
    min_pass_trace_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_trace_coverage_ratio: Decimal = Decimal("0.700000")
    max_pass_contradiction_ratio: Decimal = Decimal("0.100000")
    max_watch_contradiction_ratio: Decimal = Decimal("0.300000")
    max_pass_unresolved_claim_ratio: Decimal = Decimal("0.050000")
    max_watch_unresolved_claim_ratio: Decimal = Decimal("0.200000")
    source_age_watch_seconds: Decimal = Decimal("3600.000000")
    source_age_block_seconds: Decimal = Decimal("7200.000000")
    max_watch_lineage_depth: Decimal = Decimal("4.000000")
    max_block_lineage_depth: Decimal = Decimal("7.000000")
    authority_weight: Decimal = Decimal("0.350000")
    trace_coverage_weight: Decimal = Decimal("0.350000")
    freshness_weight: Decimal = Decimal("0.150000")
    claim_consistency_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEventClaimTraceabilityConfig:
            raise TypeError(
                "ResearchSourceAuthorityEventClaimTraceabilityConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityEventClaimTraceabilityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_trace_coverage_ratio",
            "min_watch_trace_coverage_ratio",
            "max_pass_contradiction_ratio",
            "max_watch_contradiction_ratio",
            "max_pass_unresolved_claim_ratio",
            "max_watch_unresolved_claim_ratio",
            "authority_weight",
            "trace_coverage_weight",
            "freshness_weight",
            "claim_consistency_weight",
        ):
            object.__setattr__(self, field_name, _require_ratio(field_name, getattr(self, field_name)))
        for field_name in (
            "source_age_watch_seconds",
            "source_age_block_seconds",
            "max_watch_lineage_depth",
            "max_block_lineage_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEventClaimTraceabilityInput:
    private_event_claim_key: str
    authority_tier: str
    claim_lineage_depth: Decimal
    supporting_source_count: Decimal
    authoritative_source_count: Decimal
    traced_source_count: Decimal
    stale_source_count: Decimal
    contradictory_source_count: Decimal
    unresolved_claim_count: Decimal
    max_source_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEventClaimTraceabilityInput:
            raise TypeError(
                "ResearchSourceAuthorityEventClaimTraceabilityInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityEventClaimTraceabilityInput,
            "input",
        )
        _require_private_claim_key("private_event_claim_key", self.private_event_claim_key)
        _require_member("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        for field_name in (
            "claim_lineage_depth",
            "supporting_source_count",
            "authoritative_source_count",
            "traced_source_count",
            "stale_source_count",
            "contradictory_source_count",
            "unresolved_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEventClaimTraceabilityRow:
    claim_trace_hash: str
    authority_tier: str
    claim_lineage_depth: Decimal
    supporting_source_count: Decimal
    authoritative_source_count: Decimal
    traced_source_count: Decimal
    stale_source_count: Decimal
    contradictory_source_count: Decimal
    unresolved_claim_count: Decimal
    max_source_age_seconds: Decimal
    authority_score: Decimal
    trace_coverage_ratio: Decimal
    freshness_score: Decimal
    contradiction_ratio: Decimal
    unresolved_claim_ratio: Decimal
    claim_consistency_score: Decimal
    claim_traceability_score: Decimal
    claim_traceability_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEventClaimTraceabilityRow:
            raise TypeError(
                "ResearchSourceAuthorityEventClaimTraceabilityRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceAuthorityEventClaimTraceabilityRow, "row")
        _require_sha256("claim_trace_hash", self.claim_trace_hash)
        _require_member("authority_tier", self.authority_tier, AUTHORITY_TIERS)
        for field_name in (
            "claim_lineage_depth",
            "supporting_source_count",
            "authoritative_source_count",
            "traced_source_count",
            "stale_source_count",
            "contradictory_source_count",
            "unresolved_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "authority_score",
            "trace_coverage_ratio",
            "freshness_score",
            "contradiction_ratio",
            "unresolved_claim_ratio",
            "claim_consistency_score",
            "claim_traceability_score",
            "claim_traceability_risk_score",
        ):
            object.__setattr__(self, field_name, _require_ratio(field_name, getattr(self, field_name)))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount:
            raise TypeError(
                "ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount,
            "reason_code_count",
        )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _require_ratio("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEventClaimTraceabilityReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_authority_count: Decimal
    low_trace_coverage_count: Decimal
    stale_source_count: Decimal
    contradictory_claim_count: Decimal
    unresolved_claim_count: Decimal
    deep_lineage_count: Decimal
    mean_trace_coverage_ratio: Decimal
    mean_claim_traceability_score: Decimal
    lowest_claim_traceability_score: Decimal
    highest_claim_traceability_risk_score: Decimal
    oldest_source_age_seconds: Decimal
    highest_contradiction_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount, ...]
    rows: tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEventClaimTraceabilityReport:
            raise TypeError(
                "ResearchSourceAuthorityEventClaimTraceabilityReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceAuthorityEventClaimTraceabilityReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_authority_count",
            "low_trace_coverage_count",
            "stale_source_count",
            "contradictory_claim_count",
            "unresolved_claim_count",
            "deep_lineage_count",
            "oldest_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_trace_coverage_ratio",
            "mean_claim_traceability_score",
            "lowest_claim_traceability_score",
            "highest_claim_traceability_risk_score",
            "highest_contradiction_ratio",
        ):
            object.__setattr__(self, field_name, _require_ratio(field_name, getattr(self, field_name)))
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
        _require_or_set_digest(self)


REPORT_PUBLIC_PAYLOAD_KEYS = tuple(
    field.name for field in fields(ResearchSourceAuthorityEventClaimTraceabilityReport)
)
ROW_PUBLIC_PAYLOAD_KEYS = tuple(
    field.name for field in fields(ResearchSourceAuthorityEventClaimTraceabilityRow)
)
REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS = tuple(
    field.name
    for field in fields(ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount)
)


def build_research_source_authority_event_claim_traceability_report(
    inputs: list[ResearchSourceAuthorityEventClaimTraceabilityInput]
    | tuple[ResearchSourceAuthorityEventClaimTraceabilityInput, ...],
    *,
    config: ResearchSourceAuthorityEventClaimTraceabilityConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityEventClaimTraceabilityReport:
    if type(config) is not ResearchSourceAuthorityEventClaimTraceabilityConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityEventClaimTraceabilityConfig",
        )
    _require_hard_flags("config", config)
    _validate_config(config)
    rows = _claim_traceability_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityEventClaimTraceabilityReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        low_authority_count=_reason_count(
            rows,
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        low_trace_coverage_count=_reason_count(
            rows,
            (LOW_TRACE_COVERAGE_WATCH_REASON, LOW_TRACE_COVERAGE_BLOCK_REASON),
        ),
        stale_source_count=_reason_count(
            rows,
            (STALE_SOURCE_WATCH_REASON, STALE_SOURCE_BLOCK_REASON),
        ),
        contradictory_claim_count=_reason_count(
            rows,
            (CONTRADICTION_WATCH_REASON, CONTRADICTION_BLOCK_REASON),
        ),
        unresolved_claim_count=_reason_count(
            rows,
            (UNRESOLVED_CLAIM_WATCH_REASON, UNRESOLVED_CLAIM_BLOCK_REASON),
        ),
        deep_lineage_count=_reason_count(
            rows,
            (DEEP_LINEAGE_WATCH_REASON, DEEP_LINEAGE_BLOCK_REASON),
        ),
        mean_trace_coverage_ratio=_mean(
            tuple(row.trace_coverage_ratio for row in rows),
        ),
        mean_claim_traceability_score=_mean(
            tuple(row.claim_traceability_score for row in rows),
        ),
        lowest_claim_traceability_score=min(
            (row.claim_traceability_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_claim_traceability_risk_score=max(
            (row.claim_traceability_risk_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_source_age_seconds=max(
            (row.max_source_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_ratio=max(
            (row.contradiction_ratio for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_authority_event_claim_traceability_report_payload(
    report: ResearchSourceAuthorityEventClaimTraceabilityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityEventClaimTraceabilityReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityEventClaimTraceabilityReport",
        )
    validate_research_source_authority_event_claim_traceability_report_digest(report)
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def research_source_authority_event_claim_traceability_report_digest(
    report: ResearchSourceAuthorityEventClaimTraceabilityReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityEventClaimTraceabilityReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityEventClaimTraceabilityReport",
        )
    _validate_report(report)
    _require_hard_flags("report", report)
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_event_claim_traceability_report_digest(
    report: ResearchSourceAuthorityEventClaimTraceabilityReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityEventClaimTraceabilityReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityEventClaimTraceabilityReport",
        )
    _validate_report(report)
    _require_hard_flags("report", report)
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_authority_event_claim_traceability_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    _validate_public_payload_schema(payload)


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceAuthorityEventClaimTraceabilityReport:
    _require_public_payload_keys(
        "public payload",
        payload,
        REPORT_PUBLIC_PAYLOAD_KEYS,
    )
    return ResearchSourceAuthorityEventClaimTraceabilityReport(
        generated_at=_require_public_datetime_string(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_require_public_config_version(payload["config_version"]),
        input_row_count=_require_public_decimal_string(
            "input_row_count",
            payload["input_row_count"],
        ),
        pass_count=_require_public_decimal_string("pass_count", payload["pass_count"]),
        watch_count=_require_public_decimal_string(
            "watch_count",
            payload["watch_count"],
        ),
        block_count=_require_public_decimal_string(
            "block_count",
            payload["block_count"],
        ),
        low_authority_count=_require_public_decimal_string(
            "low_authority_count",
            payload["low_authority_count"],
        ),
        low_trace_coverage_count=_require_public_decimal_string(
            "low_trace_coverage_count",
            payload["low_trace_coverage_count"],
        ),
        stale_source_count=_require_public_decimal_string(
            "stale_source_count",
            payload["stale_source_count"],
        ),
        contradictory_claim_count=_require_public_decimal_string(
            "contradictory_claim_count",
            payload["contradictory_claim_count"],
        ),
        unresolved_claim_count=_require_public_decimal_string(
            "unresolved_claim_count",
            payload["unresolved_claim_count"],
        ),
        deep_lineage_count=_require_public_decimal_string(
            "deep_lineage_count",
            payload["deep_lineage_count"],
        ),
        mean_trace_coverage_ratio=_require_public_decimal_string(
            "mean_trace_coverage_ratio",
            payload["mean_trace_coverage_ratio"],
        ),
        mean_claim_traceability_score=_require_public_decimal_string(
            "mean_claim_traceability_score",
            payload["mean_claim_traceability_score"],
        ),
        lowest_claim_traceability_score=_require_public_decimal_string(
            "lowest_claim_traceability_score",
            payload["lowest_claim_traceability_score"],
        ),
        highest_claim_traceability_risk_score=_require_public_decimal_string(
            "highest_claim_traceability_risk_score",
            payload["highest_claim_traceability_risk_score"],
        ),
        oldest_source_age_seconds=_require_public_decimal_string(
            "oldest_source_age_seconds",
            payload["oldest_source_age_seconds"],
        ),
        highest_contradiction_ratio=_require_public_decimal_string(
            "highest_contradiction_ratio",
            payload["highest_contradiction_ratio"],
        ),
        status=_require_public_status("status", payload["status"]),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        reason_code_counts=_reason_code_counts_from_public_payload(
            payload["reason_code_counts"],
        ),
        rows=_rows_from_public_payload(payload["rows"]),
        derived_validation_digest=_require_public_digest_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_public_flag("paper_only", payload["paper_only"]),
        report_only=_require_public_flag("report_only", payload["report_only"]),
        readonly=_require_public_flag("readonly", payload["readonly"]),
    )


def _rows_from_public_payload(
    value: object,
) -> tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a public JSON list")
    return tuple(_row_from_public_payload(index, item) for index, item in enumerate(value))


def _row_from_public_payload(
    index: int,
    value: object,
) -> ResearchSourceAuthorityEventClaimTraceabilityRow:
    if type(value) is not dict:
        raise ValueError("rows must contain public JSON objects")
    label = f"rows[{index}]"
    _require_public_payload_keys(label, value, ROW_PUBLIC_PAYLOAD_KEYS)
    return ResearchSourceAuthorityEventClaimTraceabilityRow(
        claim_trace_hash=_require_public_digest_string(
            f"{label}.claim_trace_hash",
            value["claim_trace_hash"],
        ),
        authority_tier=_require_public_member(
            f"{label}.authority_tier",
            value["authority_tier"],
            AUTHORITY_TIERS,
        ),
        claim_lineage_depth=_require_public_decimal_string(
            f"{label}.claim_lineage_depth",
            value["claim_lineage_depth"],
        ),
        supporting_source_count=_require_public_decimal_string(
            f"{label}.supporting_source_count",
            value["supporting_source_count"],
        ),
        authoritative_source_count=_require_public_decimal_string(
            f"{label}.authoritative_source_count",
            value["authoritative_source_count"],
        ),
        traced_source_count=_require_public_decimal_string(
            f"{label}.traced_source_count",
            value["traced_source_count"],
        ),
        stale_source_count=_require_public_decimal_string(
            f"{label}.stale_source_count",
            value["stale_source_count"],
        ),
        contradictory_source_count=_require_public_decimal_string(
            f"{label}.contradictory_source_count",
            value["contradictory_source_count"],
        ),
        unresolved_claim_count=_require_public_decimal_string(
            f"{label}.unresolved_claim_count",
            value["unresolved_claim_count"],
        ),
        max_source_age_seconds=_require_public_decimal_string(
            f"{label}.max_source_age_seconds",
            value["max_source_age_seconds"],
        ),
        authority_score=_require_public_decimal_string(
            f"{label}.authority_score",
            value["authority_score"],
        ),
        trace_coverage_ratio=_require_public_decimal_string(
            f"{label}.trace_coverage_ratio",
            value["trace_coverage_ratio"],
        ),
        freshness_score=_require_public_decimal_string(
            f"{label}.freshness_score",
            value["freshness_score"],
        ),
        contradiction_ratio=_require_public_decimal_string(
            f"{label}.contradiction_ratio",
            value["contradiction_ratio"],
        ),
        unresolved_claim_ratio=_require_public_decimal_string(
            f"{label}.unresolved_claim_ratio",
            value["unresolved_claim_ratio"],
        ),
        claim_consistency_score=_require_public_decimal_string(
            f"{label}.claim_consistency_score",
            value["claim_consistency_score"],
        ),
        claim_traceability_score=_require_public_decimal_string(
            f"{label}.claim_traceability_score",
            value["claim_traceability_score"],
        ),
        claim_traceability_risk_score=_require_public_decimal_string(
            f"{label}.claim_traceability_risk_score",
            value["claim_traceability_risk_score"],
        ),
        status=_require_public_status(f"{label}.status", value["status"]),
        reason_codes=_require_public_reason_codes(
            f"{label}.reason_codes",
            value["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_require_public_flag(f"{label}.paper_only", value["paper_only"]),
        report_only=_require_public_flag(f"{label}.report_only", value["report_only"]),
        readonly=_require_public_flag(f"{label}.readonly", value["readonly"]),
    )


def _reason_code_counts_from_public_payload(
    value: object,
) -> tuple[ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a public JSON list")
    return tuple(
        _reason_code_count_from_public_payload(index, item)
        for index, item in enumerate(value)
    )


def _reason_code_count_from_public_payload(
    index: int,
    value: object,
) -> ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain public JSON objects")
    label = f"reason_code_counts[{index}]"
    _require_public_payload_keys(label, value, REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS)
    return ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount(
        reason_code=_require_public_member(
            f"{label}.reason_code",
            value["reason_code"],
            REPORT_REASON_CODES,
        ),
        count=_require_public_decimal_string(f"{label}.count", value["count"]),
        input_ratio=_require_public_decimal_string(
            f"{label}.input_ratio",
            value["input_ratio"],
        ),
        paper_only=_require_public_flag(f"{label}.paper_only", value["paper_only"]),
        report_only=_require_public_flag(f"{label}.report_only", value["report_only"]),
        readonly=_require_public_flag(f"{label}.readonly", value["readonly"]),
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityEventClaimTraceabilityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityEventClaimTraceabilityInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityEventClaimTraceabilityInput",
            )
        _require_hard_flags("input", row)
        if row.private_event_claim_key in seen:
            raise ValueError("inputs must be unique by private_event_claim_key")
        seen.add(row.private_event_claim_key)
    return tuple(sorted(rows, key=lambda row: _claim_trace_hash(row.private_event_claim_key)))


def _claim_traceability_rows(
    inputs: tuple[ResearchSourceAuthorityEventClaimTraceabilityInput, ...],
    *,
    config: ResearchSourceAuthorityEventClaimTraceabilityConfig,
) -> tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...]:
    return tuple(
        sorted(
            (_claim_traceability_row(row, config=config) for row in inputs),
            key=_row_sort_key,
        ),
    )


def _claim_traceability_row(
    row: ResearchSourceAuthorityEventClaimTraceabilityInput,
    *,
    config: ResearchSourceAuthorityEventClaimTraceabilityConfig,
) -> ResearchSourceAuthorityEventClaimTraceabilityRow:
    authority_score = _bounded_ratio(
        row.authoritative_source_count,
        row.supporting_source_count,
    )
    trace_coverage_ratio = _bounded_ratio(
        row.traced_source_count,
        row.supporting_source_count,
    )
    freshness_score = _freshness_score(row.max_source_age_seconds, config=config)
    contradiction_ratio = _bounded_ratio(
        row.contradictory_source_count,
        row.supporting_source_count,
    )
    unresolved_claim_ratio = _bounded_ratio(
        row.unresolved_claim_count,
        row.supporting_source_count,
    )
    claim_consistency_score = (
        ONE - max(contradiction_ratio, unresolved_claim_ratio)
    ).quantize(QUANT)
    claim_traceability_score = _claim_traceability_score(
        authority_score=authority_score,
        trace_coverage_ratio=trace_coverage_ratio,
        freshness_score=freshness_score,
        claim_consistency_score=claim_consistency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        authority_score=authority_score,
        trace_coverage_ratio=trace_coverage_ratio,
        contradiction_ratio=contradiction_ratio,
        unresolved_claim_ratio=unresolved_claim_ratio,
        config=config,
    )
    return ResearchSourceAuthorityEventClaimTraceabilityRow(
        claim_trace_hash=_claim_trace_hash(row.private_event_claim_key),
        authority_tier=row.authority_tier,
        claim_lineage_depth=row.claim_lineage_depth,
        supporting_source_count=row.supporting_source_count,
        authoritative_source_count=row.authoritative_source_count,
        traced_source_count=row.traced_source_count,
        stale_source_count=row.stale_source_count,
        contradictory_source_count=row.contradictory_source_count,
        unresolved_claim_count=row.unresolved_claim_count,
        max_source_age_seconds=row.max_source_age_seconds,
        authority_score=authority_score,
        trace_coverage_ratio=trace_coverage_ratio,
        freshness_score=freshness_score,
        contradiction_ratio=contradiction_ratio,
        unresolved_claim_ratio=unresolved_claim_ratio,
        claim_consistency_score=claim_consistency_score,
        claim_traceability_score=claim_traceability_score,
        claim_traceability_risk_score=(ONE - claim_traceability_score).quantize(QUANT),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityEventClaimTraceabilityInput
    | ResearchSourceAuthorityEventClaimTraceabilityRow,
    *,
    authority_score: Decimal,
    trace_coverage_ratio: Decimal,
    contradiction_ratio: Decimal,
    unresolved_claim_ratio: Decimal,
    config: ResearchSourceAuthorityEventClaimTraceabilityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if authority_score < config.min_watch_authority_score:
        reasons.append(LOW_AUTHORITY_BLOCK_REASON)
    elif authority_score < config.min_pass_authority_score:
        reasons.append(LOW_AUTHORITY_WATCH_REASON)
    if trace_coverage_ratio < config.min_watch_trace_coverage_ratio:
        reasons.append(LOW_TRACE_COVERAGE_BLOCK_REASON)
    elif trace_coverage_ratio < config.min_pass_trace_coverage_ratio:
        reasons.append(LOW_TRACE_COVERAGE_WATCH_REASON)
    if row.max_source_age_seconds >= config.source_age_block_seconds:
        reasons.append(STALE_SOURCE_BLOCK_REASON)
    elif row.max_source_age_seconds > config.source_age_watch_seconds:
        reasons.append(STALE_SOURCE_WATCH_REASON)
    if contradiction_ratio > config.max_watch_contradiction_ratio:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_ratio > config.max_pass_contradiction_ratio:
        reasons.append(CONTRADICTION_WATCH_REASON)
    if unresolved_claim_ratio > config.max_watch_unresolved_claim_ratio:
        reasons.append(UNRESOLVED_CLAIM_BLOCK_REASON)
    elif unresolved_claim_ratio > config.max_pass_unresolved_claim_ratio:
        reasons.append(UNRESOLVED_CLAIM_WATCH_REASON)
    if row.claim_lineage_depth > config.max_block_lineage_depth:
        reasons.append(DEEP_LINEAGE_BLOCK_REASON)
    elif row.claim_lineage_depth > config.max_watch_lineage_depth:
        reasons.append(DEEP_LINEAGE_WATCH_REASON)
    if not reasons:
        return (CLEAR_REASON,)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _freshness_score(
    max_source_age_seconds: Decimal,
    *,
    config: ResearchSourceAuthorityEventClaimTraceabilityConfig,
) -> Decimal:
    if max_source_age_seconds <= config.source_age_watch_seconds:
        return ONE
    if max_source_age_seconds >= config.source_age_block_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        span = config.source_age_block_seconds - config.source_age_watch_seconds
        stale_fraction = (max_source_age_seconds - config.source_age_watch_seconds) / span
        return (ONE - stale_fraction).quantize(QUANT)


def _claim_traceability_score(
    *,
    authority_score: Decimal,
    trace_coverage_ratio: Decimal,
    freshness_score: Decimal,
    claim_consistency_score: Decimal,
    config: ResearchSourceAuthorityEventClaimTraceabilityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            authority_score * config.authority_weight
            + trace_coverage_ratio * config.trace_coverage_weight
            + freshness_score * config.freshness_weight
            + claim_consistency_score * config.claim_consistency_weight
        )
        return min(score, ONE).quantize(QUANT)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANT)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (CLEAR_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REPORT_EMPTY_REASON,)
    status_reason = {
        STATUS_PASS: REPORT_PASS_REASON,
        STATUS_WATCH: REPORT_WATCH_REASON,
        STATUS_BLOCK: REPORT_BLOCK_REASON,
    }[_report_status(rows)]
    reasons = [status_reason]
    reason_pairs = (
        (
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
            LOW_AUTHORITY_EXCEPTION_REASON,
        ),
        (
            (LOW_TRACE_COVERAGE_WATCH_REASON, LOW_TRACE_COVERAGE_BLOCK_REASON),
            LOW_TRACE_COVERAGE_EXCEPTION_REASON,
        ),
        (
            (STALE_SOURCE_WATCH_REASON, STALE_SOURCE_BLOCK_REASON),
            STALE_SOURCE_EXCEPTION_REASON,
        ),
        (
            (CONTRADICTION_WATCH_REASON, CONTRADICTION_BLOCK_REASON),
            CONTRADICTION_EXCEPTION_REASON,
        ),
        (
            (UNRESOLVED_CLAIM_WATCH_REASON, UNRESOLVED_CLAIM_BLOCK_REASON),
            UNRESOLVED_CLAIM_EXCEPTION_REASON,
        ),
        (
            (DEEP_LINEAGE_WATCH_REASON, DEEP_LINEAGE_BLOCK_REASON),
            DEEP_LINEAGE_EXCEPTION_REASON,
        ),
    )
    for row_reasons, report_reason in reason_pairs:
        if any(reason in row.reason_codes for row in rows for reason in row_reasons):
            reasons.append(report_reason)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...],
) -> tuple[ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    row_count = _count(len(rows))
    return tuple(
        ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            input_ratio=_bounded_ratio(_count(counts[reason_code]), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in counts
    )


def _row_sort_key(
    row: ResearchSourceAuthorityEventClaimTraceabilityRow,
) -> tuple[Decimal, str]:
    return (-row.claim_traceability_risk_score, row.claim_trace_hash)


def _claim_trace_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _status_count(
    rows: tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / _count(len(values))).quantize(QUANT)


def _validate_config(config: ResearchSourceAuthorityEventClaimTraceabilityConfig) -> None:
    _require_floor_pair(
        "min_pass_authority_score",
        config.min_pass_authority_score,
        "min_watch_authority_score",
        config.min_watch_authority_score,
    )
    _require_floor_pair(
        "min_pass_trace_coverage_ratio",
        config.min_pass_trace_coverage_ratio,
        "min_watch_trace_coverage_ratio",
        config.min_watch_trace_coverage_ratio,
    )
    _require_ceiling_pair(
        "max_pass_contradiction_ratio",
        config.max_pass_contradiction_ratio,
        config.max_watch_contradiction_ratio,
    )
    _require_ceiling_pair(
        "max_pass_unresolved_claim_ratio",
        config.max_pass_unresolved_claim_ratio,
        config.max_watch_unresolved_claim_ratio,
    )
    if config.source_age_watch_seconds >= config.source_age_block_seconds:
        raise ValueError("source_age_watch_seconds must be less than block seconds")
    if config.max_watch_lineage_depth >= config.max_block_lineage_depth:
        raise ValueError("max_watch_lineage_depth must be less than block depth")
    weight_sum = (
        config.authority_weight
        + config.trace_coverage_weight
        + config.freshness_weight
        + config.claim_consistency_weight
    ).quantize(QUANT)
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")
    for config_field in fields(ResearchSourceAuthorityEventClaimTraceabilityConfig):
        if config_field.name in (
            "config_version",
            "paper_only",
            "report_only",
            "readonly",
        ):
            continue
        if getattr(config, config_field.name) != config_field.default:
            raise ValueError(
                f"{config_field.name} must match config_version",
            )


def _validate_input(row: ResearchSourceAuthorityEventClaimTraceabilityInput) -> None:
    if row.authoritative_source_count > row.supporting_source_count:
        raise ValueError("authoritative_source_count must not exceed supporting_source_count")
    if row.traced_source_count > row.supporting_source_count:
        raise ValueError("traced_source_count must not exceed supporting_source_count")
    if row.stale_source_count > row.supporting_source_count:
        raise ValueError("stale_source_count must not exceed supporting_source_count")
    if (
        row.contradictory_source_count + row.unresolved_claim_count
        > row.supporting_source_count
    ):
        raise ValueError("claim counts must not exceed supporting_source_count")


def _validate_row(row: ResearchSourceAuthorityEventClaimTraceabilityRow) -> None:
    if row.authoritative_source_count > row.supporting_source_count:
        raise ValueError("authoritative_source_count must not exceed supporting_source_count")
    if row.traced_source_count > row.supporting_source_count:
        raise ValueError("traced_source_count must not exceed supporting_source_count")
    if row.stale_source_count > row.supporting_source_count:
        raise ValueError("stale_source_count must not exceed supporting_source_count")
    if (
        row.contradictory_source_count + row.unresolved_claim_count
        > row.supporting_source_count
    ):
        raise ValueError("claim counts must not exceed supporting_source_count")
    config = ResearchSourceAuthorityEventClaimTraceabilityConfig()
    expected_authority_score = _bounded_ratio(
        row.authoritative_source_count,
        row.supporting_source_count,
    )
    expected_trace_coverage_ratio = _bounded_ratio(
        row.traced_source_count,
        row.supporting_source_count,
    )
    expected_contradiction_ratio = _bounded_ratio(
        row.contradictory_source_count,
        row.supporting_source_count,
    )
    expected_unresolved_claim_ratio = _bounded_ratio(
        row.unresolved_claim_count,
        row.supporting_source_count,
    )
    count_derived_ratios = (
        (
            "authority_score",
            row.authority_score,
            expected_authority_score,
        ),
        (
            "trace_coverage_ratio",
            row.trace_coverage_ratio,
            expected_trace_coverage_ratio,
        ),
        (
            "contradiction_ratio",
            row.contradiction_ratio,
            expected_contradiction_ratio,
        ),
        (
            "unresolved_claim_ratio",
            row.unresolved_claim_ratio,
            expected_unresolved_claim_ratio,
        ),
    )
    for field_name, actual, expected in count_derived_ratios:
        if actual != expected:
            raise ValueError(f"{field_name} must match source counts")
    expected_freshness_score = _freshness_score(
        row.max_source_age_seconds,
        config=config,
    )
    if row.freshness_score != expected_freshness_score:
        raise ValueError("freshness_score must match source age")
    expected_claim_consistency_score = (
        ONE - max(expected_contradiction_ratio, expected_unresolved_claim_ratio)
    ).quantize(QUANT)
    if row.claim_consistency_score != expected_claim_consistency_score:
        raise ValueError("claim_consistency_score must match claim ratios")
    expected_claim_traceability_score = _claim_traceability_score(
        authority_score=expected_authority_score,
        trace_coverage_ratio=expected_trace_coverage_ratio,
        freshness_score=expected_freshness_score,
        claim_consistency_score=expected_claim_consistency_score,
        config=config,
    )
    if row.claim_traceability_score != expected_claim_traceability_score:
        raise ValueError("claim_traceability_score must match component scores")
    if row.claim_traceability_risk_score != (
        ONE - expected_claim_traceability_score
    ).quantize(QUANT):
        raise ValueError("claim_traceability_risk_score must match score")
    expected_reason_codes = _row_reason_codes(
        row,
        authority_score=expected_authority_score,
        trace_coverage_ratio=expected_trace_coverage_ratio,
        contradiction_ratio=expected_contradiction_ratio,
        unresolved_claim_ratio=expected_unresolved_claim_ratio,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(expected_reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(report: ResearchSourceAuthorityEventClaimTraceabilityReport) -> None:
    if (
        report.config_version
        != DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must match the supported value")
    for row in report.rows:
        _require_exact_type(
            row,
            ResearchSourceAuthorityEventClaimTraceabilityRow,
            "row",
        )
        _validate_row(row)
        _require_hard_flags("row", row)
    if report.input_row_count != _count(len(report.rows)):
        raise ValueError("input_row_count must match rows")
    for status, field_name in (
        (STATUS_PASS, "pass_count"),
        (STATUS_WATCH, "watch_count"),
        (STATUS_BLOCK, "block_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "low_authority_count",
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        (
            "low_trace_coverage_count",
            (LOW_TRACE_COVERAGE_WATCH_REASON, LOW_TRACE_COVERAGE_BLOCK_REASON),
        ),
        (
            "stale_source_count",
            (STALE_SOURCE_WATCH_REASON, STALE_SOURCE_BLOCK_REASON),
        ),
        (
            "contradictory_claim_count",
            (CONTRADICTION_WATCH_REASON, CONTRADICTION_BLOCK_REASON),
        ),
        (
            "unresolved_claim_count",
            (UNRESOLVED_CLAIM_WATCH_REASON, UNRESOLVED_CLAIM_BLOCK_REASON),
        ),
        (
            "deep_lineage_count",
            (DEEP_LINEAGE_WATCH_REASON, DEEP_LINEAGE_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.mean_trace_coverage_ratio != _mean(
        tuple(row.trace_coverage_ratio for row in report.rows),
    ):
        raise ValueError("mean_trace_coverage_ratio must match rows")
    if report.mean_claim_traceability_score != _mean(
        tuple(row.claim_traceability_score for row in report.rows),
    ):
        raise ValueError("mean_claim_traceability_score must match rows")
    if report.lowest_claim_traceability_score != min(
        (row.claim_traceability_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_claim_traceability_score must match rows")
    if report.highest_claim_traceability_risk_score != max(
        (row.claim_traceability_risk_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_claim_traceability_risk_score must match rows")
    if report.oldest_source_age_seconds != max(
        (row.max_source_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_source_age_seconds must match rows")
    if report.highest_contradiction_ratio != max(
        (row.contradiction_ratio for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic risk sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityEventClaimTraceabilityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityEventClaimTraceabilityRow:
            raise ValueError(
                "rows must contain ResearchSourceAuthorityEventClaimTraceabilityRow",
            )
        _require_hard_flags("row", row)
        if row.claim_trace_hash in seen:
            raise ValueError("rows must be unique by claim_trace_hash")
        seen.add(row.claim_trace_hash)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic risk sort")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityEventClaimTraceabilityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
    expected_order = tuple(reason for reason in ROW_REASON_CODES if reason in seen)
    if tuple(item.reason_code for item in counts) != expected_order:
        raise ValueError("reason_code_counts must be deterministic")
    return counts


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


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
        or value not in RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_STATUSES
    ):
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
        raise ValueError(f"{field_name} must not contain duplicates")
    expected = tuple(reason_code for reason_code in allowed if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_public_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    actual = set(value)
    expected = set(expected_keys)
    missing = tuple(key for key in expected_keys if key not in actual)
    extra = tuple(sorted(actual - expected))
    if missing:
        raise ValueError(f"{label} missing public payload keys: {', '.join(missing)}")
    if extra:
        raise ValueError(f"{label} has unexpected public payload keys: {', '.join(extra)}")


def _require_public_config_version(value: object) -> str:
    _require_public_string("config_version", value)
    if value != DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVENT_CLAIM_TRACEABILITY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must match the supported value")
    return value


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a public datetime string") from exc
    utc_value = _as_utc(field_name, parsed)
    if value != utc_value.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return utc_value


def _require_public_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a public decimal string") from exc
    decimal_value = _require_nonnegative_decimal(field_name, decimal_value)
    if value.startswith("-") or format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must be a canonical public decimal string")
    return decimal_value


def _require_public_status(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    return value


def _require_public_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    _require_member(field_name, value, allowed)
    return value


def _require_public_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public JSON list")
    return _normalize_reason_codes(field_name, value, allowed)


def _require_public_digest_string(field_name: str, value: object) -> str:
    _require_sha256(field_name, value)
    return value


def _require_public_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a stripped nonempty string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_private_claim_key(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a stripped nonempty string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_exact_type(value: object, expected: type[object], label: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value <= watch_value:
        raise ValueError(f"{pass_name} must exceed {watch_name}")


def _require_ceiling_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_value: Decimal,
) -> None:
    if pass_value >= watch_value:
        raise ValueError(f"{pass_name} must be less than watch threshold")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")


def _require_or_set_digest(
    report: ResearchSourceAuthorityEventClaimTraceabilityReport,
) -> None:
    if report.derived_validation_digest == "":
        object.__setattr__(
            report,
            "derived_validation_digest",
            _report_digest_from_public_payload(report),
        )
        return
    validate_research_source_authority_event_claim_traceability_report_digest(report)


def _report_digest_from_public_payload(
    report: ResearchSourceAuthorityEventClaimTraceabilityReport,
) -> str:
    payload = _json_ready(report, include_digest=False)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    _reject_public_payload(unsigned)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    if digest != sha256(encoded).hexdigest():
        raise ValueError("derived_validation_digest must match public payload")


def _json_ready(value: object, *, include_digest: bool = True) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), include_digest=include_digest)
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if key == "derived_validation_digest" and not include_digest:
                continue
            ready[key] = _json_ready(item, include_digest=include_digest)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if type(value) is Decimal:
        return format(value.quantize(QUANT), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


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
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must not expose numeric primitives")
    if type(value) is datetime:
        raise ValueError("public payload must not expose datetime objects")
    raise ValueError("public payload contains unsupported value")
