"""Pure in-memory primary resolution signal completeness report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_REPORT_CONFIG_VERSION = (
    "research-source-primary-resolution-signal-completeness-report-v0"
)
RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_source_primary_resolution_signal_completeness_empty"
HEALTHY_REASON = "primary_resolution_signal_complete"
LOW_AUTHORITY_COVERAGE_WATCH_REASON = "low_authority_coverage_watch"
LOW_AUTHORITY_COVERAGE_BLOCK_REASON = "low_authority_coverage_block"
STALE_SIGNAL_WATCH_REASON = "stale_primary_resolution_signal_watch"
STALE_SIGNAL_BLOCK_REASON = "stale_primary_resolution_signal_block"
THIN_CORROBORATION_WATCH_REASON = "thin_corroboration_watch"
THIN_CORROBORATION_BLOCK_REASON = "thin_corroboration_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
LOW_EXTRACTION_CONFIDENCE_WATCH_REASON = "low_extraction_confidence_watch"
LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON = "low_extraction_confidence_block"
DEADLINE_PROXIMITY_WATCH_REASON = "deadline_proximity_watch"
DEADLINE_PROXIMITY_BLOCK_REASON = "deadline_proximity_block"

ROW_REASON_CODES = (
    HEALTHY_REASON,
    LOW_AUTHORITY_COVERAGE_BLOCK_REASON,
    STALE_SIGNAL_BLOCK_REASON,
    THIN_CORROBORATION_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
    DEADLINE_PROXIMITY_BLOCK_REASON,
    LOW_AUTHORITY_COVERAGE_WATCH_REASON,
    STALE_SIGNAL_WATCH_REASON,
    THIN_CORROBORATION_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
    DEADLINE_PROXIMITY_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, HEALTHY_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

REPORT_PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "signal_family_count",
    "pass_signal_family_count",
    "watch_signal_family_count",
    "block_signal_family_count",
    "low_authority_coverage_count",
    "stale_signal_count",
    "thin_corroboration_count",
    "contradiction_pressure_count",
    "low_extraction_confidence_count",
    "deadline_proximity_count",
    "highest_resolution_signal_gap_score",
    "lowest_authority_coverage_score",
    "oldest_signal_freshness_seconds",
    "lowest_corroboration_score",
    "highest_contradiction_pressure_score",
    "lowest_extraction_confidence_score",
    "nearest_deadline_seconds_remaining",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_PAYLOAD_KEYS = (
    "signal_family",
    "authority_coverage_score",
    "authority_coverage_band",
    "signal_freshness_seconds",
    "freshness_band",
    "freshness_pressure_score",
    "corroboration_score",
    "corroboration_band",
    "contradiction_pressure_score",
    "contradiction_pressure_band",
    "extraction_confidence_score",
    "extraction_confidence_band",
    "deadline_seconds_remaining",
    "deadline_proximity_band",
    "deadline_pressure_score",
    "resolution_signal_gap_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchSourcePrimaryResolutionSignalCompletenessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    authority_coverage_watch_threshold: Decimal = Decimal("0.750000")
    authority_coverage_block_threshold: Decimal = Decimal("0.500000")
    freshness_watch_age_seconds: Decimal = Decimal("1800.000000")
    freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    corroboration_watch_threshold: Decimal = Decimal("0.650000")
    corroboration_block_threshold: Decimal = Decimal("0.400000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.600000")
    extraction_confidence_watch_threshold: Decimal = Decimal("0.750000")
    extraction_confidence_block_threshold: Decimal = Decimal("0.550000")
    deadline_watch_seconds_remaining: Decimal = Decimal("3600.000000")
    deadline_block_seconds_remaining: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryResolutionSignalCompletenessConfig:
            raise TypeError(
                "ResearchSourcePrimaryResolutionSignalCompletenessConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryResolutionSignalCompletenessConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourcePrimaryResolutionSignalCompletenessConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
            "deadline_watch_seconds_remaining",
            "deadline_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_coverage_watch_threshold",
            "authority_coverage_block_threshold",
            "corroboration_watch_threshold",
            "corroboration_block_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "extraction_confidence_watch_threshold",
            "extraction_confidence_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryResolutionSignalCompletenessInput:
    signal_family: str
    authority_coverage_score: Decimal
    signal_freshness_seconds: Decimal
    corroboration_score: Decimal
    contradiction_pressure_score: Decimal
    extraction_confidence_score: Decimal
    deadline_seconds_remaining: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryResolutionSignalCompletenessInput:
            raise TypeError(
                "ResearchSourcePrimaryResolutionSignalCompletenessInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryResolutionSignalCompletenessInput:
            raise ValueError(
                "input must be exactly "
                "ResearchSourcePrimaryResolutionSignalCompletenessInput",
            )
        object.__setattr__(
            self,
            "signal_family",
            _require_public_signal_family("signal_family", self.signal_family),
        )
        for field_name in (
            "authority_coverage_score",
            "corroboration_score",
            "contradiction_pressure_score",
            "extraction_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("signal_freshness_seconds", "deadline_seconds_remaining"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryResolutionSignalCompletenessRow:
    signal_family: str
    authority_coverage_score: Decimal
    authority_coverage_band: str
    signal_freshness_seconds: Decimal
    freshness_band: str
    freshness_pressure_score: Decimal
    corroboration_score: Decimal
    corroboration_band: str
    contradiction_pressure_score: Decimal
    contradiction_pressure_band: str
    extraction_confidence_score: Decimal
    extraction_confidence_band: str
    deadline_seconds_remaining: Decimal
    deadline_proximity_band: str
    deadline_pressure_score: Decimal
    resolution_signal_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryResolutionSignalCompletenessRow:
            raise TypeError(
                "ResearchSourcePrimaryResolutionSignalCompletenessRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryResolutionSignalCompletenessRow:
            raise ValueError("row must be exactly ResearchSourcePrimaryResolutionSignalCompletenessRow")
        object.__setattr__(
            self,
            "signal_family",
            _require_public_signal_family("signal_family", self.signal_family),
        )
        for field_name in ("signal_freshness_seconds", "deadline_seconds_remaining"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_coverage_score",
            "freshness_pressure_score",
            "corroboration_score",
            "contradiction_pressure_score",
            "extraction_confidence_score",
            "deadline_pressure_score",
            "resolution_signal_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_authority_coverage_band(
            "authority_coverage_band",
            self.authority_coverage_band,
        )
        _require_freshness_band("freshness_band", self.freshness_band)
        _require_corroboration_band("corroboration_band", self.corroboration_band)
        _require_contradiction_pressure_band(
            "contradiction_pressure_band",
            self.contradiction_pressure_band,
        )
        _require_extraction_confidence_band(
            "extraction_confidence_band",
            self.extraction_confidence_band,
        )
        _require_deadline_proximity_band(
            "deadline_proximity_band",
            self.deadline_proximity_band,
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
class ResearchSourcePrimaryResolutionSignalCompletenessReport:
    generated_at: datetime
    config_version: str
    signal_family_count: Decimal
    pass_signal_family_count: Decimal
    watch_signal_family_count: Decimal
    block_signal_family_count: Decimal
    low_authority_coverage_count: Decimal
    stale_signal_count: Decimal
    thin_corroboration_count: Decimal
    contradiction_pressure_count: Decimal
    low_extraction_confidence_count: Decimal
    deadline_proximity_count: Decimal
    highest_resolution_signal_gap_score: Decimal
    lowest_authority_coverage_score: Decimal
    oldest_signal_freshness_seconds: Decimal
    lowest_corroboration_score: Decimal
    highest_contradiction_pressure_score: Decimal
    lowest_extraction_confidence_score: Decimal
    nearest_deadline_seconds_remaining: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourcePrimaryResolutionSignalCompletenessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryResolutionSignalCompletenessReport:
            raise TypeError(
                "ResearchSourcePrimaryResolutionSignalCompletenessReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryResolutionSignalCompletenessReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourcePrimaryResolutionSignalCompletenessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "signal_family_count",
            "pass_signal_family_count",
            "watch_signal_family_count",
            "block_signal_family_count",
            "low_authority_coverage_count",
            "stale_signal_count",
            "thin_corroboration_count",
            "contradiction_pressure_count",
            "low_extraction_confidence_count",
            "deadline_proximity_count",
            "oldest_signal_freshness_seconds",
            "nearest_deadline_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_resolution_signal_gap_score",
            "lowest_authority_coverage_score",
            "lowest_corroboration_score",
            "highest_contradiction_pressure_score",
            "lowest_extraction_confidence_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _reject_unsafe_public_surface_fields(self)
        require_paper_only_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_public_payload(self),
            )
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest_from_public_payload(self):
                raise ValueError("derived_validation_digest must match report payload")


def build_research_source_primary_resolution_signal_completeness_report(
    inputs: list[ResearchSourcePrimaryResolutionSignalCompletenessInput]
    | tuple[ResearchSourcePrimaryResolutionSignalCompletenessInput, ...],
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
    generated_at: datetime,
) -> ResearchSourcePrimaryResolutionSignalCompletenessReport:
    if type(config) is not ResearchSourcePrimaryResolutionSignalCompletenessConfig:
        raise ValueError(
            "config must be a ResearchSourcePrimaryResolutionSignalCompletenessConfig",
        )
    config = _revalidate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _completeness_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourcePrimaryResolutionSignalCompletenessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_family_count=_count(len(rows)),
        pass_signal_family_count=_status_count(rows, "pass"),
        watch_signal_family_count=_status_count(rows, "watch"),
        block_signal_family_count=_status_count(rows, "block"),
        low_authority_coverage_count=_reason_count(
            rows,
            (LOW_AUTHORITY_COVERAGE_WATCH_REASON, LOW_AUTHORITY_COVERAGE_BLOCK_REASON),
        ),
        stale_signal_count=_reason_count(
            rows,
            (STALE_SIGNAL_WATCH_REASON, STALE_SIGNAL_BLOCK_REASON),
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
        deadline_proximity_count=_reason_count(
            rows,
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
        highest_resolution_signal_gap_score=max(
            (row.resolution_signal_gap_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_authority_coverage_score=min(
            (row.authority_coverage_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_signal_freshness_seconds=max(
            (row.signal_freshness_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_corroboration_score=min(
            (row.corroboration_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_pressure_score=max(
            (row.contradiction_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_extraction_confidence_score=min(
            (row.extraction_confidence_score for row in rows),
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


def research_source_primary_resolution_signal_completeness_report_payload(
    report: ResearchSourcePrimaryResolutionSignalCompletenessReport,
) -> dict[str, Any]:
    revalidated_report = _revalidate_report(report)
    payload = json_ready_no_floats(revalidated_report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_report_public_payload_or_raise(payload)
    return payload


def research_source_primary_resolution_signal_completeness_report_digest(
    report: ResearchSourcePrimaryResolutionSignalCompletenessReport,
) -> str:
    return _revalidate_report(report).derived_validation_digest


def validate_research_source_primary_resolution_signal_completeness_report_digest(
    report: ResearchSourcePrimaryResolutionSignalCompletenessReport,
) -> None:
    _revalidate_report(report)


def validate_research_source_primary_resolution_signal_completeness_report_public_payload(
    payload: object,
) -> bool:
    try:
        _validate_report_public_payload_or_raise(payload)
    except (InvalidOperation, KeyError, OverflowError, TypeError, ValueError):
        return False
    return True


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourcePrimaryResolutionSignalCompletenessInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    normalized_rows: list[ResearchSourcePrimaryResolutionSignalCompletenessInput] = []
    for raw_row in rows:
        row = _revalidate_input(raw_row)
        if type(row) is not ResearchSourcePrimaryResolutionSignalCompletenessInput:
            raise ValueError(
                "inputs must contain "
                "ResearchSourcePrimaryResolutionSignalCompletenessInput",
            )
        if row.signal_family in seen:
            raise ValueError("inputs must be unique by signal_family")
        seen.add(row.signal_family)
        normalized_rows.append(row)
    return tuple(sorted(normalized_rows, key=lambda row: row.signal_family))


def _completeness_rows(
    inputs: tuple[ResearchSourcePrimaryResolutionSignalCompletenessInput, ...],
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> tuple[ResearchSourcePrimaryResolutionSignalCompletenessRow, ...]:
    return tuple(
        sorted((_completeness_row(row, config=config) for row in inputs), key=_row_sort_key),
    )


def _completeness_row(
    row: ResearchSourcePrimaryResolutionSignalCompletenessInput,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> ResearchSourcePrimaryResolutionSignalCompletenessRow:
    reason_codes = _row_reason_codes(row, config=config)
    freshness_pressure_score = _freshness_pressure_score(
        row.signal_freshness_seconds,
        config=config,
    )
    deadline_pressure_score = _deadline_pressure_score(
        row.deadline_seconds_remaining,
        config=config,
    )
    return ResearchSourcePrimaryResolutionSignalCompletenessRow(
        signal_family=row.signal_family,
        authority_coverage_score=row.authority_coverage_score,
        authority_coverage_band=_authority_coverage_band(
            row.authority_coverage_score,
            config=config,
        ),
        signal_freshness_seconds=row.signal_freshness_seconds,
        freshness_band=_freshness_band(row.signal_freshness_seconds, config=config),
        freshness_pressure_score=freshness_pressure_score,
        corroboration_score=row.corroboration_score,
        corroboration_band=_corroboration_band(row.corroboration_score, config=config),
        contradiction_pressure_score=row.contradiction_pressure_score,
        contradiction_pressure_band=_contradiction_pressure_band(
            row.contradiction_pressure_score,
            config=config,
        ),
        extraction_confidence_score=row.extraction_confidence_score,
        extraction_confidence_band=_extraction_confidence_band(
            row.extraction_confidence_score,
            config=config,
        ),
        deadline_seconds_remaining=row.deadline_seconds_remaining,
        deadline_proximity_band=_deadline_proximity_band(
            row.deadline_seconds_remaining,
            config=config,
        ),
        deadline_pressure_score=deadline_pressure_score,
        resolution_signal_gap_score=_resolution_signal_gap_score(
            row,
            freshness_pressure_score=freshness_pressure_score,
            deadline_pressure_score=deadline_pressure_score,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourcePrimaryResolutionSignalCompletenessInput,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.authority_coverage_score <= config.authority_coverage_block_threshold:
        reasons.append(LOW_AUTHORITY_COVERAGE_BLOCK_REASON)
    elif row.authority_coverage_score < config.authority_coverage_watch_threshold:
        reasons.append(LOW_AUTHORITY_COVERAGE_WATCH_REASON)
    if row.signal_freshness_seconds >= config.freshness_block_age_seconds:
        reasons.append(STALE_SIGNAL_BLOCK_REASON)
    elif row.signal_freshness_seconds > config.freshness_watch_age_seconds:
        reasons.append(STALE_SIGNAL_WATCH_REASON)
    if row.corroboration_score <= config.corroboration_block_threshold:
        reasons.append(THIN_CORROBORATION_BLOCK_REASON)
    elif row.corroboration_score < config.corroboration_watch_threshold:
        reasons.append(THIN_CORROBORATION_WATCH_REASON)
    if row.contradiction_pressure_score >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if row.extraction_confidence_score <= config.extraction_confidence_block_threshold:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON)
    elif row.extraction_confidence_score < config.extraction_confidence_watch_threshold:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_WATCH_REASON)
    if row.deadline_seconds_remaining <= config.deadline_block_seconds_remaining:
        reasons.append(DEADLINE_PROXIMITY_BLOCK_REASON)
    elif row.deadline_seconds_remaining < config.deadline_watch_seconds_remaining:
        reasons.append(DEADLINE_PROXIMITY_WATCH_REASON)
    if not reasons:
        reasons.append(HEALTHY_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _resolution_signal_gap_score(
    row: ResearchSourcePrimaryResolutionSignalCompletenessInput,
    *,
    freshness_pressure_score: Decimal,
    deadline_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        authority_gap = ONE - row.authority_coverage_score
        corroboration_gap = ONE - row.corroboration_score
        extraction_gap = ONE - row.extraction_confidence_score
        score = (
            authority_gap * Decimal("0.200000")
            + freshness_pressure_score * Decimal("0.150000")
            + corroboration_gap * Decimal("0.150000")
            + row.contradiction_pressure_score * Decimal("0.200000")
            + extraction_gap * Decimal("0.200000")
            + deadline_pressure_score * Decimal("0.100000")
        )
        return min(score, ONE).quantize(QUANT)


def _freshness_pressure_score(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / config.freshness_block_age_seconds, ONE).quantize(QUANT)


def _deadline_pressure_score(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        open_fraction = min(value / config.deadline_watch_seconds_remaining, ONE)
        return (ONE - open_fraction).quantize(QUANT)


def _authority_coverage_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> str:
    if value <= config.authority_coverage_block_threshold:
        return "gap"
    if value < config.authority_coverage_watch_threshold:
        return "partial"
    return "covered"


def _freshness_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> str:
    if value >= config.freshness_block_age_seconds:
        return "stale"
    if value > config.freshness_watch_age_seconds:
        return "aging"
    return "fresh"


def _corroboration_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> str:
    if value <= config.corroboration_block_threshold:
        return "missing"
    if value < config.corroboration_watch_threshold:
        return "thin"
    return "strong"


def _contradiction_pressure_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> str:
    if value >= config.contradiction_block_threshold:
        return "high"
    if value >= config.contradiction_watch_threshold:
        return "elevated"
    return "low"


def _extraction_confidence_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> str:
    if value <= config.extraction_confidence_block_threshold:
        return "low"
    if value < config.extraction_confidence_watch_threshold:
        return "medium"
    return "high"


def _deadline_proximity_band(
    value: Decimal,
    *,
    config: ResearchSourcePrimaryResolutionSignalCompletenessConfig,
) -> str:
    if value <= config.deadline_block_seconds_remaining:
        return "immediate"
    if value < config.deadline_watch_seconds_remaining:
        return "near"
    return "open"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (HEALTHY_REASON,):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchSourcePrimaryResolutionSignalCompletenessRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimaryResolutionSignalCompletenessRow, ...],
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
    return (HEALTHY_REASON,)


def _row_sort_key(
    row: ResearchSourcePrimaryResolutionSignalCompletenessRow,
) -> tuple[Decimal, str]:
    return (-row.resolution_signal_gap_score, row.signal_family)


def _status_count(
    rows: tuple[ResearchSourcePrimaryResolutionSignalCompletenessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourcePrimaryResolutionSignalCompletenessRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourcePrimaryResolutionSignalCompletenessConfig) -> None:
    if config.authority_coverage_block_threshold > config.authority_coverage_watch_threshold:
        raise ValueError(
            "authority_coverage_block_threshold must not exceed "
            "authority_coverage_watch_threshold",
        )
    if config.freshness_watch_age_seconds >= config.freshness_block_age_seconds:
        raise ValueError("freshness_watch_age_seconds must be less than freshness_block_age_seconds")
    if config.corroboration_block_threshold > config.corroboration_watch_threshold:
        raise ValueError(
            "corroboration_block_threshold must not exceed corroboration_watch_threshold",
        )
    if config.contradiction_watch_threshold > config.contradiction_block_threshold:
        raise ValueError(
            "contradiction_watch_threshold must not exceed contradiction_block_threshold",
        )
    if config.extraction_confidence_block_threshold > config.extraction_confidence_watch_threshold:
        raise ValueError(
            "extraction_confidence_block_threshold must not exceed "
            "extraction_confidence_watch_threshold",
        )
    if config.deadline_block_seconds_remaining > config.deadline_watch_seconds_remaining:
        raise ValueError(
            "deadline_block_seconds_remaining must not exceed deadline_watch_seconds_remaining",
        )


def _validate_row(row: ResearchSourcePrimaryResolutionSignalCompletenessRow) -> None:
    if row.reason_codes != _row_reason_codes_from_bands(row):
        raise ValueError("reason_codes must match row bands")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (HEALTHY_REASON,):
        raise ValueError("pass rows must be complete")
    with localcontext(DECIMAL_CONTEXT):
        expected_gap_score = min(
            (ONE - row.authority_coverage_score) * Decimal("0.200000")
            + row.freshness_pressure_score * Decimal("0.150000")
            + (ONE - row.corroboration_score) * Decimal("0.150000")
            + row.contradiction_pressure_score * Decimal("0.200000")
            + (ONE - row.extraction_confidence_score) * Decimal("0.200000")
            + row.deadline_pressure_score * Decimal("0.100000"),
            ONE,
        ).quantize(QUANT)
    if row.resolution_signal_gap_score != expected_gap_score:
        raise ValueError("resolution_signal_gap_score must match row components")


def _row_reason_codes_from_bands(
    row: ResearchSourcePrimaryResolutionSignalCompletenessRow,
) -> tuple[str, ...]:
    band_reason_codes = (
        {
            "covered": None,
            "partial": LOW_AUTHORITY_COVERAGE_WATCH_REASON,
            "gap": LOW_AUTHORITY_COVERAGE_BLOCK_REASON,
        }[row.authority_coverage_band],
        {
            "fresh": None,
            "aging": STALE_SIGNAL_WATCH_REASON,
            "stale": STALE_SIGNAL_BLOCK_REASON,
        }[row.freshness_band],
        {
            "strong": None,
            "thin": THIN_CORROBORATION_WATCH_REASON,
            "missing": THIN_CORROBORATION_BLOCK_REASON,
        }[row.corroboration_band],
        {
            "low": None,
            "elevated": CONTRADICTION_PRESSURE_WATCH_REASON,
            "high": CONTRADICTION_PRESSURE_BLOCK_REASON,
        }[row.contradiction_pressure_band],
        {
            "high": None,
            "medium": LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
            "low": LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
        }[row.extraction_confidence_band],
        {
            "open": None,
            "near": DEADLINE_PROXIMITY_WATCH_REASON,
            "immediate": DEADLINE_PROXIMITY_BLOCK_REASON,
        }[row.deadline_proximity_band],
    )
    selected = tuple(reason for reason in band_reason_codes if reason is not None)
    if not selected:
        return (HEALTHY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODES if reason in selected)


def _validate_report(report: ResearchSourcePrimaryResolutionSignalCompletenessReport) -> None:
    if report.signal_family_count != _count(len(report.rows)):
        raise ValueError("signal_family_count must match rows")
    for status, field_name in (
        ("pass", "pass_signal_family_count"),
        ("watch", "watch_signal_family_count"),
        ("block", "block_signal_family_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "low_authority_coverage_count",
            (LOW_AUTHORITY_COVERAGE_WATCH_REASON, LOW_AUTHORITY_COVERAGE_BLOCK_REASON),
        ),
        ("stale_signal_count", (STALE_SIGNAL_WATCH_REASON, STALE_SIGNAL_BLOCK_REASON)),
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
        (
            "deadline_proximity_count",
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_resolution_signal_gap_score != max(
        (row.resolution_signal_gap_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_resolution_signal_gap_score must match rows")
    if report.lowest_authority_coverage_score != min(
        (row.authority_coverage_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_authority_coverage_score must match rows")
    if report.oldest_signal_freshness_seconds != max(
        (row.signal_freshness_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_signal_freshness_seconds must match rows")
    if report.lowest_corroboration_score != min(
        (row.corroboration_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_corroboration_score must match rows")
    if report.highest_contradiction_pressure_score != max(
        (row.contradiction_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.lowest_extraction_confidence_score != min(
        (row.extraction_confidence_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_extraction_confidence_score must match rows")
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
        raise ValueError("rows must use deterministic resolution signal gap sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourcePrimaryResolutionSignalCompletenessRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    normalized_rows: list[ResearchSourcePrimaryResolutionSignalCompletenessRow] = []
    for raw_row in rows:
        row = _revalidate_row(raw_row)
        if row.signal_family in seen:
            raise ValueError("rows must be unique by signal_family")
        seen.add(row.signal_family)
        normalized_rows.append(row)
    return tuple(sorted(normalized_rows, key=_row_sort_key))


def _count(value: int) -> Decimal:
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
    decimal_value = value.quantize(QUANT)
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value == ZERO:
        return ZERO
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


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
    for reason in reason_codes:
        if type(reason) is not str or reason not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_authority_coverage_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("covered", "partial", "gap"):
        raise ValueError(f"{field_name} must be covered, partial, or gap")


def _require_freshness_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "aging", "stale"):
        raise ValueError(f"{field_name} must be fresh, aging, or stale")


def _require_corroboration_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("strong", "thin", "missing"):
        raise ValueError(f"{field_name} must be strong, thin, or missing")


def _require_contradiction_pressure_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("low", "elevated", "high"):
        raise ValueError(f"{field_name} must be low, elevated, or high")


def _require_extraction_confidence_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("high", "medium", "low"):
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_deadline_proximity_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("open", "near", "immediate"):
        raise ValueError(f"{field_name} must be open, near, or immediate")


def _require_public_signal_family(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    unsafe_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate",
        "credential",
        "dsn",
        "identifier",
        "market",
        "private",
        "question",
        "secret",
        "slug",
        "table",
        "text",
        "token",
        "trade",
        "url",
        "wallet",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(char.isalnum() or char in (".", "_", "-") for char in value):
        raise ValueError(f"{field_name} must be a public family label")
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


def _reject_unsafe_public_surface_fields(value: object) -> None:
    payload = json_ready_no_floats(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface_value(payload)


def _reject_unsafe_public_surface_value(value: object) -> None:
    unsafe_key_fragments = (
        "account",
        "balance",
        "candidate_id",
        "cancel",
        "credential",
        "dsn",
        "exchange_mutation",
        "live_surface",
        "market_id",
        "market_question",
        "market_slug",
        "order",
        "private_key",
        "raw_candidate_id",
        "replace",
        "source_text",
        "source_url",
        "table_name",
        "token",
        "trade",
        "url",
        "wallet",
    )
    unsafe_value_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "market-",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "table",
        "dsn",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in unsafe_key_fragments):
                raise ValueError(f"unsafe public payload field: {key}")
            _reject_unsafe_public_surface_value(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_surface_value(item)
        return
    if isinstance(value, str):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in unsafe_value_fragments):
            raise ValueError("unsafe public payload value")


def _report_digest_from_public_payload(
    report: ResearchSourcePrimaryResolutionSignalCompletenessReport,
) -> str:
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _revalidate_config(
    value: object,
) -> ResearchSourcePrimaryResolutionSignalCompletenessConfig:
    if type(value) is not ResearchSourcePrimaryResolutionSignalCompletenessConfig:
        raise ValueError(
            "config must be a ResearchSourcePrimaryResolutionSignalCompletenessConfig",
        )
    return ResearchSourcePrimaryResolutionSignalCompletenessConfig(
        **{field.name: getattr(value, field.name) for field in fields(type(value))},
    )


def _revalidate_input(
    value: object,
) -> ResearchSourcePrimaryResolutionSignalCompletenessInput:
    if type(value) is not ResearchSourcePrimaryResolutionSignalCompletenessInput:
        raise ValueError(
            "inputs must contain "
            "ResearchSourcePrimaryResolutionSignalCompletenessInput",
        )
    return ResearchSourcePrimaryResolutionSignalCompletenessInput(
        **{field.name: getattr(value, field.name) for field in fields(type(value))},
    )


def _revalidate_row(
    value: object,
) -> ResearchSourcePrimaryResolutionSignalCompletenessRow:
    if type(value) is not ResearchSourcePrimaryResolutionSignalCompletenessRow:
        raise ValueError(
            "rows must contain ResearchSourcePrimaryResolutionSignalCompletenessRow",
        )
    return ResearchSourcePrimaryResolutionSignalCompletenessRow(
        **{field.name: getattr(value, field.name) for field in fields(type(value))},
    )


def _revalidate_report(
    value: object,
) -> ResearchSourcePrimaryResolutionSignalCompletenessReport:
    if type(value) is not ResearchSourcePrimaryResolutionSignalCompletenessReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryResolutionSignalCompletenessReport",
        )
    return ResearchSourcePrimaryResolutionSignalCompletenessReport(
        **{field.name: getattr(value, field.name) for field in fields(type(value))},
    )


def _validate_report_public_payload_or_raise(
    payload: object,
) -> ResearchSourcePrimaryResolutionSignalCompletenessReport:
    _require_payload_keys("payload", payload, REPORT_PUBLIC_PAYLOAD_KEYS)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface_value(payload)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_row_from_public_payload(row) for row in rows_value)
    report = ResearchSourcePrimaryResolutionSignalCompletenessReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_canonical_string(
            "config_version",
            payload["config_version"],
        ),
        signal_family_count=_payload_nonnegative_decimal(
            "signal_family_count",
            payload["signal_family_count"],
        ),
        pass_signal_family_count=_payload_nonnegative_decimal(
            "pass_signal_family_count",
            payload["pass_signal_family_count"],
        ),
        watch_signal_family_count=_payload_nonnegative_decimal(
            "watch_signal_family_count",
            payload["watch_signal_family_count"],
        ),
        block_signal_family_count=_payload_nonnegative_decimal(
            "block_signal_family_count",
            payload["block_signal_family_count"],
        ),
        low_authority_coverage_count=_payload_nonnegative_decimal(
            "low_authority_coverage_count",
            payload["low_authority_coverage_count"],
        ),
        stale_signal_count=_payload_nonnegative_decimal(
            "stale_signal_count",
            payload["stale_signal_count"],
        ),
        thin_corroboration_count=_payload_nonnegative_decimal(
            "thin_corroboration_count",
            payload["thin_corroboration_count"],
        ),
        contradiction_pressure_count=_payload_nonnegative_decimal(
            "contradiction_pressure_count",
            payload["contradiction_pressure_count"],
        ),
        low_extraction_confidence_count=_payload_nonnegative_decimal(
            "low_extraction_confidence_count",
            payload["low_extraction_confidence_count"],
        ),
        deadline_proximity_count=_payload_nonnegative_decimal(
            "deadline_proximity_count",
            payload["deadline_proximity_count"],
        ),
        highest_resolution_signal_gap_score=_payload_ratio(
            "highest_resolution_signal_gap_score",
            payload["highest_resolution_signal_gap_score"],
        ),
        lowest_authority_coverage_score=_payload_ratio(
            "lowest_authority_coverage_score",
            payload["lowest_authority_coverage_score"],
        ),
        oldest_signal_freshness_seconds=_payload_nonnegative_decimal(
            "oldest_signal_freshness_seconds",
            payload["oldest_signal_freshness_seconds"],
        ),
        lowest_corroboration_score=_payload_ratio(
            "lowest_corroboration_score",
            payload["lowest_corroboration_score"],
        ),
        highest_contradiction_pressure_score=_payload_ratio(
            "highest_contradiction_pressure_score",
            payload["highest_contradiction_pressure_score"],
        ),
        lowest_extraction_confidence_score=_payload_ratio(
            "lowest_extraction_confidence_score",
            payload["lowest_extraction_confidence_score"],
        ),
        nearest_deadline_seconds_remaining=_payload_nonnegative_decimal(
            "nearest_deadline_seconds_remaining",
            payload["nearest_deadline_seconds_remaining"],
        ),
        status=_payload_canonical_string("status", payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            REPORT_REASON_CODES,
        ),
        rows=rows,
        derived_validation_digest=_payload_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )
    canonical_payload = json_ready_no_floats(report)
    if canonical_payload != payload:
        raise ValueError("payload must use canonical schema values")
    return report


def _row_from_public_payload(
    payload: object,
) -> ResearchSourcePrimaryResolutionSignalCompletenessRow:
    _require_payload_keys("row", payload, ROW_PUBLIC_PAYLOAD_KEYS)
    if type(payload) is not dict:
        raise ValueError("row must be a dict")
    row = ResearchSourcePrimaryResolutionSignalCompletenessRow(
        signal_family=_payload_canonical_string(
            "signal_family",
            payload["signal_family"],
        ),
        authority_coverage_score=_payload_ratio(
            "authority_coverage_score",
            payload["authority_coverage_score"],
        ),
        authority_coverage_band=_payload_canonical_string(
            "authority_coverage_band",
            payload["authority_coverage_band"],
        ),
        signal_freshness_seconds=_payload_nonnegative_decimal(
            "signal_freshness_seconds",
            payload["signal_freshness_seconds"],
        ),
        freshness_band=_payload_canonical_string(
            "freshness_band",
            payload["freshness_band"],
        ),
        freshness_pressure_score=_payload_ratio(
            "freshness_pressure_score",
            payload["freshness_pressure_score"],
        ),
        corroboration_score=_payload_ratio(
            "corroboration_score",
            payload["corroboration_score"],
        ),
        corroboration_band=_payload_canonical_string(
            "corroboration_band",
            payload["corroboration_band"],
        ),
        contradiction_pressure_score=_payload_ratio(
            "contradiction_pressure_score",
            payload["contradiction_pressure_score"],
        ),
        contradiction_pressure_band=_payload_canonical_string(
            "contradiction_pressure_band",
            payload["contradiction_pressure_band"],
        ),
        extraction_confidence_score=_payload_ratio(
            "extraction_confidence_score",
            payload["extraction_confidence_score"],
        ),
        extraction_confidence_band=_payload_canonical_string(
            "extraction_confidence_band",
            payload["extraction_confidence_band"],
        ),
        deadline_seconds_remaining=_payload_nonnegative_decimal(
            "deadline_seconds_remaining",
            payload["deadline_seconds_remaining"],
        ),
        deadline_proximity_band=_payload_canonical_string(
            "deadline_proximity_band",
            payload["deadline_proximity_band"],
        ),
        deadline_pressure_score=_payload_ratio(
            "deadline_pressure_score",
            payload["deadline_pressure_score"],
        ),
        resolution_signal_gap_score=_payload_ratio(
            "resolution_signal_gap_score",
            payload["resolution_signal_gap_score"],
        ),
        status=_payload_canonical_string("status", payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            ROW_REASON_CODES,
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )
    canonical_payload = json_ready_no_floats(row)
    if canonical_payload != payload:
        raise ValueError("row must use canonical schema values")
    return row


def _require_payload_keys(
    label: str,
    value: object,
    expected_keys: tuple[str, ...],
) -> None:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    if set(value) != set(expected_keys):
        raise ValueError(f"{label} keys must match expected public schema")


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO-8601 string")
    parsed = datetime.fromisoformat(value)
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must use canonical UTC ISO-8601")
    return normalized


def _payload_canonical_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    decimal_value = _require_nonnegative_decimal(field_name, Decimal(value))
    if format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must use canonical Decimal text")
    return decimal_value


def _payload_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _payload_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _payload_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(field_name, tuple(value), allowed)
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use canonical reason codes")
    return normalized


def _payload_sha256(field_name: str, value: object) -> str:
    _require_sha256(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be true")
    return True


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_PRIMARY_RESOLUTION_SIGNAL_COMPLETENESS_STATUSES",
    "ResearchSourcePrimaryResolutionSignalCompletenessConfig",
    "ResearchSourcePrimaryResolutionSignalCompletenessInput",
    "ResearchSourcePrimaryResolutionSignalCompletenessReport",
    "ResearchSourcePrimaryResolutionSignalCompletenessRow",
    "build_research_source_primary_resolution_signal_completeness_report",
    "research_source_primary_resolution_signal_completeness_report_digest",
    "research_source_primary_resolution_signal_completeness_report_payload",
    "validate_research_source_primary_resolution_signal_completeness_report_digest",
    "validate_research_source_primary_resolution_signal_completeness_report_public_payload",
)
