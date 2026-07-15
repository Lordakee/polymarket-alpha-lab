"""Pure in-memory fallback source coverage gap report for research review."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import re
from typing import Any
import weakref

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_FALLBACK_COVERAGE_GAP_REPORT_CONFIG_VERSION = (
    "research-source-fallback-coverage-gap-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

PASS_REASON = "fallback_coverage_gap_pass"
WATCH_REASON = "fallback_coverage_gap_watch"
BLOCK_REASON = "fallback_coverage_gap_block"
EMPTY_REASON = "no_fallback_coverage_scopes"
MISSING_FALLBACK_REASON = "missing_fallback_source"
STALE_WATCH_REASON = "stale_fallback_watch"
STALE_BLOCK_REASON = "stale_fallback_block"
AUTHORITY_WATCH_REASON = "fallback_authority_watch"
AUTHORITY_BLOCK_REASON = "fallback_authority_block"
CORROBORATION_WATCH_REASON = "corroboration_depth_watch"
CORROBORATION_BLOCK_REASON = "corroboration_depth_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
EXTRACTION_WATCH_REASON = "extraction_confidence_watch"
EXTRACTION_BLOCK_REASON = "extraction_confidence_block"
DEADLINE_WATCH_REASON = "deadline_proximity_watch"
DEADLINE_BLOCK_REASON = "deadline_proximity_block"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
DETAIL_REASON_CODES = (
    AUTHORITY_BLOCK_REASON,
    AUTHORITY_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    CORROBORATION_BLOCK_REASON,
    CORROBORATION_WATCH_REASON,
    DEADLINE_BLOCK_REASON,
    DEADLINE_WATCH_REASON,
    EXTRACTION_BLOCK_REASON,
    EXTRACTION_WATCH_REASON,
    MISSING_FALLBACK_REASON,
    STALE_BLOCK_REASON,
    STALE_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON, PASS_REASON, *DETAIL_REASON_CODES)
ROW_REASON_CODES = (*STATUS_REASON_CODES, *DETAIL_REASON_CODES)
REASON_CODE_SET = frozenset((*REPORT_REASON_CODES, *ROW_REASON_CODES))

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "slug",
    "question",
    "raw_url",
    "raw-url",
    "url",
    "source_text",
    "source-text",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "http://",
    "https://",
    "www.",
)

_PUBLIC_SNAPSHOTS: dict[int, tuple[tuple[str, str], ...]] = {}
_PUBLIC_SNAPSHOT_REFS: dict[int, weakref.ReferenceType[object]] = {}


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_FALLBACK_COVERAGE_GAP_REPORT_CONFIG_VERSION",
    "ResearchSourceFallbackCoverageGapConfig",
    "ResearchSourceFallbackCoverageGapInput",
    "ResearchSourceFallbackCoverageSignal",
    "ResearchSourceFallbackCoverageGapRow",
    "ResearchSourceFallbackCoverageGapReasonCodeCount",
    "ResearchSourceFallbackCoverageGapReport",
    "build_research_source_fallback_coverage_gap_report",
    "research_source_fallback_coverage_gap_report_digest",
    "research_source_fallback_coverage_gap_report_payload",
    "validate_research_source_fallback_coverage_gap_report_payload",
    "validate_research_source_fallback_coverage_gap_report_digest",
)


@dataclass(frozen=True)
class ResearchSourceFallbackCoverageGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_FALLBACK_COVERAGE_GAP_REPORT_CONFIG_VERSION
    )
    max_fallback_age_seconds: Decimal = Decimal("3600.000000")
    block_fallback_age_seconds: Decimal = Decimal("10800.000000")
    fallback_authority_watch_threshold: Decimal = Decimal("0.700000")
    fallback_authority_block_threshold: Decimal = Decimal("0.400000")
    minimum_corroboration_depth: Decimal = Decimal("2.000000")
    contradiction_watch_threshold: Decimal = Decimal("0.350000")
    contradiction_block_threshold: Decimal = Decimal("0.700000")
    extraction_confidence_watch_threshold: Decimal = Decimal("0.800000")
    extraction_confidence_block_threshold: Decimal = Decimal("0.500000")
    deadline_watch_seconds: Decimal = Decimal("7200.000000")
    deadline_block_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFallbackCoverageGapConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceFallbackCoverageGapConfig)
        _require_safe_public_string("config_version", self.config_version)
        for field_name in (
            "max_fallback_age_seconds",
            "block_fallback_age_seconds",
            "deadline_watch_seconds",
            "deadline_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fallback_authority_watch_threshold",
            "fallback_authority_block_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "extraction_confidence_watch_threshold",
            "extraction_confidence_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_corroboration_depth",
            _normalize_positive_count(
                "minimum_corroboration_depth",
                self.minimum_corroboration_depth,
            ),
        )
        if self.block_fallback_age_seconds <= self.max_fallback_age_seconds:
            raise ValueError(
                "block_fallback_age_seconds must exceed max_fallback_age_seconds",
            )
        _require_watch_block_floor_pair(
            "fallback_authority_watch_threshold",
            self.fallback_authority_watch_threshold,
            "fallback_authority_block_threshold",
            self.fallback_authority_block_threshold,
        )
        _require_watch_block_floor_pair(
            "extraction_confidence_watch_threshold",
            self.extraction_confidence_watch_threshold,
            "extraction_confidence_block_threshold",
            self.extraction_confidence_block_threshold,
        )
        _require_watch_block_ceiling_pair(
            "contradiction_watch_threshold",
            self.contradiction_watch_threshold,
            "contradiction_block_threshold",
            self.contradiction_block_threshold,
        )
        if self.deadline_watch_seconds <= self.deadline_block_seconds:
            raise ValueError("deadline_watch_seconds must exceed deadline_block_seconds")
        require_paper_only_flags("config", self)
        _reject_unsafe_public_surface("config", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchSourceFallbackCoverageSignal:
    review_scope: str
    primary_source_available: bool
    fallback_available: bool
    fallback_observed_at: datetime | None
    fallback_authority_score: Decimal
    corroboration_depth: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    decision_deadline_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFallbackCoverageSignal does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("signal", self, ResearchSourceFallbackCoverageSignal)
        object.__setattr__(
            self,
            "review_scope",
            _require_safe_public_string("review_scope", self.review_scope),
        )
        for field_name in ("primary_source_available", "fallback_available"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "fallback_observed_at",
            _optional_utc("fallback_observed_at", self.fallback_observed_at),
        )
        object.__setattr__(
            self,
            "decision_deadline_at",
            _optional_utc("decision_deadline_at", self.decision_deadline_at),
        )
        for field_name in (
            "fallback_authority_score",
            "contradiction_pressure",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_depth",
            _normalize_count("corroboration_depth", self.corroboration_depth),
        )
        require_paper_only_flags("signal", self)
        _reject_unsafe_public_surface("signal", self)
        _store_public_snapshot(self)


ResearchSourceFallbackCoverageGapInput = ResearchSourceFallbackCoverageSignal


@dataclass(frozen=True)
class ResearchSourceFallbackCoverageGapRow:
    review_scope: str
    primary_source_available: bool
    fallback_available: bool
    fallback_observed_at: datetime | None
    fallback_age_seconds: Decimal | None
    fallback_authority_score: Decimal
    fallback_freshness_score: Decimal
    corroboration_depth: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    decision_deadline_at: datetime | None
    deadline_seconds_remaining: Decimal | None
    deadline_proximity_score: Decimal
    fallback_readiness_score: Decimal
    coverage_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFallbackCoverageGapRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceFallbackCoverageGapRow)
        object.__setattr__(
            self,
            "review_scope",
            _require_safe_public_string("review_scope", self.review_scope),
        )
        for field_name in ("primary_source_available", "fallback_available"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "fallback_observed_at",
            _optional_utc("fallback_observed_at", self.fallback_observed_at),
        )
        object.__setattr__(
            self,
            "decision_deadline_at",
            _optional_utc("decision_deadline_at", self.decision_deadline_at),
        )
        for field_name in ("fallback_age_seconds", "deadline_seconds_remaining"):
            object.__setattr__(
                self,
                field_name,
                _optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fallback_authority_score",
            "fallback_freshness_score",
            "corroboration_score",
            "contradiction_pressure",
            "extraction_confidence",
            "deadline_proximity_score",
            "fallback_readiness_score",
            "coverage_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_depth",
            _normalize_count("corroboration_depth", self.corroboration_depth),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_surface("row", self)
        _set_or_validate_digest(self, "row")
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchSourceFallbackCoverageGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFallbackCoverageGapReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchSourceFallbackCoverageGapReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        require_paper_only_flags("reason_code_count", self)
        _reject_unsafe_public_surface("reason_code_count", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchSourceFallbackCoverageGapReport:
    generated_at: datetime
    config: ResearchSourceFallbackCoverageGapConfig
    config_version: str
    review_scope_count: Decimal
    primary_source_gap_count: Decimal
    fallback_available_count: Decimal
    fresh_fallback_count: Decimal
    authoritative_fallback_count: Decimal
    corroborated_fallback_count: Decimal
    confident_extraction_count: Decimal
    deadline_pressure_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_coverage_gap_score: Decimal
    lowest_fallback_readiness_score: Decimal
    highest_fallback_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceFallbackCoverageGapReasonCodeCount, ...]
    rows: tuple[ResearchSourceFallbackCoverageGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceFallbackCoverageGapReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceFallbackCoverageGapReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "config", _require_config(self.config))
        _require_safe_public_string("config_version", self.config_version)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "review_scope_count",
            "primary_source_gap_count",
            "fallback_available_count",
            "fresh_fallback_count",
            "authoritative_fallback_count",
            "corroborated_fallback_count",
            "confident_extraction_count",
            "deadline_pressure_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_coverage_gap_score",
            "lowest_fallback_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_fallback_age_seconds",
            _normalize_nonnegative_decimal(
                "highest_fallback_age_seconds",
                self.highest_fallback_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        require_paper_only_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        _set_or_validate_digest(self, "report")
        _store_public_snapshot(self)


_PUBLIC_CONFIG_SCHEMA = tuple(field.name for field in fields(ResearchSourceFallbackCoverageGapConfig))
_PUBLIC_ROW_SCHEMA = tuple(field.name for field in fields(ResearchSourceFallbackCoverageGapRow))
_PUBLIC_REASON_CODE_COUNT_SCHEMA = tuple(
    field.name for field in fields(ResearchSourceFallbackCoverageGapReasonCodeCount)
)
_PUBLIC_REPORT_SCHEMA = tuple(field.name for field in fields(ResearchSourceFallbackCoverageGapReport))


def build_research_source_fallback_coverage_gap_report(
    signals: Iterable[ResearchSourceFallbackCoverageSignal],
    *,
    config: ResearchSourceFallbackCoverageGapConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceFallbackCoverageGapReport:
    normalized_config = (
        ResearchSourceFallbackCoverageGapConfig()
        if config is None
        else _require_config(config)
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signal(
                    signal,
                    config=normalized_config,
                    generated_at=generated_at_utc,
                )
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceFallbackCoverageGapReport(
        generated_at=generated_at_utc,
        config=normalized_config,
        config_version=normalized_config.config_version,
        review_scope_count=_decimal_from_int(len(rows)),
        primary_source_gap_count=_row_condition_count(rows, _row_has_primary_gap),
        fallback_available_count=_row_condition_count(rows, _row_has_fallback_available),
        fresh_fallback_count=_row_condition_count(rows, _row_has_fresh_fallback),
        authoritative_fallback_count=_row_condition_count(
            rows,
            _row_has_authoritative_fallback,
        ),
        corroborated_fallback_count=_row_condition_count(
            rows,
            _row_has_corroborated_fallback,
        ),
        confident_extraction_count=_row_condition_count(
            rows,
            _row_has_confident_extraction,
        ),
        deadline_pressure_count=_row_condition_count(rows, _row_has_deadline_pressure),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        max_coverage_gap_score=max(
            (row.coverage_gap_score for row in rows),
            default=ZERO,
        ),
        lowest_fallback_readiness_score=min(
            (row.fallback_readiness_score for row in rows),
            default=ZERO,
        ),
        highest_fallback_age_seconds=max(
            (
                row.fallback_age_seconds
                for row in rows
                if row.fallback_age_seconds is not None
            ),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(_report_reason_codes(rows), rows),
        rows=rows,
    )


def research_source_fallback_coverage_gap_report_payload(
    report: ResearchSourceFallbackCoverageGapReport | dict[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchSourceFallbackCoverageGapReport:
        _require_untampered_report(report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        validate_research_source_fallback_coverage_gap_report_payload(payload)
        return _freeze_json_object(payload)
    if type(report) is dict:
        validate_research_source_fallback_coverage_gap_report_payload(report)
        return _freeze_json_object(report)
    raise ValueError("report must be an exact report or dict payload")


def research_source_fallback_coverage_gap_report_digest(
    report: ResearchSourceFallbackCoverageGapReport,
) -> str:
    _require_exact_type("report", report, ResearchSourceFallbackCoverageGapReport)
    _require_untampered_report(report)
    return _derived_validation_digest(report, "report")


def validate_research_source_fallback_coverage_gap_report_digest(
    report: ResearchSourceFallbackCoverageGapReport,
) -> bool:
    _require_exact_type("report", report, ResearchSourceFallbackCoverageGapReport)
    _require_untampered_report(report)
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    expected = research_source_fallback_coverage_gap_report_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match payload")
    return True


def validate_research_source_fallback_coverage_gap_report_payload(
    payload: Mapping[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be an exact dict")
    _require_public_schema("payload", payload, _PUBLIC_REPORT_SCHEMA)
    _require_public_schema("payload.config", payload["config"], _PUBLIC_CONFIG_SCHEMA)
    for index, value in enumerate(payload["rows"]):
        _require_public_schema(f"payload.rows[{index}]", value, _PUBLIC_ROW_SCHEMA)
    for index, value in enumerate(payload["reason_code_counts"]):
        _require_public_schema(
            f"payload.reason_code_counts[{index}]",
            value,
            _PUBLIC_REASON_CODE_COUNT_SCHEMA,
        )
    _reject_unsafe_public_surface("payload", payload)
    report = _report_from_public_payload(payload)
    if json_ready_no_floats(report) != payload:
        raise ValueError("payload must use canonical public values")


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceFallbackCoverageGapReport:
    config = _config_from_public_payload(payload["config"])
    rows = tuple(_row_from_public_payload(value) for value in payload["rows"])
    counts = tuple(
        _reason_code_count_from_public_payload(value)
        for value in payload["reason_code_counts"]
    )
    return ResearchSourceFallbackCoverageGapReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config=config,
        config_version=_public_string("config_version", payload["config_version"]),
        review_scope_count=_public_decimal("review_scope_count", payload["review_scope_count"]),
        primary_source_gap_count=_public_decimal(
            "primary_source_gap_count",
            payload["primary_source_gap_count"],
        ),
        fallback_available_count=_public_decimal(
            "fallback_available_count",
            payload["fallback_available_count"],
        ),
        fresh_fallback_count=_public_decimal(
            "fresh_fallback_count",
            payload["fresh_fallback_count"],
        ),
        authoritative_fallback_count=_public_decimal(
            "authoritative_fallback_count",
            payload["authoritative_fallback_count"],
        ),
        corroborated_fallback_count=_public_decimal(
            "corroborated_fallback_count",
            payload["corroborated_fallback_count"],
        ),
        confident_extraction_count=_public_decimal(
            "confident_extraction_count",
            payload["confident_extraction_count"],
        ),
        deadline_pressure_count=_public_decimal(
            "deadline_pressure_count",
            payload["deadline_pressure_count"],
        ),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        max_coverage_gap_score=_public_decimal(
            "max_coverage_gap_score",
            payload["max_coverage_gap_score"],
        ),
        lowest_fallback_readiness_score=_public_decimal(
            "lowest_fallback_readiness_score",
            payload["lowest_fallback_readiness_score"],
        ),
        highest_fallback_age_seconds=_public_decimal(
            "highest_fallback_age_seconds",
            payload["highest_fallback_age_seconds"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_strings("reason_codes", payload["reason_codes"]),
        reason_code_counts=counts,
        rows=rows,
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _config_from_public_payload(value: object) -> ResearchSourceFallbackCoverageGapConfig:
    if type(value) is not dict:
        raise ValueError("payload.config must be an exact dict")
    return ResearchSourceFallbackCoverageGapConfig(
        config_version=_public_string("config_version", value["config_version"]),
        max_fallback_age_seconds=_public_decimal(
            "max_fallback_age_seconds",
            value["max_fallback_age_seconds"],
        ),
        block_fallback_age_seconds=_public_decimal(
            "block_fallback_age_seconds",
            value["block_fallback_age_seconds"],
        ),
        fallback_authority_watch_threshold=_public_decimal(
            "fallback_authority_watch_threshold",
            value["fallback_authority_watch_threshold"],
        ),
        fallback_authority_block_threshold=_public_decimal(
            "fallback_authority_block_threshold",
            value["fallback_authority_block_threshold"],
        ),
        minimum_corroboration_depth=_public_decimal(
            "minimum_corroboration_depth",
            value["minimum_corroboration_depth"],
        ),
        contradiction_watch_threshold=_public_decimal(
            "contradiction_watch_threshold",
            value["contradiction_watch_threshold"],
        ),
        contradiction_block_threshold=_public_decimal(
            "contradiction_block_threshold",
            value["contradiction_block_threshold"],
        ),
        extraction_confidence_watch_threshold=_public_decimal(
            "extraction_confidence_watch_threshold",
            value["extraction_confidence_watch_threshold"],
        ),
        extraction_confidence_block_threshold=_public_decimal(
            "extraction_confidence_block_threshold",
            value["extraction_confidence_block_threshold"],
        ),
        deadline_watch_seconds=_public_decimal(
            "deadline_watch_seconds",
            value["deadline_watch_seconds"],
        ),
        deadline_block_seconds=_public_decimal(
            "deadline_block_seconds",
            value["deadline_block_seconds"],
        ),
        paper_only=_public_true("paper_only", value["paper_only"]),
        report_only=_public_true("report_only", value["report_only"]),
        readonly=_public_true("readonly", value["readonly"]),
    )


def _row_from_public_payload(value: object) -> ResearchSourceFallbackCoverageGapRow:
    if type(value) is not dict:
        raise ValueError("payload row must be an exact dict")
    optional_datetime = lambda name: (
        None if value[name] is None else _public_datetime(name, value[name])
    )
    optional_decimal = lambda name: (
        None if value[name] is None else _public_decimal(name, value[name])
    )
    return ResearchSourceFallbackCoverageGapRow(
        review_scope=_public_string("review_scope", value["review_scope"]),
        primary_source_available=_public_bool(
            "primary_source_available",
            value["primary_source_available"],
        ),
        fallback_available=_public_bool("fallback_available", value["fallback_available"]),
        fallback_observed_at=optional_datetime("fallback_observed_at"),
        fallback_age_seconds=optional_decimal("fallback_age_seconds"),
        fallback_authority_score=_public_decimal(
            "fallback_authority_score",
            value["fallback_authority_score"],
        ),
        fallback_freshness_score=_public_decimal(
            "fallback_freshness_score",
            value["fallback_freshness_score"],
        ),
        corroboration_depth=_public_decimal("corroboration_depth", value["corroboration_depth"]),
        corroboration_score=_public_decimal("corroboration_score", value["corroboration_score"]),
        contradiction_pressure=_public_decimal(
            "contradiction_pressure",
            value["contradiction_pressure"],
        ),
        extraction_confidence=_public_decimal(
            "extraction_confidence",
            value["extraction_confidence"],
        ),
        decision_deadline_at=optional_datetime("decision_deadline_at"),
        deadline_seconds_remaining=optional_decimal("deadline_seconds_remaining"),
        deadline_proximity_score=_public_decimal(
            "deadline_proximity_score",
            value["deadline_proximity_score"],
        ),
        fallback_readiness_score=_public_decimal(
            "fallback_readiness_score",
            value["fallback_readiness_score"],
        ),
        coverage_gap_score=_public_decimal("coverage_gap_score", value["coverage_gap_score"]),
        status=_public_string("status", value["status"]),
        reason_codes=_public_strings("reason_codes", value["reason_codes"]),
        derived_validation_digest=_public_string(
            "derived_validation_digest",
            value["derived_validation_digest"],
        ),
        paper_only=_public_true("paper_only", value["paper_only"]),
        report_only=_public_true("report_only", value["report_only"]),
        readonly=_public_true("readonly", value["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceFallbackCoverageGapReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("payload reason_code_count must be an exact dict")
    return ResearchSourceFallbackCoverageGapReasonCodeCount(
        reason_code=_public_string("reason_code", value["reason_code"]),
        count=_public_decimal("count", value["count"]),
        paper_only=_public_true("paper_only", value["paper_only"]),
        report_only=_public_true("report_only", value["report_only"]),
        readonly=_public_true("readonly", value["readonly"]),
    )


def _require_config(
    config: ResearchSourceFallbackCoverageGapConfig,
) -> ResearchSourceFallbackCoverageGapConfig:
    _require_exact_type("config", config, ResearchSourceFallbackCoverageGapConfig)
    _require_untampered_public_dataclass(config, "config")
    require_paper_only_flags("config", config)
    _reject_unsafe_public_surface("config", config)
    return config


def _normalize_signals(
    signals: Iterable[ResearchSourceFallbackCoverageSignal],
) -> tuple[ResearchSourceFallbackCoverageSignal, ...]:
    if isinstance(signals, (str, bytes, dict)):
        raise ValueError("signals must be an iterable of fallback coverage signals")
    normalized = tuple(signals)
    seen_review_scopes: set[str] = set()
    for signal in normalized:
        _require_exact_type("signal", signal, ResearchSourceFallbackCoverageSignal)
        _require_untampered_public_dataclass(signal, "input")
        require_paper_only_flags("signal", signal)
        _reject_unsafe_public_surface("signal", signal)
        if signal.review_scope in seen_review_scopes:
            raise ValueError("review_scope values must be unique")
        seen_review_scopes.add(signal.review_scope)
    return normalized


def _row_from_signal(
    signal: ResearchSourceFallbackCoverageSignal,
    *,
    config: ResearchSourceFallbackCoverageGapConfig,
    generated_at: datetime,
) -> ResearchSourceFallbackCoverageGapRow:
    fallback_age_seconds = _fallback_age_seconds(signal, generated_at)
    deadline_seconds_remaining = _deadline_seconds_remaining(signal, generated_at)
    fallback_freshness_score = _fallback_freshness_score(
        signal,
        fallback_age_seconds=fallback_age_seconds,
        config=config,
    )
    corroboration_score = _corroboration_score(signal, config=config)
    deadline_proximity_score = _deadline_proximity_score(
        deadline_seconds_remaining,
        config=config,
    )
    reason_codes = _row_reason_codes(
        signal,
        fallback_age_seconds=fallback_age_seconds,
        deadline_seconds_remaining=deadline_seconds_remaining,
        config=config,
    )
    status = _status_from_detail_reasons(reason_codes)
    fallback_readiness_score = _fallback_readiness_score(
        signal,
        fallback_freshness_score=fallback_freshness_score,
        corroboration_score=corroboration_score,
    )
    return ResearchSourceFallbackCoverageGapRow(
        review_scope=signal.review_scope,
        primary_source_available=signal.primary_source_available,
        fallback_available=signal.fallback_available,
        fallback_observed_at=signal.fallback_observed_at,
        fallback_age_seconds=fallback_age_seconds,
        fallback_authority_score=signal.fallback_authority_score,
        fallback_freshness_score=fallback_freshness_score,
        corroboration_depth=signal.corroboration_depth,
        corroboration_score=corroboration_score,
        contradiction_pressure=signal.contradiction_pressure,
        extraction_confidence=signal.extraction_confidence,
        decision_deadline_at=signal.decision_deadline_at,
        deadline_seconds_remaining=deadline_seconds_remaining,
        deadline_proximity_score=deadline_proximity_score,
        fallback_readiness_score=fallback_readiness_score,
        coverage_gap_score=_coverage_gap_score(
            signal,
            fallback_readiness_score=fallback_readiness_score,
            deadline_proximity_score=deadline_proximity_score,
        ),
        status=status,
        reason_codes=(_status_reason_for_status(status), *reason_codes),
    )


def _fallback_age_seconds(
    signal: ResearchSourceFallbackCoverageSignal,
    generated_at: datetime,
) -> Decimal | None:
    if signal.fallback_observed_at is None:
        return None
    if signal.fallback_observed_at > generated_at:
        raise ValueError("fallback_observed_at must not be after generated_at")
    return _duration_seconds(signal.fallback_observed_at, generated_at)


def _deadline_seconds_remaining(
    signal: ResearchSourceFallbackCoverageSignal,
    generated_at: datetime,
) -> Decimal | None:
    if signal.decision_deadline_at is None:
        return None
    if signal.decision_deadline_at <= generated_at:
        return ZERO
    return _duration_seconds(generated_at, signal.decision_deadline_at)


def _fallback_freshness_score(
    signal: ResearchSourceFallbackCoverageSignal,
    *,
    fallback_age_seconds: Decimal | None,
    config: ResearchSourceFallbackCoverageGapConfig,
) -> Decimal:
    if signal.primary_source_available:
        return ONE
    if not signal.fallback_available or fallback_age_seconds is None:
        return ZERO
    if fallback_age_seconds <= config.max_fallback_age_seconds:
        return ONE
    if fallback_age_seconds >= config.block_fallback_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _derive_ratio(
            "fallback_freshness_score",
            ONE - (fallback_age_seconds / config.block_fallback_age_seconds),
        )


def _corroboration_score(
    signal: ResearchSourceFallbackCoverageSignal,
    *,
    config: ResearchSourceFallbackCoverageGapConfig,
) -> Decimal:
    if signal.primary_source_available:
        return ONE
    if not signal.fallback_available:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _derive_ratio(
            "corroboration_score",
            min(ONE, signal.corroboration_depth / config.minimum_corroboration_depth),
        )


def _deadline_proximity_score(
    deadline_seconds_remaining: Decimal | None,
    *,
    config: ResearchSourceFallbackCoverageGapConfig,
) -> Decimal:
    if deadline_seconds_remaining is None:
        return ZERO
    if deadline_seconds_remaining <= config.deadline_block_seconds:
        return ONE
    if deadline_seconds_remaining >= config.deadline_watch_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _derive_ratio(
            "deadline_proximity_score",
            (config.deadline_watch_seconds - deadline_seconds_remaining)
            / (config.deadline_watch_seconds - config.deadline_block_seconds),
        )


def _fallback_readiness_score(
    signal: ResearchSourceFallbackCoverageSignal,
    *,
    fallback_freshness_score: Decimal,
    corroboration_score: Decimal,
) -> Decimal:
    if signal.primary_source_available:
        return ONE
    availability_score = ONE if signal.fallback_available else ZERO
    contradiction_resilience_score = ONE - signal.contradiction_pressure
    with localcontext(DECIMAL_CONTEXT):
        return _derive_ratio(
            "fallback_readiness_score",
            (
                availability_score
                + fallback_freshness_score
                + signal.fallback_authority_score
                + corroboration_score
                + contradiction_resilience_score
                + signal.extraction_confidence
            )
            / Decimal("6"),
        )


def _coverage_gap_score(
    signal: ResearchSourceFallbackCoverageSignal,
    *,
    fallback_readiness_score: Decimal,
    deadline_proximity_score: Decimal,
) -> Decimal:
    if signal.primary_source_available:
        return ZERO
    return _derive_ratio(
        "coverage_gap_score",
        max(ONE - fallback_readiness_score, deadline_proximity_score),
    )


def _row_reason_codes(
    signal: ResearchSourceFallbackCoverageSignal,
    *,
    fallback_age_seconds: Decimal | None,
    deadline_seconds_remaining: Decimal | None,
    config: ResearchSourceFallbackCoverageGapConfig,
) -> tuple[str, ...]:
    if signal.primary_source_available:
        return ()

    detail_reasons: list[str] = []
    fallback_missing = not signal.fallback_available or fallback_age_seconds is None
    if fallback_missing:
        detail_reasons.append(MISSING_FALLBACK_REASON)
    elif fallback_age_seconds >= config.block_fallback_age_seconds:
        detail_reasons.append(STALE_BLOCK_REASON)
    elif fallback_age_seconds > config.max_fallback_age_seconds:
        detail_reasons.append(STALE_WATCH_REASON)

    if signal.fallback_authority_score < config.fallback_authority_block_threshold:
        detail_reasons.append(AUTHORITY_BLOCK_REASON)
    elif signal.fallback_authority_score < config.fallback_authority_watch_threshold:
        detail_reasons.append(AUTHORITY_WATCH_REASON)

    if signal.corroboration_depth == ZERO:
        detail_reasons.append(CORROBORATION_BLOCK_REASON)
    elif signal.corroboration_depth < config.minimum_corroboration_depth:
        detail_reasons.append(CORROBORATION_WATCH_REASON)

    if signal.contradiction_pressure >= config.contradiction_block_threshold:
        detail_reasons.append(CONTRADICTION_BLOCK_REASON)
    elif signal.contradiction_pressure >= config.contradiction_watch_threshold:
        detail_reasons.append(CONTRADICTION_WATCH_REASON)

    if signal.extraction_confidence < config.extraction_confidence_block_threshold:
        detail_reasons.append(EXTRACTION_BLOCK_REASON)
    elif signal.extraction_confidence < config.extraction_confidence_watch_threshold:
        detail_reasons.append(EXTRACTION_WATCH_REASON)

    if deadline_seconds_remaining is not None:
        if deadline_seconds_remaining <= config.deadline_block_seconds:
            detail_reasons.append(DEADLINE_BLOCK_REASON)
        elif deadline_seconds_remaining <= config.deadline_watch_seconds:
            detail_reasons.append(DEADLINE_WATCH_REASON)

    return tuple(sorted(detail_reasons))


def _status_from_detail_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(_is_block_detail_reason(reason_code) for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _status_reason_for_status(status: str) -> str:
    if status == STATUS_BLOCK:
        return BLOCK_REASON
    if status == STATUS_WATCH:
        return WATCH_REASON
    if status == STATUS_PASS:
        return PASS_REASON
    raise ValueError("status must be one of: pass, watch, block")


def _is_block_detail_reason(reason_code: str) -> bool:
    return reason_code == MISSING_FALLBACK_REASON or reason_code.endswith("_block")


def _report_status(rows: tuple[ResearchSourceFallbackCoverageGapRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceFallbackCoverageGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    detail_reasons = sorted(
        {
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code not in STATUS_REASON_CODES
        },
    )
    if detail_reasons:
        return tuple(detail_reasons)
    return (PASS_REASON,)


def _row_condition_count(
    rows: tuple[ResearchSourceFallbackCoverageGapRow, ...],
    predicate: Any,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if predicate(row)))


def _row_has_primary_gap(row: ResearchSourceFallbackCoverageGapRow) -> bool:
    return not row.primary_source_available


def _row_has_fallback_available(row: ResearchSourceFallbackCoverageGapRow) -> bool:
    return not row.primary_source_available and row.fallback_available


def _row_has_fresh_fallback(row: ResearchSourceFallbackCoverageGapRow) -> bool:
    return (
        not row.primary_source_available
        and row.fallback_available
        and MISSING_FALLBACK_REASON not in row.reason_codes
        and STALE_BLOCK_REASON not in row.reason_codes
        and STALE_WATCH_REASON not in row.reason_codes
    )


def _row_has_authoritative_fallback(row: ResearchSourceFallbackCoverageGapRow) -> bool:
    return (
        not row.primary_source_available
        and row.fallback_available
        and AUTHORITY_BLOCK_REASON not in row.reason_codes
        and AUTHORITY_WATCH_REASON not in row.reason_codes
    )


def _row_has_corroborated_fallback(row: ResearchSourceFallbackCoverageGapRow) -> bool:
    return (
        not row.primary_source_available
        and row.fallback_available
        and CORROBORATION_BLOCK_REASON not in row.reason_codes
        and CORROBORATION_WATCH_REASON not in row.reason_codes
    )


def _row_has_confident_extraction(row: ResearchSourceFallbackCoverageGapRow) -> bool:
    return (
        not row.primary_source_available
        and row.fallback_available
        and EXTRACTION_BLOCK_REASON not in row.reason_codes
        and EXTRACTION_WATCH_REASON not in row.reason_codes
    )


def _row_has_deadline_pressure(row: ResearchSourceFallbackCoverageGapRow) -> bool:
    return (
        not row.primary_source_available
        and (
            DEADLINE_BLOCK_REASON in row.reason_codes
            or DEADLINE_WATCH_REASON in row.reason_codes
        )
    )


def _status_count(
    rows: tuple[ResearchSourceFallbackCoverageGapRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchSourceFallbackCoverageGapRow, ...],
) -> tuple[ResearchSourceFallbackCoverageGapReasonCodeCount, ...]:
    return tuple(
        ResearchSourceFallbackCoverageGapReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_from_int(
                sum(reason_code in row.reason_codes for row in rows),
            ),
        )
        for reason_code in reason_codes
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceFallbackCoverageGapRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_review_scopes: set[str] = set()
    for row in normalized:
        _require_exact_type("row", row, ResearchSourceFallbackCoverageGapRow)
        _require_untampered_public_dataclass(row, "row")
        require_paper_only_flags("row", row)
        if row.review_scope in seen_review_scopes:
            raise ValueError("rows review_scope values must be unique")
        seen_review_scopes.add(row.review_scope)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _row_sort_key(row: ResearchSourceFallbackCoverageGapRow) -> tuple[int, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.coverage_gap_score.copy_negate(),
        row.review_scope,
    )


def _validate_row_consistency(row: ResearchSourceFallbackCoverageGapRow) -> None:
    expected_status_reason = _status_reason_for_status(row.status)
    if row.reason_codes[0] != expected_status_reason:
        raise ValueError("reason_codes must begin with the matching status reason")
    if row.reason_codes[0] == PASS_REASON and len(row.reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if row.reason_codes[0] != PASS_REASON and len(row.reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    detail_reasons = row.reason_codes[1:]
    if detail_reasons != tuple(sorted(detail_reasons)):
        raise ValueError("reason_codes must use canonical order")
    if row.status != _status_from_detail_reasons(detail_reasons):
        raise ValueError("status must match reason_codes")
    if row.primary_source_available:
        if row.status != STATUS_PASS or row.coverage_gap_score != ZERO:
            raise ValueError("primary source availability must clear fallback gap")
        if row.fallback_readiness_score != ONE:
            raise ValueError("fallback_readiness_score must be one when primary is available")
    if row.fallback_observed_at is None and row.fallback_age_seconds is not None:
        raise ValueError("fallback_age_seconds must match fallback_observed_at")
    if row.fallback_observed_at is not None and row.fallback_age_seconds is None:
        raise ValueError("fallback_age_seconds must match fallback_observed_at")
    if row.decision_deadline_at is None and row.deadline_seconds_remaining is not None:
        raise ValueError("deadline_seconds_remaining must match decision_deadline_at")
    if row.decision_deadline_at is not None and row.deadline_seconds_remaining is None:
        raise ValueError("deadline_seconds_remaining must match decision_deadline_at")


def _validate_report_consistency(report: ResearchSourceFallbackCoverageGapReport) -> None:
    expected_rows = tuple(
        _row_from_signal(
            _signal_from_row(row),
            config=report.config,
            generated_at=report.generated_at,
        )
        for row in report.rows
    )
    for actual_row, expected_row in zip(report.rows, expected_rows, strict=True):
        for field in fields(ResearchSourceFallbackCoverageGapRow):
            if field.name == "derived_validation_digest":
                continue
            if getattr(actual_row, field.name) != getattr(expected_row, field.name):
                raise ValueError(f"{field.name} must be re-derived from observations")
    expected_values = {
        "review_scope_count": _decimal_from_int(len(report.rows)),
        "primary_source_gap_count": _row_condition_count(
            report.rows,
            _row_has_primary_gap,
        ),
        "fallback_available_count": _row_condition_count(
            report.rows,
            _row_has_fallback_available,
        ),
        "fresh_fallback_count": _row_condition_count(report.rows, _row_has_fresh_fallback),
        "authoritative_fallback_count": _row_condition_count(
            report.rows,
            _row_has_authoritative_fallback,
        ),
        "corroborated_fallback_count": _row_condition_count(
            report.rows,
            _row_has_corroborated_fallback,
        ),
        "confident_extraction_count": _row_condition_count(
            report.rows,
            _row_has_confident_extraction,
        ),
        "deadline_pressure_count": _row_condition_count(
            report.rows,
            _row_has_deadline_pressure,
        ),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "max_coverage_gap_score": max(
            (row.coverage_gap_score for row in report.rows),
            default=ZERO,
        ),
        "lowest_fallback_readiness_score": min(
            (row.fallback_readiness_score for row in report.rows),
            default=ZERO,
        ),
        "highest_fallback_age_seconds": max(
            (
                row.fallback_age_seconds
                for row in report.rows
                if row.fallback_age_seconds is not None
            ),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _signal_from_row(
    row: ResearchSourceFallbackCoverageGapRow,
) -> ResearchSourceFallbackCoverageSignal:
    return ResearchSourceFallbackCoverageSignal(
        review_scope=row.review_scope,
        primary_source_available=row.primary_source_available,
        fallback_available=row.fallback_available,
        fallback_observed_at=row.fallback_observed_at,
        fallback_authority_score=row.fallback_authority_score,
        corroboration_depth=row.corroboration_depth,
        contradiction_pressure=row.contradiction_pressure,
        extraction_confidence=row.extraction_confidence,
        decision_deadline_at=row.decision_deadline_at,
    )


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchSourceFallbackCoverageGapReasonCodeCount, ...]:
    if type(values) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(values)
    seen_reason_codes: set[str] = set()
    for value in normalized:
        _require_exact_type(
            "reason_code_count",
            value,
            ResearchSourceFallbackCoverageGapReasonCodeCount,
        )
        _require_untampered_public_dataclass(value, "reason_code_count")
        if value.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts values must be unique")
        seen_reason_codes.add(value.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda value: value.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("row reason_codes must begin with a status reason")
    return reason_codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes("reason_codes", value)
    if any(reason_code in (WATCH_REASON, BLOCK_REASON) for reason_code in reason_codes):
        raise ValueError("report reason_codes must not contain row status reasons")
    return reason_codes


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError(f"{name} values must be unique")
        seen_reason_codes.add(reason_code)
    return reason_codes


def _set_or_validate_digest(value: object, label: str) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(
            value,
            "derived_validation_digest",
            _derived_validation_digest(value, label),
        )
        return
    _require_digest("derived_validation_digest", current_digest)
    if current_digest != _derived_validation_digest(value, label):
        raise ValueError("derived_validation_digest does not match payload")


def _derived_validation_digest(value: object, label: str) -> str:
    ready_value = _json_ready_without_digest(value)
    _reject_unsafe_public_surface(f"{label} digest payload", ready_value)
    canonical_payload = json.dumps(
        ready_value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = json_ready_no_floats(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    started_at_utc = _as_utc("started_at", started_at)
    finished_at_utc = _as_utc("finished_at", finished_at)
    if finished_at_utc < started_at_utc:
        raise ValueError("duration seconds must be nonnegative")
    delta = finished_at_utc - started_at_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
        return _normalize_nonnegative_decimal("duration_seconds", seconds)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _decimal_from_int(value: int) -> Decimal:
    return _normalize_count("count", Decimal(value))


def _normalize_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole-number Decimal")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be greater than zero")
    return normalized


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _derive_ratio(name: str, value: Decimal) -> Decimal:
    normalized = _quantize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be greater than zero")
    return normalized


def _optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(name, value)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not be negative zero")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{name} must not exceed six decimal places")
    return _quantize_nonnegative_decimal(name, value)


def _quantize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not be negative zero")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            normalized = value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{name} could not be normalized") from exc
    return normalized


def _require_watch_block_floor_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value >= watch_value:
        raise ValueError(f"{block_name} must be less than {watch_name}")


def _require_watch_block_ceiling_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of: pass, watch, block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError(f"{name} is not supported")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_safe_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe public identifier")
    if _contains_unsafe_public_surface(value):
        raise ValueError(f"{name} contains unsafe public surface")
    return value


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _contains_unsafe_public_surface(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str and _contains_unsafe_public_surface(value):
        raise ValueError(f"unsafe value in {label}")


def _contains_unsafe_public_surface(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


def _require_public_schema(
    label: str,
    value: object,
    schema: tuple[str, ...],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an exact dict")
    if tuple(value) != schema:
        raise ValueError(f"{label} must use canonical key order and schema")


def _public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    return value


def _public_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")
    return value


def _public_true(name: str, value: object) -> bool:
    if type(value) is not bool or value is not True:
        raise ValueError(f"{name} must be exactly True")
    return True


def _public_strings(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{name} must be a JSON string array")
    return tuple(value)


def _public_decimal(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a canonical Decimal string") from exc
    normalized = _normalize_nonnegative_decimal(name, parsed)
    if normalized.to_eng_string() != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return normalized


def _public_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _store_public_snapshot(value: object) -> None:
    identity = id(value)
    _PUBLIC_SNAPSHOTS[identity] = _public_snapshot(value)

    def _clear_snapshot(_: weakref.ReferenceType[object]) -> None:
        _PUBLIC_SNAPSHOTS.pop(identity, None)
        _PUBLIC_SNAPSHOT_REFS.pop(identity, None)

    _PUBLIC_SNAPSHOT_REFS[identity] = weakref.ref(value, _clear_snapshot)


def _public_snapshot(value: object) -> tuple[tuple[str, str], ...]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("public snapshot requires a dataclass instance")
    return tuple(
        (
            field.name,
            json.dumps(
                json_ready_no_floats(getattr(value, field.name)),
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
        for field in fields(value)
    )


def _require_untampered_public_dataclass(value: object, label: str) -> None:
    expected = _PUBLIC_SNAPSHOTS.get(id(value))
    if type(expected) is not tuple:
        raise ValueError(f"{label} canonical snapshot is missing")
    if _public_snapshot(value) != expected:
        raise ValueError(f"{label} was modified after initialization")


def _require_untampered_report(report: ResearchSourceFallbackCoverageGapReport) -> None:
    _require_exact_type("report", report, ResearchSourceFallbackCoverageGapReport)
    _require_untampered_public_dataclass(report, "report")
    _require_config(report.config)
    for row in report.rows:
        _require_untampered_public_dataclass(row, "row")
    for count in report.reason_code_counts:
        _require_untampered_public_dataclass(count, "reason_code_count")
    require_paper_only_flags("report", report)
    _validate_report_consistency(report)
