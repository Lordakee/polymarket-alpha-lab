"""Pure report-only authority and freshness review priority module."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-source-authority-freshness-priority-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_authority_freshness_priority_empty"
CLEAR_REASON = "research_source_authority_freshness_priority_clear"
LOW_AUTHORITY_WATCH_REASON = "research_source_authority_freshness_priority_low_authority_watch"
LOW_AUTHORITY_BLOCK_REASON = "research_source_authority_freshness_priority_low_authority_block"
STALE_VERIFICATION_WATCH_REASON = (
    "research_source_authority_freshness_priority_stale_verification_watch"
)
STALE_VERIFICATION_BLOCK_REASON = (
    "research_source_authority_freshness_priority_stale_verification_block"
)
THIN_CORROBORATION_WATCH_REASON = (
    "research_source_authority_freshness_priority_thin_corroboration_watch"
)
THIN_CORROBORATION_BLOCK_REASON = (
    "research_source_authority_freshness_priority_thin_corroboration_block"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "research_source_authority_freshness_priority_contradiction_pressure_watch"
)
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "research_source_authority_freshness_priority_contradiction_pressure_block"
)
LOW_EXTRACTION_CONFIDENCE_WATCH_REASON = (
    "research_source_authority_freshness_priority_low_extraction_confidence_watch"
)
LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON = (
    "research_source_authority_freshness_priority_low_extraction_confidence_block"
)
MISSING_FIELDS_WATCH_REASON = (
    "research_source_authority_freshness_priority_missing_fields_watch"
)
MISSING_FIELDS_BLOCK_REASON = (
    "research_source_authority_freshness_priority_missing_fields_block"
)
DEADLINE_PROXIMITY_WATCH_REASON = (
    "research_source_authority_freshness_priority_deadline_proximity_watch"
)
DEADLINE_PROXIMITY_BLOCK_REASON = (
    "research_source_authority_freshness_priority_deadline_proximity_block"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_AUTHORITY_BLOCK_REASON,
    STALE_VERIFICATION_BLOCK_REASON,
    THIN_CORROBORATION_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
    MISSING_FIELDS_BLOCK_REASON,
    DEADLINE_PROXIMITY_BLOCK_REASON,
    LOW_AUTHORITY_WATCH_REASON,
    STALE_VERIFICATION_WATCH_REASON,
    THIN_CORROBORATION_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
    MISSING_FIELDS_WATCH_REASON,
    DEADLINE_PROXIMITY_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

AUTHORITY_WEIGHT = Decimal("0.200000")
FRESHNESS_WEIGHT = Decimal("0.175000")
CORROBORATION_WEIGHT = Decimal("0.150000")
CONTRADICTION_WEIGHT = Decimal("0.175000")
EXTRACTION_WEIGHT = Decimal("0.125000")
MISSING_FIELDS_WEIGHT = Decimal("0.100000")
DEADLINE_WEIGHT = Decimal("0.075000")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "url",
    "source_text",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
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
    "market_",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_url",
    "source_text",
    " table",
    "table_",
    "dsn",
    "token",
    "wallet",
    "order",
    "trade",
    "live_",
    "live_surface",
    "_slug",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_REPORT_CONFIG_VERSION
    )
    authority_watch_floor: Decimal = Decimal("0.700000")
    authority_block_floor: Decimal = Decimal("0.500000")
    freshness_watch_age_seconds: Decimal = Decimal("1800.000000")
    freshness_block_age_seconds: Decimal = Decimal("3600.000000")
    corroboration_watch_depth: Decimal = Decimal("2.000000")
    corroboration_block_depth: Decimal = Decimal("0.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.300000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    extraction_confidence_watch_floor: Decimal = Decimal("0.800000")
    extraction_confidence_block_floor: Decimal = Decimal("0.600000")
    missing_fields_watch_count: Decimal = Decimal("1.000000")
    missing_fields_block_count: Decimal = Decimal("2.000000")
    deadline_watch_seconds_remaining: Decimal = Decimal("1800.000000")
    deadline_block_seconds_remaining: Decimal = Decimal("600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessPriorityConfig:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessPriorityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessPriorityConfig:
            raise ValueError(
                "config must be exactly ResearchSourceAuthorityFreshnessPriorityConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "authority_watch_floor",
            "authority_block_floor",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "extraction_confidence_watch_floor",
            "extraction_confidence_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
            "corroboration_watch_depth",
            "missing_fields_watch_count",
            "missing_fields_block_count",
            "deadline_watch_seconds_remaining",
            "deadline_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_block_depth",
            _require_nonnegative_decimal(
                "corroboration_block_depth",
                self.corroboration_block_depth,
            ),
        )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessPriorityInput:
    review_bucket: str
    source_authority_score: Decimal
    latest_verification_age_seconds: Decimal
    corroboration_depth_count: Decimal
    contradiction_pressure_score: Decimal
    extraction_confidence_score: Decimal
    missing_required_field_count: Decimal
    required_field_count: Decimal
    deadline_seconds_remaining: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessPriorityInput:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessPriorityInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessPriorityInput:
            raise ValueError(
                "input must be exactly ResearchSourceAuthorityFreshnessPriorityInput",
            )
        object.__setattr__(
            self,
            "review_bucket",
            _require_public_bucket("review_bucket", self.review_bucket),
        )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure_score",
            "extraction_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_verification_age_seconds",
            "deadline_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "corroboration_depth_count",
            "missing_required_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_field_count",
            _require_positive_whole_decimal("required_field_count", self.required_field_count),
        )
        if self.missing_required_field_count > self.required_field_count:
            raise ValueError("missing_required_field_count must not exceed required_field_count")
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessPriorityRow:
    review_bucket: str
    source_authority_score: Decimal
    authority_band: str
    latest_verification_age_seconds: Decimal
    freshness_band: str
    corroboration_depth_count: Decimal
    corroboration_depth_score: Decimal
    contradiction_pressure_score: Decimal
    extraction_confidence_score: Decimal
    missing_required_field_count: Decimal
    required_field_count: Decimal
    field_completeness_score: Decimal
    deadline_seconds_remaining: Decimal
    deadline_pressure_score: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessPriorityRow:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessPriorityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessPriorityRow:
            raise ValueError("row must be exactly ResearchSourceAuthorityFreshnessPriorityRow")
        object.__setattr__(
            self,
            "review_bucket",
            _require_public_bucket("review_bucket", self.review_bucket),
        )
        for field_name in (
            "source_authority_score",
            "corroboration_depth_score",
            "contradiction_pressure_score",
            "extraction_confidence_score",
            "field_completeness_score",
            "deadline_pressure_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_verification_age_seconds",
            "deadline_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "corroboration_depth_count",
            "missing_required_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_field_count",
            _require_positive_whole_decimal("required_field_count", self.required_field_count),
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
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessPriorityReport:
    generated_at: datetime
    config_version: str
    review_item_count: Decimal
    pass_review_item_count: Decimal
    watch_review_item_count: Decimal
    block_review_item_count: Decimal
    low_authority_count: Decimal
    stale_verification_count: Decimal
    thin_corroboration_count: Decimal
    contradiction_pressure_count: Decimal
    low_extraction_confidence_count: Decimal
    missing_field_count: Decimal
    deadline_proximity_count: Decimal
    highest_priority_score: Decimal
    oldest_latest_verification_age_seconds: Decimal
    lowest_source_authority_score: Decimal
    lowest_extraction_confidence_score: Decimal
    highest_contradiction_pressure_score: Decimal
    nearest_deadline_seconds_remaining: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAuthorityFreshnessPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityFreshnessPriorityReport:
            raise TypeError(
                "ResearchSourceAuthorityFreshnessPriorityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityFreshnessPriorityReport:
            raise ValueError(
                "report must be exactly ResearchSourceAuthorityFreshnessPriorityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "review_item_count",
            "pass_review_item_count",
            "watch_review_item_count",
            "block_review_item_count",
            "low_authority_count",
            "stale_verification_count",
            "thin_corroboration_count",
            "contradiction_pressure_count",
            "low_extraction_confidence_count",
            "missing_field_count",
            "deadline_proximity_count",
            "oldest_latest_verification_age_seconds",
            "nearest_deadline_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_priority_score",
            "lowest_source_authority_score",
            "lowest_extraction_confidence_score",
            "highest_contradiction_pressure_score",
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)
        _require_or_set_digest(self)


def build_research_source_authority_freshness_priority_report(
    inputs: list[ResearchSourceAuthorityFreshnessPriorityInput]
    | tuple[ResearchSourceAuthorityFreshnessPriorityInput, ...],
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityFreshnessPriorityReport:
    if type(config) is not ResearchSourceAuthorityFreshnessPriorityConfig:
        raise ValueError("config must be a ResearchSourceAuthorityFreshnessPriorityConfig")
    require_paper_only_flags("config", config)
    rows = _priority_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityFreshnessPriorityReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        review_item_count=_count(len(rows)),
        pass_review_item_count=_status_count(rows, "pass"),
        watch_review_item_count=_status_count(rows, "watch"),
        block_review_item_count=_status_count(rows, "block"),
        low_authority_count=_reason_count(
            rows,
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        stale_verification_count=_reason_count(
            rows,
            (STALE_VERIFICATION_WATCH_REASON, STALE_VERIFICATION_BLOCK_REASON),
        ),
        thin_corroboration_count=_reason_count(
            rows,
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        low_extraction_confidence_count=_reason_count(
            rows,
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        missing_field_count=_reason_count(
            rows,
            (MISSING_FIELDS_WATCH_REASON, MISSING_FIELDS_BLOCK_REASON),
        ),
        deadline_proximity_count=_reason_count(
            rows,
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
        highest_priority_score=max(
            (row.priority_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_latest_verification_age_seconds=max(
            (row.latest_verification_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_source_authority_score=min(
            (row.source_authority_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_extraction_confidence_score=min(
            (row.extraction_confidence_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_pressure_score=max(
            (row.contradiction_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        nearest_deadline_seconds_remaining=min(
            (row.deadline_seconds_remaining for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_authority_freshness_priority_report_payload(
    report: ResearchSourceAuthorityFreshnessPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityFreshnessPriorityReport:
        raise ValueError("report must be a ResearchSourceAuthorityFreshnessPriorityReport")
    validate_research_source_authority_freshness_priority_report_digest(report)
    require_paper_only_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def research_source_authority_freshness_priority_report_digest(
    report: ResearchSourceAuthorityFreshnessPriorityReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityFreshnessPriorityReport:
        raise ValueError("report must be a ResearchSourceAuthorityFreshnessPriorityReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_freshness_priority_report_digest(
    report: ResearchSourceAuthorityFreshnessPriorityReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityFreshnessPriorityReport:
        raise ValueError("report must be a ResearchSourceAuthorityFreshnessPriorityReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityFreshnessPriorityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityFreshnessPriorityInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityFreshnessPriorityInput",
            )
        require_paper_only_flags("input", row)
        if row.review_bucket in seen:
            raise ValueError("inputs must be unique by review_bucket")
        seen.add(row.review_bucket)
    return tuple(sorted(rows, key=lambda row: row.review_bucket))


def _priority_rows(
    inputs: tuple[ResearchSourceAuthorityFreshnessPriorityInput, ...],
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> tuple[ResearchSourceAuthorityFreshnessPriorityRow, ...]:
    return tuple(sorted((_priority_row(row, config=config) for row in inputs), key=_row_sort_key))


def _priority_row(
    row: ResearchSourceAuthorityFreshnessPriorityInput,
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> ResearchSourceAuthorityFreshnessPriorityRow:
    reason_codes = _row_reason_codes(row, config=config)
    corroboration_depth_score = _corroboration_depth_score(row, config=config)
    field_completeness_score = _field_completeness_score(row)
    deadline_pressure_score = _deadline_pressure_score(row.deadline_seconds_remaining, config=config)
    return ResearchSourceAuthorityFreshnessPriorityRow(
        review_bucket=row.review_bucket,
        source_authority_score=row.source_authority_score,
        authority_band=_authority_band(row.source_authority_score, config=config),
        latest_verification_age_seconds=row.latest_verification_age_seconds,
        freshness_band=_freshness_band(row.latest_verification_age_seconds, config=config),
        corroboration_depth_count=row.corroboration_depth_count,
        corroboration_depth_score=corroboration_depth_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        extraction_confidence_score=row.extraction_confidence_score,
        missing_required_field_count=row.missing_required_field_count,
        required_field_count=row.required_field_count,
        field_completeness_score=field_completeness_score,
        deadline_seconds_remaining=row.deadline_seconds_remaining,
        deadline_pressure_score=deadline_pressure_score,
        priority_score=_priority_score(
            row,
            corroboration_depth_score=corroboration_depth_score,
            field_completeness_score=field_completeness_score,
            deadline_pressure_score=deadline_pressure_score,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityFreshnessPriorityInput,
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.source_authority_score <= config.authority_block_floor:
        reasons.append(LOW_AUTHORITY_BLOCK_REASON)
    elif row.source_authority_score < config.authority_watch_floor:
        reasons.append(LOW_AUTHORITY_WATCH_REASON)
    if row.latest_verification_age_seconds >= config.freshness_block_age_seconds:
        reasons.append(STALE_VERIFICATION_BLOCK_REASON)
    elif row.latest_verification_age_seconds > config.freshness_watch_age_seconds:
        reasons.append(STALE_VERIFICATION_WATCH_REASON)
    if row.corroboration_depth_count <= config.corroboration_block_depth:
        reasons.append(THIN_CORROBORATION_BLOCK_REASON)
    elif row.corroboration_depth_count < config.corroboration_watch_depth:
        reasons.append(THIN_CORROBORATION_WATCH_REASON)
    if row.contradiction_pressure_score >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if row.extraction_confidence_score <= config.extraction_confidence_block_floor:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON)
    elif row.extraction_confidence_score < config.extraction_confidence_watch_floor:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_WATCH_REASON)
    if row.missing_required_field_count >= config.missing_fields_block_count:
        reasons.append(MISSING_FIELDS_BLOCK_REASON)
    elif row.missing_required_field_count >= config.missing_fields_watch_count:
        reasons.append(MISSING_FIELDS_WATCH_REASON)
    if row.deadline_seconds_remaining <= config.deadline_block_seconds_remaining:
        reasons.append(DEADLINE_PROXIMITY_BLOCK_REASON)
    elif row.deadline_seconds_remaining < config.deadline_watch_seconds_remaining:
        reasons.append(DEADLINE_PROXIMITY_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _priority_score(
    row: ResearchSourceAuthorityFreshnessPriorityInput,
    *,
    corroboration_depth_score: Decimal,
    field_completeness_score: Decimal,
    deadline_pressure_score: Decimal,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = ONE - row.source_authority_score
        freshness_pressure = min(
            row.latest_verification_age_seconds / config.freshness_block_age_seconds,
            ONE,
        )
        corroboration_gap = ONE - corroboration_depth_score
        extraction_gap = ONE - row.extraction_confidence_score
        field_gap = ONE - field_completeness_score
        score = (
            authority_gap * AUTHORITY_WEIGHT
            + freshness_pressure * FRESHNESS_WEIGHT
            + corroboration_gap * CORROBORATION_WEIGHT
            + row.contradiction_pressure_score * CONTRADICTION_WEIGHT
            + extraction_gap * EXTRACTION_WEIGHT
            + field_gap * MISSING_FIELDS_WEIGHT
            + deadline_pressure_score * DEADLINE_WEIGHT
        )
        return min(score, ONE).quantize(QUANT)


def _corroboration_depth_score(
    row: ResearchSourceAuthorityFreshnessPriorityInput,
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> Decimal:
    return min(_ratio(row.corroboration_depth_count, config.corroboration_watch_depth), ONE)


def _field_completeness_score(row: ResearchSourceAuthorityFreshnessPriorityInput) -> Decimal:
    return (ONE - _ratio(row.missing_required_field_count, row.required_field_count)).quantize(QUANT)


def _deadline_pressure_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        open_fraction = min(value / config.deadline_watch_seconds_remaining, ONE)
        return (ONE - open_fraction).quantize(QUANT)


def _authority_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> str:
    if value >= config.authority_watch_floor:
        return "high"
    if value <= config.authority_block_floor:
        return "low"
    return "medium"


def _freshness_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessPriorityConfig,
) -> str:
    if value <= config.freshness_watch_age_seconds:
        return "fresh"
    if value < config.freshness_block_age_seconds:
        return "aging"
    return "stale"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceAuthorityFreshnessPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityFreshnessPriorityRow, ...],
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


def _row_sort_key(row: ResearchSourceAuthorityFreshnessPriorityRow) -> tuple[Decimal, str]:
    return (-row.priority_score, row.review_bucket)


def _status_count(
    rows: tuple[ResearchSourceAuthorityFreshnessPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityFreshnessPriorityRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourceAuthorityFreshnessPriorityConfig) -> None:
    if config.authority_block_floor > config.authority_watch_floor:
        raise ValueError("authority_block_floor must not exceed authority_watch_floor")
    if config.freshness_watch_age_seconds >= config.freshness_block_age_seconds:
        raise ValueError("freshness_watch_age_seconds must be less than freshness_block_age_seconds")
    if config.corroboration_block_depth >= config.corroboration_watch_depth:
        raise ValueError("corroboration_block_depth must be less than corroboration_watch_depth")
    if config.contradiction_watch_pressure > config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must not exceed contradiction_block_pressure",
        )
    if config.extraction_confidence_block_floor > config.extraction_confidence_watch_floor:
        raise ValueError(
            "extraction_confidence_block_floor must not exceed extraction_confidence_watch_floor",
        )
    if config.missing_fields_watch_count > config.missing_fields_block_count:
        raise ValueError("missing_fields_watch_count must not exceed missing_fields_block_count")
    if config.deadline_block_seconds_remaining > config.deadline_watch_seconds_remaining:
        raise ValueError(
            "deadline_block_seconds_remaining must not exceed deadline_watch_seconds_remaining",
        )


def _validate_row(row: ResearchSourceAuthorityFreshnessPriorityRow) -> None:
    if row.missing_required_field_count > row.required_field_count:
        raise ValueError("missing_required_field_count must not exceed required_field_count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")
    if row.field_completeness_score != (
        ONE - _ratio(row.missing_required_field_count, row.required_field_count)
    ).quantize(QUANT):
        raise ValueError("field_completeness_score must match field counts")


def _validate_report(report: ResearchSourceAuthorityFreshnessPriorityReport) -> None:
    if report.review_item_count != _count(len(report.rows)):
        raise ValueError("review_item_count must match rows")
    for status, field_name in (
        ("pass", "pass_review_item_count"),
        ("watch", "watch_review_item_count"),
        ("block", "block_review_item_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        ("low_authority_count", (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON)),
        (
            "stale_verification_count",
            (STALE_VERIFICATION_WATCH_REASON, STALE_VERIFICATION_BLOCK_REASON),
        ),
        (
            "thin_corroboration_count",
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        (
            "low_extraction_confidence_count",
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        ("missing_field_count", (MISSING_FIELDS_WATCH_REASON, MISSING_FIELDS_BLOCK_REASON)),
        (
            "deadline_proximity_count",
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_priority_score != max(
        (row.priority_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_priority_score must match rows")
    if report.oldest_latest_verification_age_seconds != max(
        (row.latest_verification_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_latest_verification_age_seconds must match rows")
    if report.lowest_source_authority_score != min(
        (row.source_authority_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_source_authority_score must match rows")
    if report.lowest_extraction_confidence_score != min(
        (row.extraction_confidence_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_extraction_confidence_score must match rows")
    if report.highest_contradiction_pressure_score != max(
        (row.contradiction_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.nearest_deadline_seconds_remaining != min(
        (row.deadline_seconds_remaining for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("nearest_deadline_seconds_remaining must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityFreshnessPriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityFreshnessPriorityRow:
            raise ValueError("rows must contain ResearchSourceAuthorityFreshnessPriorityRow")
        require_paper_only_flags("row", row)
        if row.review_bucket in seen:
            raise ValueError("rows must be unique by review_bucket")
        seen.add(row.review_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


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


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_positive_decimal("ratio denominator", denominator)
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


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


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_or_set_digest(report: ResearchSourceAuthorityFreshnessPriorityReport) -> None:
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
    report: ResearchSourceAuthorityFreshnessPriorityReport,
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
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("public payload contains unsafe key")
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_STATUSES",
    "ResearchSourceAuthorityFreshnessPriorityConfig",
    "ResearchSourceAuthorityFreshnessPriorityInput",
    "ResearchSourceAuthorityFreshnessPriorityReport",
    "ResearchSourceAuthorityFreshnessPriorityRow",
    "build_research_source_authority_freshness_priority_report",
    "research_source_authority_freshness_priority_report_digest",
    "research_source_authority_freshness_priority_report_payload",
    "validate_research_source_authority_freshness_priority_report_digest",
)
