"""Pure in-memory source resolution evidence gap triage report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_CONFIG_VERSION = (
    "research-source-resolution-evidence-gap-triage-report-v0"
)
RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_source_resolution_evidence_gap_triage_empty"
CLEAR_REASON = "resolution_evidence_gap_clear"
LOW_SOURCE_AUTHORITY_WATCH_REASON = "low_source_authority_watch"
LOW_SOURCE_AUTHORITY_BLOCK_REASON = "low_source_authority_block"
STALE_EVIDENCE_WATCH_REASON = "stale_evidence_watch"
STALE_EVIDENCE_BLOCK_REASON = "stale_evidence_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
LOW_CORROBORATION_WATCH_REASON = "low_corroboration_watch"
LOW_CORROBORATION_BLOCK_REASON = "low_corroboration_block"
LOW_EXTRACTION_CONFIDENCE_WATCH_REASON = "low_extraction_confidence_watch"
LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON = "low_extraction_confidence_block"
MISSING_CRITICAL_FIELDS_WATCH_REASON = "missing_critical_fields_watch"
MISSING_CRITICAL_FIELDS_BLOCK_REASON = "missing_critical_fields_block"
DEADLINE_PROXIMITY_WATCH_REASON = "deadline_proximity_watch"
DEADLINE_PROXIMITY_BLOCK_REASON = "deadline_proximity_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    LOW_SOURCE_AUTHORITY_BLOCK_REASON,
    STALE_EVIDENCE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    LOW_CORROBORATION_BLOCK_REASON,
    LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
    MISSING_CRITICAL_FIELDS_BLOCK_REASON,
    DEADLINE_PROXIMITY_BLOCK_REASON,
    LOW_SOURCE_AUTHORITY_WATCH_REASON,
    STALE_EVIDENCE_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    LOW_CORROBORATION_WATCH_REASON,
    LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
    MISSING_CRITICAL_FIELDS_WATCH_REASON,
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
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SHA256_HEX_LENGTH = 64


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceGapTriageConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_CONFIG_VERSION
    )
    min_source_authority_score: Decimal = Decimal("0.800000")
    block_source_authority_score: Decimal = Decimal("0.500000")
    freshness_watch_age_seconds: Decimal = Decimal("3600.000000")
    freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    contradiction_watch_pressure: Decimal = Decimal("0.300000")
    contradiction_block_pressure: Decimal = Decimal("0.600000")
    min_corroboration_depth: Decimal = Decimal("2.000000")
    block_corroboration_depth: Decimal = Decimal("1.000000")
    min_extraction_confidence: Decimal = Decimal("0.800000")
    block_extraction_confidence: Decimal = Decimal("0.500000")
    critical_field_watch_missing_count: Decimal = Decimal("1.000000")
    critical_field_block_missing_count: Decimal = Decimal("2.000000")
    deadline_watch_proximity_seconds: Decimal = Decimal("43200.000000")
    deadline_block_proximity_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceGapTriageConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceResolutionEvidenceGapTriageConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_source_authority_score",
            "block_source_authority_score",
            "contradiction_watch_pressure",
            "contradiction_block_pressure",
            "min_extraction_confidence",
            "block_extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
            "min_corroboration_depth",
            "block_corroboration_depth",
            "deadline_watch_proximity_seconds",
            "deadline_block_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "critical_field_watch_missing_count",
            "critical_field_block_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceGapTriageInput:
    resolution_bucket: str
    evidence_family: str
    evidence_observed_at: datetime
    resolution_deadline_at: datetime
    source_authority_score: Decimal
    contradiction_pressure: Decimal
    corroboration_depth: Decimal
    extraction_confidence: Decimal
    missing_critical_field_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceGapTriageInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resolution_bucket",
            _require_public_label("resolution_bucket", self.resolution_bucket),
        )
        object.__setattr__(
            self,
            "evidence_family",
            _require_public_label("evidence_family", self.evidence_family),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "corroboration_depth",
            "missing_critical_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceGapTriageRow:
    resolution_bucket: str
    evidence_count: Decimal
    evidence_family_count: Decimal
    latest_evidence_age_seconds: Decimal
    average_evidence_age_seconds: Decimal
    average_source_authority_score: Decimal
    contradiction_pressure: Decimal
    corroboration_depth: Decimal
    minimum_extraction_confidence: Decimal
    missing_critical_field_count: Decimal
    deadline_proximity_seconds: Decimal
    evidence_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceGapTriageRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceResolutionEvidenceGapTriageRow)
        object.__setattr__(
            self,
            "resolution_bucket",
            _require_public_label("resolution_bucket", self.resolution_bucket),
        )
        for field_name in (
            "evidence_count",
            "evidence_family_count",
            "latest_evidence_age_seconds",
            "average_evidence_age_seconds",
            "corroboration_depth",
            "missing_critical_field_count",
            "deadline_proximity_seconds",
            "evidence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_authority_score",
            "contradiction_pressure",
            "minimum_extraction_confidence",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("evidence gap triage row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceGapTriageReport:
    generated_at: datetime
    config_version: str
    resolution_bucket_count: Decimal
    evidence_count: Decimal
    pass_resolution_bucket_count: Decimal
    watch_resolution_bucket_count: Decimal
    block_resolution_bucket_count: Decimal
    low_source_authority_count: Decimal
    stale_evidence_count: Decimal
    contradiction_pressure_count: Decimal
    low_corroboration_count: Decimal
    low_extraction_confidence_count: Decimal
    missing_critical_fields_count: Decimal
    deadline_pressure_count: Decimal
    highest_evidence_gap_score: Decimal
    nearest_deadline_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceGapTriageReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceResolutionEvidenceGapTriageReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "resolution_bucket_count",
            "evidence_count",
            "pass_resolution_bucket_count",
            "watch_resolution_bucket_count",
            "block_resolution_bucket_count",
            "low_source_authority_count",
            "stale_evidence_count",
            "contradiction_pressure_count",
            "low_corroboration_count",
            "low_extraction_confidence_count",
            "missing_critical_fields_count",
            "deadline_pressure_count",
            "highest_evidence_gap_score",
            "nearest_deadline_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        require_paper_only_flags("evidence gap triage report", self)
        _reject_unsafe_public_surface("report", self)
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


def build_research_source_resolution_evidence_gap_triage_report(
    inputs: list[ResearchSourceResolutionEvidenceGapTriageInput]
    | tuple[ResearchSourceResolutionEvidenceGapTriageInput, ...],
    *,
    config: ResearchSourceResolutionEvidenceGapTriageConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionEvidenceGapTriageReport:
    """Build a deterministic report-only source-resolution evidence gap snapshot."""

    if type(config) is not ResearchSourceResolutionEvidenceGapTriageConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionEvidenceGapTriageConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _evidence_gap_rows(
        _normalize_inputs(inputs, generated_at=generated_at_utc),
        config=config,
        generated_at=generated_at_utc,
    )
    return ResearchSourceResolutionEvidenceGapTriageReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        resolution_bucket_count=_count(len(rows)),
        evidence_count=_sum_rows(rows, "evidence_count"),
        pass_resolution_bucket_count=_status_count(rows, "pass"),
        watch_resolution_bucket_count=_status_count(rows, "watch"),
        block_resolution_bucket_count=_status_count(rows, "block"),
        low_source_authority_count=_reason_count(
            rows,
            (LOW_SOURCE_AUTHORITY_WATCH_REASON, LOW_SOURCE_AUTHORITY_BLOCK_REASON),
        ),
        stale_evidence_count=_reason_count(
            rows,
            (STALE_EVIDENCE_WATCH_REASON, STALE_EVIDENCE_BLOCK_REASON),
        ),
        contradiction_pressure_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        low_corroboration_count=_reason_count(
            rows,
            (LOW_CORROBORATION_WATCH_REASON, LOW_CORROBORATION_BLOCK_REASON),
        ),
        low_extraction_confidence_count=_reason_count(
            rows,
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        missing_critical_fields_count=_reason_count(
            rows,
            (MISSING_CRITICAL_FIELDS_WATCH_REASON, MISSING_CRITICAL_FIELDS_BLOCK_REASON),
        ),
        deadline_pressure_count=_reason_count(
            rows,
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
        highest_evidence_gap_score=max(
            (row.evidence_gap_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        nearest_deadline_seconds=min(
            (row.deadline_proximity_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_resolution_evidence_gap_triage_report_payload(
    report: ResearchSourceResolutionEvidenceGapTriageReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceResolutionEvidenceGapTriageReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionEvidenceGapTriageReport",
        )
    validate_research_source_resolution_evidence_gap_triage_report_digest(report)
    require_paper_only_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("payload", payload)
    return payload


def research_source_resolution_evidence_gap_triage_report_digest(
    report: ResearchSourceResolutionEvidenceGapTriageReport,
) -> str:
    if type(report) is not ResearchSourceResolutionEvidenceGapTriageReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionEvidenceGapTriageReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_source_resolution_evidence_gap_triage_report_digest(
    report: ResearchSourceResolutionEvidenceGapTriageReport,
) -> None:
    if type(report) is not ResearchSourceResolutionEvidenceGapTriageReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionEvidenceGapTriageReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceResolutionEvidenceGapTriageInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceResolutionEvidenceGapTriageInput:
            raise ValueError(
                "inputs must contain ResearchSourceResolutionEvidenceGapTriageInput",
            )
        require_paper_only_flags("input", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be in the future")
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.resolution_bucket,
                row.evidence_family,
                row.evidence_observed_at,
                row.resolution_deadline_at,
            ),
        ),
    )


def _evidence_gap_rows(
    inputs: tuple[ResearchSourceResolutionEvidenceGapTriageInput, ...],
    *,
    config: ResearchSourceResolutionEvidenceGapTriageConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...]:
    grouped: dict[str, list[ResearchSourceResolutionEvidenceGapTriageInput]] = {}
    for row in inputs:
        grouped.setdefault(row.resolution_bucket, []).append(row)
    return tuple(
        sorted(
            (
                _evidence_gap_row(
                    bucket_rows=tuple(bucket_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for bucket_rows in grouped.values()
            ),
            key=_row_sort_key,
        ),
    )


def _evidence_gap_row(
    *,
    bucket_rows: tuple[ResearchSourceResolutionEvidenceGapTriageInput, ...],
    config: ResearchSourceResolutionEvidenceGapTriageConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionEvidenceGapTriageRow:
    ages = tuple(_age_seconds(generated_at, row.evidence_observed_at) for row in bucket_rows)
    deadline_proximities = tuple(
        _deadline_seconds(generated_at, row.resolution_deadline_at) for row in bucket_rows
    )
    evidence_count = _count(len(bucket_rows))
    evidence_family_count = _count(len({row.evidence_family for row in bucket_rows}))
    latest_age = min(ages, default=ZERO).quantize(QUANT)
    average_age = _average(ages)
    average_source_authority = _average(
        tuple(row.source_authority_score for row in bucket_rows),
    )
    contradiction_pressure = max(
        (row.contradiction_pressure for row in bucket_rows),
        default=ZERO,
    ).quantize(QUANT)
    corroboration_depth = min(
        (row.corroboration_depth for row in bucket_rows),
        default=ZERO,
    ).quantize(QUANT)
    minimum_extraction_confidence = min(
        (row.extraction_confidence for row in bucket_rows),
        default=ZERO,
    ).quantize(QUANT)
    missing_critical_field_count = max(
        (row.missing_critical_field_count for row in bucket_rows),
        default=ZERO,
    ).quantize(QUANT)
    deadline_proximity_seconds = min(deadline_proximities, default=ZERO).quantize(QUANT)
    reason_codes = _row_reason_codes(
        latest_evidence_age_seconds=latest_age,
        average_source_authority_score=average_source_authority,
        contradiction_pressure=contradiction_pressure,
        corroboration_depth=corroboration_depth,
        minimum_extraction_confidence=minimum_extraction_confidence,
        missing_critical_field_count=missing_critical_field_count,
        deadline_proximity_seconds=deadline_proximity_seconds,
        config=config,
    )
    return ResearchSourceResolutionEvidenceGapTriageRow(
        resolution_bucket=bucket_rows[0].resolution_bucket,
        evidence_count=evidence_count,
        evidence_family_count=evidence_family_count,
        latest_evidence_age_seconds=latest_age,
        average_evidence_age_seconds=average_age,
        average_source_authority_score=average_source_authority,
        contradiction_pressure=contradiction_pressure,
        corroboration_depth=corroboration_depth,
        minimum_extraction_confidence=minimum_extraction_confidence,
        missing_critical_field_count=missing_critical_field_count,
        deadline_proximity_seconds=deadline_proximity_seconds,
        evidence_gap_score=_evidence_gap_score(
            latest_evidence_age_seconds=latest_age,
            average_source_authority_score=average_source_authority,
            contradiction_pressure=contradiction_pressure,
            corroboration_depth=corroboration_depth,
            minimum_extraction_confidence=minimum_extraction_confidence,
            missing_critical_field_count=missing_critical_field_count,
            deadline_proximity_seconds=deadline_proximity_seconds,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    latest_evidence_age_seconds: Decimal,
    average_source_authority_score: Decimal,
    contradiction_pressure: Decimal,
    corroboration_depth: Decimal,
    minimum_extraction_confidence: Decimal,
    missing_critical_field_count: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchSourceResolutionEvidenceGapTriageConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if average_source_authority_score <= config.block_source_authority_score:
        reasons.append(LOW_SOURCE_AUTHORITY_BLOCK_REASON)
    elif average_source_authority_score < config.min_source_authority_score:
        reasons.append(LOW_SOURCE_AUTHORITY_WATCH_REASON)
    if latest_evidence_age_seconds >= config.freshness_block_age_seconds:
        reasons.append(STALE_EVIDENCE_BLOCK_REASON)
    elif latest_evidence_age_seconds > config.freshness_watch_age_seconds:
        reasons.append(STALE_EVIDENCE_WATCH_REASON)
    if contradiction_pressure >= config.contradiction_block_pressure:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif contradiction_pressure >= config.contradiction_watch_pressure:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if corroboration_depth <= config.block_corroboration_depth:
        reasons.append(LOW_CORROBORATION_BLOCK_REASON)
    elif corroboration_depth < config.min_corroboration_depth:
        reasons.append(LOW_CORROBORATION_WATCH_REASON)
    if minimum_extraction_confidence <= config.block_extraction_confidence:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON)
    elif minimum_extraction_confidence < config.min_extraction_confidence:
        reasons.append(LOW_EXTRACTION_CONFIDENCE_WATCH_REASON)
    if missing_critical_field_count >= config.critical_field_block_missing_count:
        reasons.append(MISSING_CRITICAL_FIELDS_BLOCK_REASON)
    elif missing_critical_field_count >= config.critical_field_watch_missing_count:
        reasons.append(MISSING_CRITICAL_FIELDS_WATCH_REASON)
    if deadline_proximity_seconds <= config.deadline_block_proximity_seconds:
        reasons.append(DEADLINE_PROXIMITY_BLOCK_REASON)
    elif deadline_proximity_seconds <= config.deadline_watch_proximity_seconds:
        reasons.append(DEADLINE_PROXIMITY_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _evidence_gap_score(
    *,
    latest_evidence_age_seconds: Decimal,
    average_source_authority_score: Decimal,
    contradiction_pressure: Decimal,
    corroboration_depth: Decimal,
    minimum_extraction_confidence: Decimal,
    missing_critical_field_count: Decimal,
    deadline_proximity_seconds: Decimal,
    config: ResearchSourceResolutionEvidenceGapTriageConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        source_authority_gap = ONE - average_source_authority_score
        freshness_pressure = min(
            latest_evidence_age_seconds / config.freshness_block_age_seconds,
            ONE,
        )
        corroboration_gap = max(
            (config.min_corroboration_depth - corroboration_depth)
            / config.min_corroboration_depth,
            ZERO,
        )
        extraction_gap = ONE - minimum_extraction_confidence
        if config.critical_field_block_missing_count == ZERO:
            missing_field_pressure = ONE if missing_critical_field_count > ZERO else ZERO
        else:
            missing_field_pressure = min(
                missing_critical_field_count / config.critical_field_block_missing_count,
                ONE,
            )
        deadline_pressure = max(
            ONE - (deadline_proximity_seconds / config.deadline_watch_proximity_seconds),
            ZERO,
        )
        score = (
            source_authority_gap
            + freshness_pressure
            + contradiction_pressure
            + corroboration_gap
            + extraction_gap
            + missing_field_pressure
            + deadline_pressure
        ) / Decimal("7.000000")
        return score.quantize(QUANT)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...],
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


def _row_sort_key(row: ResearchSourceResolutionEvidenceGapTriageRow) -> tuple[Decimal, str]:
    return (-row.evidence_gap_score, row.resolution_bucket)


def _status_count(
    rows: tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _sum_rows(
    rows: tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...],
    field_name: str,
) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), ZERO).quantize(QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANT)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at_utc = _as_utc("evidence_observed_at", observed_at)
    delta = generated_at_utc - observed_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("evidence_observed_at must not be in the future")
    return seconds.quantize(QUANT)


def _deadline_seconds(generated_at: datetime, deadline_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    deadline_at_utc = _as_utc("resolution_deadline_at", deadline_at)
    delta = deadline_at_utc - generated_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return max(seconds, ZERO).quantize(QUANT)


def _validate_config(config: ResearchSourceResolutionEvidenceGapTriageConfig) -> None:
    if config.block_source_authority_score >= config.min_source_authority_score:
        raise ValueError(
            "block_source_authority_score must be below min_source_authority_score",
        )
    if config.freshness_watch_age_seconds >= config.freshness_block_age_seconds:
        raise ValueError(
            "freshness_watch_age_seconds must be below freshness_block_age_seconds",
        )
    if config.contradiction_watch_pressure > config.contradiction_block_pressure:
        raise ValueError(
            "contradiction_watch_pressure must not exceed contradiction_block_pressure",
        )
    if config.block_corroboration_depth > config.min_corroboration_depth:
        raise ValueError(
            "block_corroboration_depth must not exceed min_corroboration_depth",
        )
    if config.block_extraction_confidence >= config.min_extraction_confidence:
        raise ValueError(
            "block_extraction_confidence must be below min_extraction_confidence",
        )
    if (
        config.critical_field_watch_missing_count
        > config.critical_field_block_missing_count
    ):
        raise ValueError(
            "critical_field_watch_missing_count must not exceed "
            "critical_field_block_missing_count",
        )
    if config.deadline_block_proximity_seconds > config.deadline_watch_proximity_seconds:
        raise ValueError(
            "deadline_block_proximity_seconds must not exceed "
            "deadline_watch_proximity_seconds",
        )


def _validate_row(row: ResearchSourceResolutionEvidenceGapTriageRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.evidence_family_count <= ZERO:
        raise ValueError("evidence_family_count must be positive")
    if row.latest_evidence_age_seconds > row.average_evidence_age_seconds:
        raise ValueError("latest_evidence_age_seconds must not exceed average")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must be clear")


def _validate_report(report: ResearchSourceResolutionEvidenceGapTriageReport) -> None:
    if report.resolution_bucket_count != _count(len(report.rows)):
        raise ValueError("resolution_bucket_count must match rows")
    if report.evidence_count != _sum_rows(report.rows, "evidence_count"):
        raise ValueError("evidence_count must match rows")
    for status, field_name in (
        ("pass", "pass_resolution_bucket_count"),
        ("watch", "watch_resolution_bucket_count"),
        ("block", "block_resolution_bucket_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "low_source_authority_count",
            (LOW_SOURCE_AUTHORITY_WATCH_REASON, LOW_SOURCE_AUTHORITY_BLOCK_REASON),
        ),
        (
            "stale_evidence_count",
            (STALE_EVIDENCE_WATCH_REASON, STALE_EVIDENCE_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        (
            "low_corroboration_count",
            (LOW_CORROBORATION_WATCH_REASON, LOW_CORROBORATION_BLOCK_REASON),
        ),
        (
            "low_extraction_confidence_count",
            (
                LOW_EXTRACTION_CONFIDENCE_WATCH_REASON,
                LOW_EXTRACTION_CONFIDENCE_BLOCK_REASON,
            ),
        ),
        (
            "missing_critical_fields_count",
            (MISSING_CRITICAL_FIELDS_WATCH_REASON, MISSING_CRITICAL_FIELDS_BLOCK_REASON),
        ),
        (
            "deadline_pressure_count",
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_evidence_gap_score != max(
        (row.evidence_gap_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_evidence_gap_score must match rows")
    if report.nearest_deadline_seconds != min(
        (row.deadline_proximity_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("nearest_deadline_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic evidence gap sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceResolutionEvidenceGapTriageRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceResolutionEvidenceGapTriageRow:
            raise ValueError(
                "rows must contain ResearchSourceResolutionEvidenceGapTriageRow",
            )
        require_paper_only_flags("evidence gap triage row", row)
        if row.resolution_bucket in seen:
            raise ValueError("rows must be unique by resolution_bucket")
        seen.add(row.resolution_bucket)
    return tuple(sorted(rows, key=_row_sort_key))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


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
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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
        or value not in RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
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
        "live",
        "market",
        "private",
        "question",
        "secret",
        "slug",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
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


def _report_digest_from_public_payload(
    report: ResearchSourceResolutionEvidenceGapTriageReport,
) -> str:
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("payload", payload)
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


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(label: str, key: str) -> None:
    lowered = key.lower()
    unsafe_fragments = (
        "raw_candidate",
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "market_question",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{label} contains unsafe public field")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    unsafe_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_",
        "market-",
        "market_",
        "question",
        "slug",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{label} contains unsafe public text")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_STATUSES",
    "ResearchSourceResolutionEvidenceGapTriageConfig",
    "ResearchSourceResolutionEvidenceGapTriageInput",
    "ResearchSourceResolutionEvidenceGapTriageReport",
    "ResearchSourceResolutionEvidenceGapTriageRow",
    "build_research_source_resolution_evidence_gap_triage_report",
    "research_source_resolution_evidence_gap_triage_report_digest",
    "research_source_resolution_evidence_gap_triage_report_payload",
    "validate_research_source_resolution_evidence_gap_triage_report_digest",
)
