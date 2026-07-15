"""Pure report-only reducer for authority and Scrapling recheck priority."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, final

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-source-authority-scrapling-recheck-priority-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_source_authority_scrapling_recheck_priority_empty"
CLEAR_REASON = "research_source_authority_scrapling_recheck_priority_clear"
LOW_AUTHORITY_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_low_authority_watch"
)
LOW_AUTHORITY_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_low_authority_block"
)
STALE_SCRAPLING_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_stale_scrapling_watch"
)
STALE_SCRAPLING_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_stale_scrapling_block"
)
STALE_AUTHORITY_REVISION_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_stale_authority_revision_watch"
)
STALE_AUTHORITY_REVISION_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_stale_authority_revision_block"
)
LOW_EXTRACTION_CONFIDENCE_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_low_extraction_confidence_watch"
)
LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_low_extraction_confidence_block"
)
EXTRACTOR_DISAGREEMENT_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_extractor_disagreement_watch"
)
EXTRACTOR_DISAGREEMENT_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_extractor_disagreement_block"
)
THIN_PRIMARY_COVERAGE_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_thin_primary_coverage_watch"
)
THIN_PRIMARY_COVERAGE_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_thin_primary_coverage_block"
)
UNRESOLVED_CLAIM_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_unresolved_claim_watch"
)
UNRESOLVED_CLAIM_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_unresolved_claim_block"
)
FAILED_ATTEMPT_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_failed_attempt_watch"
)
FAILED_ATTEMPT_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_failed_attempt_block"
)
RESOLUTION_PROXIMITY_WATCH_REASON = (
    "research_source_authority_scrapling_recheck_priority_resolution_proximity_watch"
)
RESOLUTION_PROXIMITY_BLOCK_REASON = (
    "research_source_authority_scrapling_recheck_priority_resolution_proximity_block"
)

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_AUTHORITY_BLOCK_REASON,
    STALE_SCRAPLING_BLOCK_REASON,
    STALE_AUTHORITY_REVISION_BLOCK_REASON,
    LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
    EXTRACTOR_DISAGREEMENT_BLOCK_REASON,
    THIN_PRIMARY_COVERAGE_BLOCK_REASON,
    UNRESOLVED_CLAIM_BLOCK_REASON,
    FAILED_ATTEMPT_BLOCK_REASON,
    RESOLUTION_PROXIMITY_BLOCK_REASON,
    LOW_AUTHORITY_WATCH_REASON,
    STALE_SCRAPLING_WATCH_REASON,
    STALE_AUTHORITY_REVISION_WATCH_REASON,
    LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
    EXTRACTOR_DISAGREEMENT_WATCH_REASON,
    THIN_PRIMARY_COVERAGE_WATCH_REASON,
    UNRESOLVED_CLAIM_WATCH_REASON,
    FAILED_ATTEMPT_WATCH_REASON,
    RESOLUTION_PROXIMITY_WATCH_REASON,
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

AUTHORITY_WEIGHT = Decimal("0.175000")
SCRAPLING_FRESHNESS_WEIGHT = Decimal("0.150000")
AUTHORITY_REVISION_WEIGHT = Decimal("0.125000")
EXTRACTION_CONFIDENCE_WEIGHT = Decimal("0.150000")
EXTRACTOR_DISAGREEMENT_WEIGHT = Decimal("0.125000")
PRIMARY_COVERAGE_WEIGHT = Decimal("0.100000")
UNRESOLVED_CLAIM_WEIGHT = Decimal("0.075000")
FAILED_ATTEMPT_WEIGHT = Decimal("0.050000")
RESOLUTION_PROXIMITY_WEIGHT = Decimal("0.050000")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
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
    "sizing",
    "recommendation",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "candidate-",
    "candidate_id",
    "raw_candidate",
    "market-",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_url",
    "source_text",
    " table",
    "dsn",
    "token",
    "wallet",
    "order",
    "trade",
    "live_surface",
    "private_key",
    "api_key",
    "secret",
    "password",
    "sizing",
    "recommendation",
)


@final
@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingRecheckPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_REPORT_CONFIG_VERSION
    )
    authority_watch_floor: Decimal = Decimal("0.750000")
    authority_block_floor: Decimal = Decimal("0.550000")
    scrapling_freshness_watch_age_seconds: Decimal = Decimal("1800.000000")
    scrapling_freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    authority_revision_watch_age_seconds: Decimal = Decimal("86400.000000")
    authority_revision_block_age_seconds: Decimal = Decimal("172800.000000")
    extraction_confidence_watch_floor: Decimal = Decimal("0.800000")
    extraction_confidence_block_floor: Decimal = Decimal("0.600000")
    extractor_disagreement_watch_pressure: Decimal = Decimal("0.250000")
    extractor_disagreement_block_pressure: Decimal = Decimal("0.500000")
    primary_coverage_watch_floor: Decimal = Decimal("0.750000")
    primary_coverage_block_floor: Decimal = Decimal("0.500000")
    unresolved_claim_watch_count: Decimal = Decimal("1.000000")
    unresolved_claim_block_count: Decimal = Decimal("2.000000")
    failed_attempt_watch_count: Decimal = Decimal("1.000000")
    failed_attempt_block_count: Decimal = Decimal("3.000000")
    resolution_watch_seconds_remaining: Decimal = Decimal("7200.000000")
    resolution_block_seconds_remaining: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityScraplingRecheckPriorityConfig:
            raise TypeError(
                "ResearchSourceAuthorityScraplingRecheckPriorityConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingRecheckPriorityConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceAuthorityScraplingRecheckPriorityConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "authority_watch_floor",
            "authority_block_floor",
            "extraction_confidence_watch_floor",
            "extraction_confidence_block_floor",
            "extractor_disagreement_watch_pressure",
            "extractor_disagreement_block_pressure",
            "primary_coverage_watch_floor",
            "primary_coverage_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scrapling_freshness_watch_age_seconds",
            "scrapling_freshness_block_age_seconds",
            "authority_revision_watch_age_seconds",
            "authority_revision_block_age_seconds",
            "resolution_watch_seconds_remaining",
            "resolution_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_claim_watch_count",
            "unresolved_claim_block_count",
            "failed_attempt_watch_count",
            "failed_attempt_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingRecheckPriorityInput:
    recheck_bucket: str
    source_authority_score: Decimal
    scrapling_latest_success_age_seconds: Decimal
    authority_revision_age_seconds: Decimal
    scrapling_extraction_confidence_score: Decimal
    cross_extractor_disagreement_score: Decimal
    primary_evidence_coverage_ratio: Decimal
    unresolved_claim_count: Decimal
    failed_scrapling_attempt_count: Decimal
    successful_scrapling_attempt_count: Decimal
    resolution_seconds_remaining: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityScraplingRecheckPriorityInput:
            raise TypeError(
                "ResearchSourceAuthorityScraplingRecheckPriorityInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingRecheckPriorityInput:
            raise ValueError(
                "input must be exactly "
                "ResearchSourceAuthorityScraplingRecheckPriorityInput",
            )
        object.__setattr__(
            self,
            "recheck_bucket",
            _require_public_bucket("recheck_bucket", self.recheck_bucket),
        )
        for field_name in (
            "source_authority_score",
            "scrapling_extraction_confidence_score",
            "cross_extractor_disagreement_score",
            "primary_evidence_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scrapling_latest_success_age_seconds",
            "authority_revision_age_seconds",
            "resolution_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_claim_count",
            "failed_scrapling_attempt_count",
            "successful_scrapling_attempt_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@final
@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingRecheckPriorityRow:
    recheck_bucket: str
    source_authority_score: Decimal
    authority_band: str
    scrapling_latest_success_age_seconds: Decimal
    scrapling_freshness_band: str
    authority_revision_age_seconds: Decimal
    authority_revision_band: str
    scrapling_extraction_confidence_score: Decimal
    cross_extractor_disagreement_score: Decimal
    primary_evidence_coverage_ratio: Decimal
    unresolved_claim_count: Decimal
    failed_scrapling_attempt_count: Decimal
    successful_scrapling_attempt_count: Decimal
    failed_attempt_pressure_score: Decimal
    resolution_seconds_remaining: Decimal
    resolution_pressure_score: Decimal
    recheck_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchSourceAuthorityScraplingRecheckPriorityConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityScraplingRecheckPriorityRow:
            raise TypeError(
                "ResearchSourceAuthorityScraplingRecheckPriorityRow does not "
                "support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourceAuthorityScraplingRecheckPriorityConfig | None,
    ) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingRecheckPriorityRow:
            raise ValueError(
                "row must be exactly ResearchSourceAuthorityScraplingRecheckPriorityRow",
            )
        object.__setattr__(
            self,
            "recheck_bucket",
            _require_public_bucket("recheck_bucket", self.recheck_bucket),
        )
        for field_name in (
            "source_authority_score",
            "scrapling_extraction_confidence_score",
            "cross_extractor_disagreement_score",
            "primary_evidence_coverage_ratio",
            "failed_attempt_pressure_score",
            "resolution_pressure_score",
            "recheck_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "scrapling_latest_success_age_seconds",
            "authority_revision_age_seconds",
            "resolution_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_claim_count",
            "failed_scrapling_attempt_count",
            "successful_scrapling_attempt_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_authority_band("authority_band", self.authority_band)
        _require_freshness_band("scrapling_freshness_band", self.scrapling_freshness_band)
        _require_revision_band("authority_revision_band", self.authority_revision_band)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self, config=validation_config or _default_config())
        _require_hard_flags("row", self)


class _ReportValidationConfigCarrier:
    __slots__ = ("_validation_config",)


@final
@dataclass(frozen=True)
class ResearchSourceAuthorityScraplingRecheckPriorityReport(
    _ReportValidationConfigCarrier,
):
    generated_at: datetime
    config_version: str
    recheck_item_count: Decimal
    pass_recheck_item_count: Decimal
    watch_recheck_item_count: Decimal
    block_recheck_item_count: Decimal
    low_authority_count: Decimal
    stale_scrapling_count: Decimal
    stale_authority_revision_count: Decimal
    low_extraction_confidence_count: Decimal
    extractor_disagreement_count: Decimal
    thin_primary_coverage_count: Decimal
    unresolved_claim_count: Decimal
    failed_attempt_pressure_count: Decimal
    resolution_proximity_count: Decimal
    highest_recheck_priority_score: Decimal
    oldest_scrapling_latest_success_age_seconds: Decimal
    oldest_authority_revision_age_seconds: Decimal
    lowest_source_authority_score: Decimal
    lowest_scrapling_extraction_confidence_score: Decimal
    highest_cross_extractor_disagreement_score: Decimal
    lowest_primary_evidence_coverage_ratio: Decimal
    nearest_resolution_seconds_remaining: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAuthorityScraplingRecheckPriorityRow, ...]
    validation_config: InitVar[
        ResearchSourceAuthorityScraplingRecheckPriorityConfig | None
    ] = None
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityScraplingRecheckPriorityReport:
            raise TypeError(
                "ResearchSourceAuthorityScraplingRecheckPriorityReport does not "
                "support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourceAuthorityScraplingRecheckPriorityConfig | None,
    ) -> None:
        if type(self) is not ResearchSourceAuthorityScraplingRecheckPriorityReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceAuthorityScraplingRecheckPriorityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "recheck_item_count",
            "pass_recheck_item_count",
            "watch_recheck_item_count",
            "block_recheck_item_count",
            "low_authority_count",
            "stale_scrapling_count",
            "stale_authority_revision_count",
            "low_extraction_confidence_count",
            "extractor_disagreement_count",
            "thin_primary_coverage_count",
            "unresolved_claim_count",
            "failed_attempt_pressure_count",
            "resolution_proximity_count",
            "oldest_scrapling_latest_success_age_seconds",
            "oldest_authority_revision_age_seconds",
            "nearest_resolution_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_recheck_priority_score",
            "lowest_source_authority_score",
            "lowest_scrapling_extraction_confidence_score",
            "highest_cross_extractor_disagreement_score",
            "lowest_primary_evidence_coverage_ratio",
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
        if validation_config is not None and type(validation_config) is not ResearchSourceAuthorityScraplingRecheckPriorityConfig:
            raise ValueError(
                "validation_config must be exactly "
                "ResearchSourceAuthorityScraplingRecheckPriorityConfig",
            )
        effective_config = validation_config or _default_config()
        _validate_config(effective_config)
        _require_hard_flags("config", effective_config)
        object.__setattr__(self, "_validation_config", effective_config)
        _validate_report(self, config=effective_config)
        _require_hard_flags("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_authority_scrapling_recheck_priority_report_payload(self)


def build_research_source_authority_scrapling_recheck_priority_report(
    inputs: list[ResearchSourceAuthorityScraplingRecheckPriorityInput]
    | tuple[ResearchSourceAuthorityScraplingRecheckPriorityInput, ...],
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityScraplingRecheckPriorityReport:
    if type(config) is not ResearchSourceAuthorityScraplingRecheckPriorityConfig:
        raise ValueError(
            "config must be exactly "
            "ResearchSourceAuthorityScraplingRecheckPriorityConfig",
        )
    _require_hard_flags("config", config)
    _validate_config(config)
    rows = _priority_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityScraplingRecheckPriorityReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        recheck_item_count=_count(len(rows)),
        pass_recheck_item_count=_status_count(rows, "pass"),
        watch_recheck_item_count=_status_count(rows, "watch"),
        block_recheck_item_count=_status_count(rows, "block"),
        low_authority_count=_reason_count(
            rows,
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        stale_scrapling_count=_reason_count(
            rows,
            (STALE_SCRAPLING_WATCH_REASON, STALE_SCRAPLING_BLOCK_REASON),
        ),
        stale_authority_revision_count=_reason_count(
            rows,
            (
                STALE_AUTHORITY_REVISION_WATCH_REASON,
                STALE_AUTHORITY_REVISION_BLOCK_REASON,
            ),
        ),
        low_extraction_confidence_count=_reason_count(
            rows,
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        extractor_disagreement_count=_reason_count(
            rows,
            (EXTRACTOR_DISAGREEMENT_WATCH_REASON, EXTRACTOR_DISAGREEMENT_BLOCK_REASON),
        ),
        thin_primary_coverage_count=_reason_count(
            rows,
            (THIN_PRIMARY_COVERAGE_WATCH_REASON, THIN_PRIMARY_COVERAGE_BLOCK_REASON),
        ),
        unresolved_claim_count=_reason_count(
            rows,
            (UNRESOLVED_CLAIM_WATCH_REASON, UNRESOLVED_CLAIM_BLOCK_REASON),
        ),
        failed_attempt_pressure_count=_reason_count(
            rows,
            (FAILED_ATTEMPT_WATCH_REASON, FAILED_ATTEMPT_BLOCK_REASON),
        ),
        resolution_proximity_count=_reason_count(
            rows,
            (RESOLUTION_PROXIMITY_WATCH_REASON, RESOLUTION_PROXIMITY_BLOCK_REASON),
        ),
        highest_recheck_priority_score=_quantize(max(
            (row.recheck_priority_score for row in rows),
            default=ZERO,
        )),
        oldest_scrapling_latest_success_age_seconds=_quantize(max(
            (row.scrapling_latest_success_age_seconds for row in rows),
            default=ZERO,
        )),
        oldest_authority_revision_age_seconds=_quantize(max(
            (row.authority_revision_age_seconds for row in rows),
            default=ZERO,
        )),
        lowest_source_authority_score=_quantize(min(
            (row.source_authority_score for row in rows),
            default=ZERO,
        )),
        lowest_scrapling_extraction_confidence_score=_quantize(min(
            (row.scrapling_extraction_confidence_score for row in rows),
            default=ZERO,
        )),
        highest_cross_extractor_disagreement_score=_quantize(max(
            (row.cross_extractor_disagreement_score for row in rows),
            default=ZERO,
        )),
        lowest_primary_evidence_coverage_ratio=_quantize(min(
            (row.primary_evidence_coverage_ratio for row in rows),
            default=ZERO,
        )),
        nearest_resolution_seconds_remaining=_quantize(min(
            (row.resolution_seconds_remaining for row in rows),
            default=ZERO,
        )),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        validation_config=config,
    )


def research_source_authority_scrapling_recheck_priority_report_payload(
    report: ResearchSourceAuthorityScraplingRecheckPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityScraplingRecheckPriorityReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityScraplingRecheckPriorityReport",
        )
    _validate_report(report, config=_report_validation_config(report))
    validate_research_source_authority_scrapling_recheck_priority_report_digest(report)
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _validate_public_flags(payload)
    _validate_public_statuses(payload)
    _verify_public_digest(payload)
    return payload


def research_source_authority_scrapling_recheck_priority_report_digest(
    report: ResearchSourceAuthorityScraplingRecheckPriorityReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityScraplingRecheckPriorityReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityScraplingRecheckPriorityReport",
        )
    _validate_report(report, config=_report_validation_config(report))
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_scrapling_recheck_priority_report_digest(
    report: ResearchSourceAuthorityScraplingRecheckPriorityReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityScraplingRecheckPriorityReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityScraplingRecheckPriorityReport",
        )
    _validate_report(report, config=_report_validation_config(report))
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match public payload")


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityScraplingRecheckPriorityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityScraplingRecheckPriorityInput:
            raise ValueError(
                "inputs must contain "
                "ResearchSourceAuthorityScraplingRecheckPriorityInput",
            )
        _require_hard_flags("input", row)
        if row.recheck_bucket in seen:
            raise ValueError("inputs must be unique by recheck_bucket")
        seen.add(row.recheck_bucket)
    return tuple(sorted(rows, key=lambda row: row.recheck_bucket))


def _priority_rows(
    inputs: tuple[ResearchSourceAuthorityScraplingRecheckPriorityInput, ...],
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> tuple[ResearchSourceAuthorityScraplingRecheckPriorityRow, ...]:
    return tuple(sorted((_priority_row(row, config=config) for row in inputs), key=_row_sort_key))


def _priority_row(
    row: ResearchSourceAuthorityScraplingRecheckPriorityInput,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> ResearchSourceAuthorityScraplingRecheckPriorityRow:
    reason_codes = _row_reason_codes(row, config=config)
    failed_attempt_pressure_score = _failed_attempt_pressure_score(
        row.failed_scrapling_attempt_count,
        row.successful_scrapling_attempt_count,
    )
    resolution_pressure_score = _resolution_pressure_score(
        row.resolution_seconds_remaining,
        config=config,
    )
    return ResearchSourceAuthorityScraplingRecheckPriorityRow(
        recheck_bucket=row.recheck_bucket,
        source_authority_score=row.source_authority_score,
        authority_band=_authority_band(row.source_authority_score, config=config),
        scrapling_latest_success_age_seconds=row.scrapling_latest_success_age_seconds,
        scrapling_freshness_band=_scrapling_freshness_band(
            row.scrapling_latest_success_age_seconds,
            config=config,
        ),
        authority_revision_age_seconds=row.authority_revision_age_seconds,
        authority_revision_band=_authority_revision_band(
            row.authority_revision_age_seconds,
            config=config,
        ),
        scrapling_extraction_confidence_score=row.scrapling_extraction_confidence_score,
        cross_extractor_disagreement_score=row.cross_extractor_disagreement_score,
        primary_evidence_coverage_ratio=row.primary_evidence_coverage_ratio,
        unresolved_claim_count=row.unresolved_claim_count,
        failed_scrapling_attempt_count=row.failed_scrapling_attempt_count,
        successful_scrapling_attempt_count=row.successful_scrapling_attempt_count,
        failed_attempt_pressure_score=failed_attempt_pressure_score,
        resolution_seconds_remaining=row.resolution_seconds_remaining,
        resolution_pressure_score=resolution_pressure_score,
        recheck_priority_score=_recheck_priority_score(
            row,
            failed_attempt_pressure_score=failed_attempt_pressure_score,
            resolution_pressure_score=resolution_pressure_score,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityScraplingRecheckPriorityInput,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.source_authority_score <= config.authority_block_floor:
        reasons.append(LOW_AUTHORITY_BLOCK_REASON)
    elif row.source_authority_score < config.authority_watch_floor:
        reasons.append(LOW_AUTHORITY_WATCH_REASON)
    if row.scrapling_latest_success_age_seconds >= config.scrapling_freshness_block_age_seconds:
        reasons.append(STALE_SCRAPLING_BLOCK_REASON)
    elif row.scrapling_latest_success_age_seconds > config.scrapling_freshness_watch_age_seconds:
        reasons.append(STALE_SCRAPLING_WATCH_REASON)
    if row.authority_revision_age_seconds >= config.authority_revision_block_age_seconds:
        reasons.append(STALE_AUTHORITY_REVISION_BLOCK_REASON)
    elif row.authority_revision_age_seconds > config.authority_revision_watch_age_seconds:
        reasons.append(STALE_AUTHORITY_REVISION_WATCH_REASON)
    if row.scrapling_extraction_confidence_score <= config.extraction_confidence_block_floor:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON)
    elif row.scrapling_extraction_confidence_score < config.extraction_confidence_watch_floor:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_WATCH_REASON)
    if row.cross_extractor_disagreement_score >= config.extractor_disagreement_block_pressure:
        reasons.append(EXTRACTOR_DISAGREEMENT_BLOCK_REASON)
    elif row.cross_extractor_disagreement_score >= config.extractor_disagreement_watch_pressure:
        reasons.append(EXTRACTOR_DISAGREEMENT_WATCH_REASON)
    if row.primary_evidence_coverage_ratio <= config.primary_coverage_block_floor:
        reasons.append(THIN_PRIMARY_COVERAGE_BLOCK_REASON)
    elif row.primary_evidence_coverage_ratio < config.primary_coverage_watch_floor:
        reasons.append(THIN_PRIMARY_COVERAGE_WATCH_REASON)
    if row.unresolved_claim_count >= config.unresolved_claim_block_count:
        reasons.append(UNRESOLVED_CLAIM_BLOCK_REASON)
    elif row.unresolved_claim_count >= config.unresolved_claim_watch_count:
        reasons.append(UNRESOLVED_CLAIM_WATCH_REASON)
    if row.failed_scrapling_attempt_count >= config.failed_attempt_block_count:
        reasons.append(FAILED_ATTEMPT_BLOCK_REASON)
    elif row.failed_scrapling_attempt_count >= config.failed_attempt_watch_count:
        reasons.append(FAILED_ATTEMPT_WATCH_REASON)
    if row.resolution_seconds_remaining <= config.resolution_block_seconds_remaining:
        reasons.append(RESOLUTION_PROXIMITY_BLOCK_REASON)
    elif row.resolution_seconds_remaining < config.resolution_watch_seconds_remaining:
        reasons.append(RESOLUTION_PROXIMITY_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _recheck_priority_score(
    row: ResearchSourceAuthorityScraplingRecheckPriorityInput,
    *,
    failed_attempt_pressure_score: Decimal,
    resolution_pressure_score: Decimal,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = ONE - row.source_authority_score
        scrapling_freshness_pressure = min(
            row.scrapling_latest_success_age_seconds
            / config.scrapling_freshness_block_age_seconds,
            ONE,
        )
        authority_revision_pressure = min(
            row.authority_revision_age_seconds
            / config.authority_revision_block_age_seconds,
            ONE,
        )
        extraction_gap = ONE - row.scrapling_extraction_confidence_score
        primary_coverage_gap = ONE - row.primary_evidence_coverage_ratio
        unresolved_claim_pressure = min(
            _ratio(row.unresolved_claim_count, config.unresolved_claim_block_count),
            ONE,
        )
        score = (
            authority_gap * AUTHORITY_WEIGHT
            + scrapling_freshness_pressure * SCRAPLING_FRESHNESS_WEIGHT
            + authority_revision_pressure * AUTHORITY_REVISION_WEIGHT
            + extraction_gap * EXTRACTION_CONFIDENCE_WEIGHT
            + row.cross_extractor_disagreement_score * EXTRACTOR_DISAGREEMENT_WEIGHT
            + primary_coverage_gap * PRIMARY_COVERAGE_WEIGHT
            + unresolved_claim_pressure * UNRESOLVED_CLAIM_WEIGHT
            + failed_attempt_pressure_score * FAILED_ATTEMPT_WEIGHT
            + resolution_pressure_score * RESOLUTION_PROXIMITY_WEIGHT
        )
        return _quantize(min(score, ONE))


def _failed_attempt_pressure_score(failed_count: Decimal, successful_count: Decimal) -> Decimal:
    return _safe_ratio(failed_count, failed_count + successful_count)


def _resolution_pressure_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        open_fraction = min(value / config.resolution_watch_seconds_remaining, ONE)
        return _quantize(ONE - open_fraction)


def _authority_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> str:
    if value >= config.authority_watch_floor:
        return "high"
    if value <= config.authority_block_floor:
        return "low"
    return "medium"


def _scrapling_freshness_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> str:
    if value <= config.scrapling_freshness_watch_age_seconds:
        return "fresh"
    if value < config.scrapling_freshness_block_age_seconds:
        return "aging"
    return "stale"


def _authority_revision_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> str:
    if value <= config.authority_revision_watch_age_seconds:
        return "current"
    if value < config.authority_revision_block_age_seconds:
        return "aging"
    return "stale"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchSourceAuthorityScraplingRecheckPriorityRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityScraplingRecheckPriorityRow, ...],
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


def _row_sort_key(
    row: ResearchSourceAuthorityScraplingRecheckPriorityRow,
) -> tuple[Decimal, str]:
    return (-row.recheck_priority_score, row.recheck_bucket)


def _default_config() -> ResearchSourceAuthorityScraplingRecheckPriorityConfig:
    return ResearchSourceAuthorityScraplingRecheckPriorityConfig()


def _report_validation_config(
    report: ResearchSourceAuthorityScraplingRecheckPriorityReport,
) -> ResearchSourceAuthorityScraplingRecheckPriorityConfig:
    config = getattr(report, "_validation_config", None)
    if type(config) is ResearchSourceAuthorityScraplingRecheckPriorityConfig:
        _validate_config(config)
        _require_hard_flags("config", config)
        return config
    return _default_config()


def _input_from_row(
    row: ResearchSourceAuthorityScraplingRecheckPriorityRow,
) -> ResearchSourceAuthorityScraplingRecheckPriorityInput:
    return ResearchSourceAuthorityScraplingRecheckPriorityInput(
        recheck_bucket=row.recheck_bucket,
        source_authority_score=row.source_authority_score,
        scrapling_latest_success_age_seconds=row.scrapling_latest_success_age_seconds,
        authority_revision_age_seconds=row.authority_revision_age_seconds,
        scrapling_extraction_confidence_score=row.scrapling_extraction_confidence_score,
        cross_extractor_disagreement_score=row.cross_extractor_disagreement_score,
        primary_evidence_coverage_ratio=row.primary_evidence_coverage_ratio,
        unresolved_claim_count=row.unresolved_claim_count,
        failed_scrapling_attempt_count=row.failed_scrapling_attempt_count,
        successful_scrapling_attempt_count=row.successful_scrapling_attempt_count,
        resolution_seconds_remaining=row.resolution_seconds_remaining,
    )


def _status_count(
    rows: tuple[ResearchSourceAuthorityScraplingRecheckPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityScraplingRecheckPriorityRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourceAuthorityScraplingRecheckPriorityConfig) -> None:
    if config.authority_block_floor > config.authority_watch_floor:
        raise ValueError("authority_block_floor must not exceed authority_watch_floor")
    if config.scrapling_freshness_watch_age_seconds >= config.scrapling_freshness_block_age_seconds:
        raise ValueError(
            "scrapling_freshness_watch_age_seconds must be less than block threshold",
        )
    if config.authority_revision_watch_age_seconds >= config.authority_revision_block_age_seconds:
        raise ValueError(
            "authority_revision_watch_age_seconds must be less than block threshold",
        )
    if config.extraction_confidence_block_floor > config.extraction_confidence_watch_floor:
        raise ValueError(
            "extraction_confidence_block_floor must not exceed watch threshold",
        )
    if config.extractor_disagreement_watch_pressure > config.extractor_disagreement_block_pressure:
        raise ValueError(
            "extractor_disagreement_watch_pressure must not exceed block threshold",
        )
    if config.primary_coverage_block_floor > config.primary_coverage_watch_floor:
        raise ValueError("primary_coverage_block_floor must not exceed watch floor")
    if config.unresolved_claim_watch_count > config.unresolved_claim_block_count:
        raise ValueError("unresolved_claim_watch_count must not exceed block count")
    if config.failed_attempt_watch_count > config.failed_attempt_block_count:
        raise ValueError("failed_attempt_watch_count must not exceed block count")
    if config.resolution_block_seconds_remaining > config.resolution_watch_seconds_remaining:
        raise ValueError("resolution_block_seconds_remaining must not exceed watch threshold")


def _validate_row(
    row: ResearchSourceAuthorityScraplingRecheckPriorityRow,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> None:
    if row.failed_attempt_pressure_score != _failed_attempt_pressure_score(
        row.failed_scrapling_attempt_count,
        row.successful_scrapling_attempt_count,
    ):
        raise ValueError("failed_attempt_pressure_score must match attempt counts")
    if row.resolution_pressure_score != _resolution_pressure_score(
        row.resolution_seconds_remaining,
        config=config,
    ):
        raise ValueError("resolution_pressure_score must match resolution_seconds_remaining")
    if row.authority_band != _authority_band(row.source_authority_score, config=config):
        raise ValueError("authority_band must match source_authority_score")
    if row.scrapling_freshness_band != _scrapling_freshness_band(
        row.scrapling_latest_success_age_seconds,
        config=config,
    ):
        raise ValueError(
            "scrapling_freshness_band must match scrapling_latest_success_age_seconds",
        )
    if row.authority_revision_band != _authority_revision_band(
        row.authority_revision_age_seconds,
        config=config,
    ):
        raise ValueError(
            "authority_revision_band must match authority_revision_age_seconds",
        )
    expected_priority_score = _recheck_priority_score(
        _input_from_row(row),
        failed_attempt_pressure_score=row.failed_attempt_pressure_score,
        resolution_pressure_score=row.resolution_pressure_score,
        config=config,
    )
    if row.recheck_priority_score != expected_priority_score:
        raise ValueError("recheck_priority_score must match row inputs")
    expected_reason_codes = _row_reason_codes(_input_from_row(row), config=config)
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use clear reason")


def _validate_report(
    report: ResearchSourceAuthorityScraplingRecheckPriorityReport,
    *,
    config: ResearchSourceAuthorityScraplingRecheckPriorityConfig,
) -> None:
    for row in report.rows:
        _validate_row(row, config=config)
    if report.recheck_item_count != _count(len(report.rows)):
        raise ValueError("recheck_item_count must match rows")
    for status, field_name in (
        ("pass", "pass_recheck_item_count"),
        ("watch", "watch_recheck_item_count"),
        ("block", "block_recheck_item_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        ("low_authority_count", (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON)),
        ("stale_scrapling_count", (STALE_SCRAPLING_WATCH_REASON, STALE_SCRAPLING_BLOCK_REASON)),
        (
            "stale_authority_revision_count",
            (
                STALE_AUTHORITY_REVISION_WATCH_REASON,
                STALE_AUTHORITY_REVISION_BLOCK_REASON,
            ),
        ),
        (
            "low_extraction_confidence_count",
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        (
            "extractor_disagreement_count",
            (EXTRACTOR_DISAGREEMENT_WATCH_REASON, EXTRACTOR_DISAGREEMENT_BLOCK_REASON),
        ),
        (
            "thin_primary_coverage_count",
            (THIN_PRIMARY_COVERAGE_WATCH_REASON, THIN_PRIMARY_COVERAGE_BLOCK_REASON),
        ),
        (
            "unresolved_claim_count",
            (UNRESOLVED_CLAIM_WATCH_REASON, UNRESOLVED_CLAIM_BLOCK_REASON),
        ),
        (
            "failed_attempt_pressure_count",
            (FAILED_ATTEMPT_WATCH_REASON, FAILED_ATTEMPT_BLOCK_REASON),
        ),
        (
            "resolution_proximity_count",
            (RESOLUTION_PROXIMITY_WATCH_REASON, RESOLUTION_PROXIMITY_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_recheck_priority_score != _quantize(max(
        (row.recheck_priority_score for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("highest_recheck_priority_score must match rows")
    if report.oldest_scrapling_latest_success_age_seconds != _quantize(max(
        (row.scrapling_latest_success_age_seconds for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("oldest_scrapling_latest_success_age_seconds must match rows")
    if report.oldest_authority_revision_age_seconds != _quantize(max(
        (row.authority_revision_age_seconds for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("oldest_authority_revision_age_seconds must match rows")
    if report.lowest_source_authority_score != _quantize(min(
        (row.source_authority_score for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("lowest_source_authority_score must match rows")
    if report.lowest_scrapling_extraction_confidence_score != _quantize(min(
        (row.scrapling_extraction_confidence_score for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("lowest_scrapling_extraction_confidence_score must match rows")
    if report.highest_cross_extractor_disagreement_score != _quantize(max(
        (row.cross_extractor_disagreement_score for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("highest_cross_extractor_disagreement_score must match rows")
    if report.lowest_primary_evidence_coverage_ratio != _quantize(min(
        (row.primary_evidence_coverage_ratio for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("lowest_primary_evidence_coverage_ratio must match rows")
    if report.nearest_resolution_seconds_remaining != _quantize(min(
        (row.resolution_seconds_remaining for row in report.rows),
        default=ZERO,
    )):
        raise ValueError("nearest_resolution_seconds_remaining must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic priority sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityScraplingRecheckPriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityScraplingRecheckPriorityRow:
            raise ValueError(
                "rows must contain ResearchSourceAuthorityScraplingRecheckPriorityRow",
            )
        _require_hard_flags("row", row)
        if row.recheck_bucket in seen:
            raise ValueError("rows must be unique by recheck_bucket")
        seen.add(row.recheck_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return _quantize(Decimal(value))


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
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        return _quantize(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        is_whole = decimal_value == decimal_value.to_integral_value()
    if not is_whole:
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
        result = numerator_value / denominator_value
    return _quantize(result)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        result = numerator_value / denominator_value
    return _quantize(result)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("decimal value must fit the decimal context") from exc
    return ZERO if normalized.is_zero() else normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_authority_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("high", "medium", "low"):
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_freshness_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "aging", "stale"):
        raise ValueError(f"{field_name} must be fresh, aging, or stale")


def _require_revision_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("current", "aging", "stale"):
        raise ValueError(f"{field_name} must be current, aging, or stale")


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


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _require_or_set_digest(
    report: ResearchSourceAuthorityScraplingRecheckPriorityReport,
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
    report: ResearchSourceAuthorityScraplingRecheckPriorityReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    _validate_public_flags(payload)
    _validate_public_statuses(payload)
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


def _validate_public_flags(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _validate_public_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_flags(item)


def _validate_public_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status" and item not in RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_STATUSES:
                raise ValueError("public payload status must be pass, watch, or block")
            _validate_public_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_statuses(item)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_SCRAPLING_RECHECK_PRIORITY_STATUSES",
    "ResearchSourceAuthorityScraplingRecheckPriorityConfig",
    "ResearchSourceAuthorityScraplingRecheckPriorityInput",
    "ResearchSourceAuthorityScraplingRecheckPriorityReport",
    "ResearchSourceAuthorityScraplingRecheckPriorityRow",
    "build_research_source_authority_scrapling_recheck_priority_report",
    "research_source_authority_scrapling_recheck_priority_report_digest",
    "research_source_authority_scrapling_recheck_priority_report_payload",
    "validate_research_source_authority_scrapling_recheck_priority_report_digest",
)
