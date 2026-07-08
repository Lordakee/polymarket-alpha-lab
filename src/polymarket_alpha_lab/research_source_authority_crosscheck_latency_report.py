"""Pure in-memory source authority cross-check latency report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_REPORT_CONFIG_VERSION = (
    "research-source-authority-crosscheck-latency-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_authority_crosscheck_latency_empty"
HEALTHY_REASON = "source_authority_crosscheck_latency_healthy"
LOW_AUTHORITY_WATCH_REASON = "low_authority_watch"
LOW_AUTHORITY_BLOCK_REASON = "low_authority_block"
LATE_AUTHORITATIVE_WATCH_REASON = "late_authoritative_crosscheck_watch"
LATE_AUTHORITATIVE_BLOCK_REASON = "late_authoritative_crosscheck_block"
THIN_CORROBORATION_WATCH_REASON = "thin_corroboration_watch"
THIN_CORROBORATION_BLOCK_REASON = "thin_corroboration_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "contradiction_pressure_block"
STALE_CROSSCHECK_WATCH_REASON = "stale_crosscheck_watch"
STALE_CROSSCHECK_BLOCK_REASON = "stale_crosscheck_block"
DEADLINE_PROXIMITY_WATCH_REASON = "deadline_proximity_watch"
DEADLINE_PROXIMITY_BLOCK_REASON = "deadline_proximity_block"

ROW_REASON_CODES = (
    HEALTHY_REASON,
    LOW_AUTHORITY_BLOCK_REASON,
    LATE_AUTHORITATIVE_BLOCK_REASON,
    THIN_CORROBORATION_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    STALE_CROSSCHECK_BLOCK_REASON,
    DEADLINE_PROXIMITY_BLOCK_REASON,
    LOW_AUTHORITY_WATCH_REASON,
    LATE_AUTHORITATIVE_WATCH_REASON,
    THIN_CORROBORATION_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    STALE_CROSSCHECK_WATCH_REASON,
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


@dataclass(frozen=True)
class ResearchSourceAuthorityCrosscheckLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_REPORT_CONFIG_VERSION
    )
    target_high_rank_latency_seconds: Decimal = Decimal("900.000000")
    max_high_rank_latency_seconds: Decimal = Decimal("1800.000000")
    freshness_watch_age_seconds: Decimal = Decimal("1800.000000")
    freshness_block_age_seconds: Decimal = Decimal("3600.000000")
    deadline_watch_seconds_remaining: Decimal = Decimal("1800.000000")
    deadline_block_seconds_remaining: Decimal = Decimal("600.000000")
    high_source_rank_threshold: Decimal = Decimal("0.800000")
    source_rank_watch_threshold: Decimal = Decimal("0.550000")
    source_rank_block_threshold: Decimal = Decimal("0.350000")
    corroboration_watch_threshold: Decimal = Decimal("0.600000")
    corroboration_block_threshold: Decimal = Decimal("0.400000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityCrosscheckLatencyConfig:
            raise TypeError(
                "ResearchSourceAuthorityCrosscheckLatencyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityCrosscheckLatencyConfig:
            raise ValueError(
                "config must be exactly ResearchSourceAuthorityCrosscheckLatencyConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "target_high_rank_latency_seconds",
            "max_high_rank_latency_seconds",
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
            "high_source_rank_threshold",
            "source_rank_watch_threshold",
            "source_rank_block_threshold",
            "corroboration_watch_threshold",
            "corroboration_block_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityCrosscheckLatencyInput:
    source_family: str
    source_rank_score: Decimal
    crosscheck_latency_seconds: Decimal
    corroboration_score: Decimal
    contradiction_pressure_score: Decimal
    evidence_freshness_seconds: Decimal
    deadline_seconds_remaining: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityCrosscheckLatencyInput:
            raise TypeError(
                "ResearchSourceAuthorityCrosscheckLatencyInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityCrosscheckLatencyInput:
            raise ValueError(
                "input must be exactly ResearchSourceAuthorityCrosscheckLatencyInput",
            )
        object.__setattr__(
            self,
            "source_family",
            _require_public_source_family("source_family", self.source_family),
        )
        for field_name in (
            "source_rank_score",
            "corroboration_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "crosscheck_latency_seconds",
            "evidence_freshness_seconds",
            "deadline_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityCrosscheckLatencyRow:
    source_family: str
    source_rank_score: Decimal
    source_rank_band: str
    crosscheck_latency_seconds: Decimal
    latency_band: str
    latency_pressure_score: Decimal
    corroboration_score: Decimal
    contradiction_pressure_score: Decimal
    evidence_freshness_seconds: Decimal
    freshness_band: str
    deadline_seconds_remaining: Decimal
    deadline_proximity_band: str
    deadline_pressure_score: Decimal
    crosscheck_latency_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityCrosscheckLatencyRow:
            raise TypeError(
                "ResearchSourceAuthorityCrosscheckLatencyRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityCrosscheckLatencyRow:
            raise ValueError("row must be exactly ResearchSourceAuthorityCrosscheckLatencyRow")
        object.__setattr__(
            self,
            "source_family",
            _require_public_source_family("source_family", self.source_family),
        )
        for field_name in (
            "source_rank_score",
            "latency_pressure_score",
            "corroboration_score",
            "contradiction_pressure_score",
            "deadline_pressure_score",
            "crosscheck_latency_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "crosscheck_latency_seconds",
            "evidence_freshness_seconds",
            "deadline_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_source_rank_band("source_rank_band", self.source_rank_band)
        _require_latency_band("latency_band", self.latency_band)
        _require_freshness_band("freshness_band", self.freshness_band)
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
class ResearchSourceAuthorityCrosscheckLatencyReport:
    generated_at: datetime
    config_version: str
    source_family_count: Decimal
    pass_source_family_count: Decimal
    watch_source_family_count: Decimal
    block_source_family_count: Decimal
    low_source_rank_count: Decimal
    late_high_rank_source_count: Decimal
    thin_corroboration_source_count: Decimal
    contradiction_pressure_source_count: Decimal
    stale_crosscheck_source_count: Decimal
    deadline_proximity_source_count: Decimal
    highest_crosscheck_latency_risk_score: Decimal
    slowest_crosscheck_latency_seconds: Decimal
    lowest_source_rank_score: Decimal
    lowest_corroboration_score: Decimal
    highest_contradiction_pressure_score: Decimal
    nearest_deadline_seconds_remaining: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAuthorityCrosscheckLatencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityCrosscheckLatencyReport:
            raise TypeError(
                "ResearchSourceAuthorityCrosscheckLatencyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityCrosscheckLatencyReport:
            raise ValueError(
                "report must be exactly ResearchSourceAuthorityCrosscheckLatencyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_family_count",
            "pass_source_family_count",
            "watch_source_family_count",
            "block_source_family_count",
            "low_source_rank_count",
            "late_high_rank_source_count",
            "thin_corroboration_source_count",
            "contradiction_pressure_source_count",
            "stale_crosscheck_source_count",
            "deadline_proximity_source_count",
            "slowest_crosscheck_latency_seconds",
            "nearest_deadline_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_crosscheck_latency_risk_score",
            "lowest_source_rank_score",
            "lowest_corroboration_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("source authority crosscheck latency report", self)
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


def build_research_source_authority_crosscheck_latency_report(
    inputs: list[ResearchSourceAuthorityCrosscheckLatencyInput]
    | tuple[ResearchSourceAuthorityCrosscheckLatencyInput, ...],
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityCrosscheckLatencyReport:
    if type(config) is not ResearchSourceAuthorityCrosscheckLatencyConfig:
        raise ValueError("config must be a ResearchSourceAuthorityCrosscheckLatencyConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _latency_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceAuthorityCrosscheckLatencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_family_count=_count(len(rows)),
        pass_source_family_count=_status_count(rows, "pass"),
        watch_source_family_count=_status_count(rows, "watch"),
        block_source_family_count=_status_count(rows, "block"),
        low_source_rank_count=_reason_count(
            rows,
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        late_high_rank_source_count=_reason_count(
            rows,
            (LATE_AUTHORITATIVE_WATCH_REASON, LATE_AUTHORITATIVE_BLOCK_REASON),
        ),
        thin_corroboration_source_count=_reason_count(
            rows,
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        contradiction_pressure_source_count=_reason_count(
            rows,
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        stale_crosscheck_source_count=_reason_count(
            rows,
            (STALE_CROSSCHECK_WATCH_REASON, STALE_CROSSCHECK_BLOCK_REASON),
        ),
        deadline_proximity_source_count=_reason_count(
            rows,
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
        highest_crosscheck_latency_risk_score=max(
            (row.crosscheck_latency_risk_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        slowest_crosscheck_latency_seconds=max(
            (row.crosscheck_latency_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_source_rank_score=min(
            (row.source_rank_score for row in rows),
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
        nearest_deadline_seconds_remaining=min(
            (row.deadline_seconds_remaining for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_authority_crosscheck_latency_report_payload(
    report: ResearchSourceAuthorityCrosscheckLatencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityCrosscheckLatencyReport:
        raise ValueError("report must be a ResearchSourceAuthorityCrosscheckLatencyReport")
    validate_research_source_authority_crosscheck_latency_report_digest(report)
    reject_unsafe_surface_fields("source authority crosscheck latency report", report)
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_source_authority_crosscheck_latency_report_digest(
    report: ResearchSourceAuthorityCrosscheckLatencyReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityCrosscheckLatencyReport:
        raise ValueError("report must be a ResearchSourceAuthorityCrosscheckLatencyReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_crosscheck_latency_report_digest(
    report: ResearchSourceAuthorityCrosscheckLatencyReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityCrosscheckLatencyReport:
        raise ValueError("report must be a ResearchSourceAuthorityCrosscheckLatencyReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityCrosscheckLatencyInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityCrosscheckLatencyInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityCrosscheckLatencyInput",
            )
        require_paper_only_flags("input", row)
        if row.source_family in seen:
            raise ValueError("inputs must be unique by source_family")
        seen.add(row.source_family)
    return tuple(sorted(rows, key=lambda row: row.source_family))


def _latency_rows(
    inputs: tuple[ResearchSourceAuthorityCrosscheckLatencyInput, ...],
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> tuple[ResearchSourceAuthorityCrosscheckLatencyRow, ...]:
    return tuple(sorted((_latency_row(row, config=config) for row in inputs), key=_row_sort_key))


def _latency_row(
    row: ResearchSourceAuthorityCrosscheckLatencyInput,
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> ResearchSourceAuthorityCrosscheckLatencyRow:
    reason_codes = _row_reason_codes(row, config=config)
    latency_pressure_score = _latency_pressure_score(
        row.crosscheck_latency_seconds,
        source_rank_score=row.source_rank_score,
        config=config,
    )
    deadline_pressure_score = _deadline_pressure_score(
        row.deadline_seconds_remaining,
        config=config,
    )
    return ResearchSourceAuthorityCrosscheckLatencyRow(
        source_family=row.source_family,
        source_rank_score=row.source_rank_score,
        source_rank_band=_source_rank_band(row.source_rank_score, config=config),
        crosscheck_latency_seconds=row.crosscheck_latency_seconds,
        latency_band=_latency_band(row.crosscheck_latency_seconds, config=config),
        latency_pressure_score=latency_pressure_score,
        corroboration_score=row.corroboration_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        evidence_freshness_seconds=row.evidence_freshness_seconds,
        freshness_band=_freshness_band(row.evidence_freshness_seconds, config=config),
        deadline_seconds_remaining=row.deadline_seconds_remaining,
        deadline_proximity_band=_deadline_proximity_band(
            row.deadline_seconds_remaining,
            config=config,
        ),
        deadline_pressure_score=deadline_pressure_score,
        crosscheck_latency_risk_score=_crosscheck_latency_risk_score(
            row,
            latency_pressure_score=latency_pressure_score,
            deadline_pressure_score=deadline_pressure_score,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchSourceAuthorityCrosscheckLatencyInput,
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.source_rank_score <= config.source_rank_block_threshold:
        reasons.append(LOW_AUTHORITY_BLOCK_REASON)
    elif row.source_rank_score < config.source_rank_watch_threshold:
        reasons.append(LOW_AUTHORITY_WATCH_REASON)
    if row.source_rank_score >= config.high_source_rank_threshold:
        if row.crosscheck_latency_seconds >= config.max_high_rank_latency_seconds:
            reasons.append(LATE_AUTHORITATIVE_BLOCK_REASON)
        elif row.crosscheck_latency_seconds > config.target_high_rank_latency_seconds:
            reasons.append(LATE_AUTHORITATIVE_WATCH_REASON)
    if row.corroboration_score <= config.corroboration_block_threshold:
        reasons.append(THIN_CORROBORATION_BLOCK_REASON)
    elif row.corroboration_score < config.corroboration_watch_threshold:
        reasons.append(THIN_CORROBORATION_WATCH_REASON)
    if row.contradiction_pressure_score >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if row.evidence_freshness_seconds >= config.freshness_block_age_seconds:
        reasons.append(STALE_CROSSCHECK_BLOCK_REASON)
    elif row.evidence_freshness_seconds > config.freshness_watch_age_seconds:
        reasons.append(STALE_CROSSCHECK_WATCH_REASON)
    if row.deadline_seconds_remaining <= config.deadline_block_seconds_remaining:
        reasons.append(DEADLINE_PROXIMITY_BLOCK_REASON)
    elif row.deadline_seconds_remaining < config.deadline_watch_seconds_remaining:
        reasons.append(DEADLINE_PROXIMITY_WATCH_REASON)
    if not reasons:
        reasons.append(HEALTHY_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _crosscheck_latency_risk_score(
    row: ResearchSourceAuthorityCrosscheckLatencyInput,
    *,
    latency_pressure_score: Decimal,
    deadline_pressure_score: Decimal,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        source_rank_gap = ONE - row.source_rank_score
        corroboration_gap = ONE - row.corroboration_score
        freshness_pressure = min(
            row.evidence_freshness_seconds / config.freshness_block_age_seconds,
            ONE,
        )
        score = (
            source_rank_gap * Decimal("0.200000")
            + latency_pressure_score * Decimal("0.250000")
            + corroboration_gap * Decimal("0.175000")
            + row.contradiction_pressure_score * Decimal("0.200000")
            + freshness_pressure * Decimal("0.100000")
            + deadline_pressure_score * Decimal("0.075000")
        )
        return min(score, ONE).quantize(QUANT)


def _latency_pressure_score(
    value: Decimal,
    *,
    source_rank_score: Decimal,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        pressure = min(value / config.max_high_rank_latency_seconds, ONE)
        source_rank_weight = Decimal("0.500000") + (source_rank_score / Decimal("2"))
        return (pressure * source_rank_weight).quantize(QUANT)


def _deadline_pressure_score(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        open_fraction = min(value / config.deadline_watch_seconds_remaining, ONE)
        return (ONE - open_fraction).quantize(QUANT)


def _source_rank_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> str:
    if value >= config.high_source_rank_threshold:
        return "high"
    if value < config.source_rank_watch_threshold:
        return "low"
    return "medium"


def _latency_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> str:
    if value <= config.target_high_rank_latency_seconds:
        return "fast"
    if value < config.max_high_rank_latency_seconds:
        return "late"
    return "critical"


def _freshness_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
) -> str:
    if value <= config.freshness_watch_age_seconds:
        return "fresh"
    if value < config.freshness_block_age_seconds:
        return "aging"
    return "stale"


def _deadline_proximity_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityCrosscheckLatencyConfig,
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


def _report_status(rows: tuple[ResearchSourceAuthorityCrosscheckLatencyRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityCrosscheckLatencyRow, ...],
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


def _row_sort_key(row: ResearchSourceAuthorityCrosscheckLatencyRow) -> tuple[Decimal, str]:
    return (-row.crosscheck_latency_risk_score, row.source_family)


def _status_count(
    rows: tuple[ResearchSourceAuthorityCrosscheckLatencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityCrosscheckLatencyRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _validate_config(config: ResearchSourceAuthorityCrosscheckLatencyConfig) -> None:
    if config.target_high_rank_latency_seconds > config.max_high_rank_latency_seconds:
        raise ValueError(
            "target_high_rank_latency_seconds must not exceed max_high_rank_latency_seconds",
        )
    if config.freshness_watch_age_seconds >= config.freshness_block_age_seconds:
        raise ValueError("freshness_watch_age_seconds must be less than freshness_block_age_seconds")
    if config.deadline_block_seconds_remaining > config.deadline_watch_seconds_remaining:
        raise ValueError(
            "deadline_block_seconds_remaining must not exceed deadline_watch_seconds_remaining",
        )
    if config.source_rank_block_threshold > config.source_rank_watch_threshold:
        raise ValueError("source_rank_block_threshold must not exceed source_rank_watch_threshold")
    if config.source_rank_watch_threshold > config.high_source_rank_threshold:
        raise ValueError("source_rank_watch_threshold must not exceed high_source_rank_threshold")
    if config.corroboration_block_threshold > config.corroboration_watch_threshold:
        raise ValueError(
            "corroboration_block_threshold must not exceed corroboration_watch_threshold",
        )
    if config.contradiction_watch_threshold > config.contradiction_block_threshold:
        raise ValueError(
            "contradiction_watch_threshold must not exceed contradiction_block_threshold",
        )


def _validate_row(row: ResearchSourceAuthorityCrosscheckLatencyRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (HEALTHY_REASON,):
        raise ValueError("pass rows must be healthy")


def _validate_report(report: ResearchSourceAuthorityCrosscheckLatencyReport) -> None:
    if report.source_family_count != _count(len(report.rows)):
        raise ValueError("source_family_count must match rows")
    for status, field_name in (
        ("pass", "pass_source_family_count"),
        ("watch", "watch_source_family_count"),
        ("block", "block_source_family_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "low_source_rank_count",
            (LOW_AUTHORITY_WATCH_REASON, LOW_AUTHORITY_BLOCK_REASON),
        ),
        (
            "late_high_rank_source_count",
            (LATE_AUTHORITATIVE_WATCH_REASON, LATE_AUTHORITATIVE_BLOCK_REASON),
        ),
        (
            "thin_corroboration_source_count",
            (THIN_CORROBORATION_WATCH_REASON, THIN_CORROBORATION_BLOCK_REASON),
        ),
        (
            "contradiction_pressure_source_count",
            (CONTRADICTION_PRESSURE_WATCH_REASON, CONTRADICTION_PRESSURE_BLOCK_REASON),
        ),
        (
            "stale_crosscheck_source_count",
            (STALE_CROSSCHECK_WATCH_REASON, STALE_CROSSCHECK_BLOCK_REASON),
        ),
        (
            "deadline_proximity_source_count",
            (DEADLINE_PROXIMITY_WATCH_REASON, DEADLINE_PROXIMITY_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_crosscheck_latency_risk_score != max(
        (row.crosscheck_latency_risk_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_crosscheck_latency_risk_score must match rows")
    if report.slowest_crosscheck_latency_seconds != max(
        (row.crosscheck_latency_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("slowest_crosscheck_latency_seconds must match rows")
    if report.lowest_source_rank_score != min(
        (row.source_rank_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_source_rank_score must match rows")
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
        raise ValueError("rows must use deterministic crosscheck latency risk sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityCrosscheckLatencyRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityCrosscheckLatencyRow:
            raise ValueError("rows must contain ResearchSourceAuthorityCrosscheckLatencyRow")
        require_paper_only_flags("row", row)
        if row.source_family in seen:
            raise ValueError("rows must be unique by source_family")
        seen.add(row.source_family)
    return tuple(sorted(rows, key=_row_sort_key))


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
        or value not in RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_source_rank_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("high", "medium", "low"):
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_latency_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fast", "late", "critical"):
        raise ValueError(f"{field_name} must be fast, late, or critical")


def _require_freshness_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fresh", "aging", "stale"):
        raise ValueError(f"{field_name} must be fresh, aging, or stale")


def _require_deadline_proximity_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("open", "near", "immediate"):
        raise ValueError(f"{field_name} must be open, near, or immediate")


def _require_public_source_family(field_name: str, value: object) -> str:
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


def _report_digest_from_public_payload(
    report: ResearchSourceAuthorityCrosscheckLatencyReport,
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


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_CROSSCHECK_LATENCY_STATUSES",
    "ResearchSourceAuthorityCrosscheckLatencyConfig",
    "ResearchSourceAuthorityCrosscheckLatencyInput",
    "ResearchSourceAuthorityCrosscheckLatencyReport",
    "ResearchSourceAuthorityCrosscheckLatencyRow",
    "build_research_source_authority_crosscheck_latency_report",
    "research_source_authority_crosscheck_latency_report_digest",
    "research_source_authority_crosscheck_latency_report_payload",
    "validate_research_source_authority_crosscheck_latency_report_digest",
)
