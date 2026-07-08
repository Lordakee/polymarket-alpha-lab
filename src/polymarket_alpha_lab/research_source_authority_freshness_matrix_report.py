"""Pure in-memory source authority, freshness, and independence matrix report."""

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


DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_REPORT_CONFIG_VERSION = (
    "research-source-authority-freshness-matrix-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_STATUSES = ("pass", "watch", "block")

EMPTY_REASON = "research_source_authority_freshness_matrix_empty"
BALANCED_REASON = "source_authority_freshness_matrix_balanced"
STALE_HIGH_SOURCE_RANK_WATCH_REASON = "stale_high_source_rank_watch"
STALE_HIGH_SOURCE_RANK_BLOCK_REASON = "stale_high_source_rank_block"
LOW_SOURCE_RANK_FAST_UPDATE_WATCH_REASON = "low_source_rank_fast_update_watch"
LOW_SOURCE_RANK_FAST_UPDATE_BLOCK_REASON = "low_source_rank_fast_update_block"
LOW_INDEPENDENCE_WATCH_REASON = "low_independence_watch"
LOW_INDEPENDENCE_BLOCK_REASON = "low_independence_block"
CONTRADICTION_RISK_WATCH_REASON = "contradiction_risk_watch"
CONTRADICTION_RISK_BLOCK_REASON = "contradiction_risk_block"

ROW_REASON_CODES = (
    BALANCED_REASON,
    STALE_HIGH_SOURCE_RANK_BLOCK_REASON,
    LOW_SOURCE_RANK_FAST_UPDATE_BLOCK_REASON,
    LOW_INDEPENDENCE_BLOCK_REASON,
    CONTRADICTION_RISK_BLOCK_REASON,
    STALE_HIGH_SOURCE_RANK_WATCH_REASON,
    LOW_SOURCE_RANK_FAST_UPDATE_WATCH_REASON,
    LOW_INDEPENDENCE_WATCH_REASON,
    CONTRADICTION_RISK_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, BALANCED_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SHA256_HEX_LENGTH = 64


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessMatrixConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_REPORT_CONFIG_VERSION
    )
    fresh_update_age_seconds: Decimal = Decimal("900.000000")
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("7200.000000")
    high_source_rank_threshold: Decimal = Decimal("0.800000")
    low_source_rank_threshold: Decimal = Decimal("0.500000")
    critical_low_source_rank_threshold: Decimal = Decimal("0.300000")
    independence_watch_threshold: Decimal = Decimal("0.700000")
    independence_block_threshold: Decimal = Decimal("0.500000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "fresh_update_age_seconds",
            "fresh_age_seconds",
            "stale_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_source_rank_threshold",
            "low_source_rank_threshold",
            "critical_low_source_rank_threshold",
            "independence_watch_threshold",
            "independence_block_threshold",
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
class ResearchSourceAuthorityFreshnessMatrixInput:
    source_family: str
    evidence_observed_at: datetime
    source_rank_score: Decimal
    independence_score: Decimal
    contradiction_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_family",
            _require_public_source_family("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        for field_name in (
            "source_rank_score",
            "independence_score",
            "contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessMatrixRow:
    source_family: str
    evidence_count: Decimal
    latest_evidence_age_seconds: Decimal
    average_evidence_age_seconds: Decimal
    average_source_rank_score: Decimal
    source_rank_band: str
    freshness_band: str
    average_independence_score: Decimal
    independence_band: str
    contradiction_risk_score: Decimal
    matrix_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_family",
            _require_public_source_family("source_family", self.source_family),
        )
        for field_name in (
            "evidence_count",
            "latest_evidence_age_seconds",
            "average_evidence_age_seconds",
            "matrix_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_rank_score",
            "average_independence_score",
            "contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_source_rank_band("source_rank_band", self.source_rank_band)
        _require_freshness_band("freshness_band", self.freshness_band)
        _require_independence_band("independence_band", self.independence_band)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("matrix row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityFreshnessMatrixReport:
    generated_at: datetime
    config_version: str
    source_family_count: Decimal
    evidence_count: Decimal
    pass_source_family_count: Decimal
    watch_source_family_count: Decimal
    block_source_family_count: Decimal
    stale_high_source_rank_count: Decimal
    low_source_rank_fast_update_count: Decimal
    low_independence_count: Decimal
    contradiction_risk_count: Decimal
    highest_matrix_risk_score: Decimal
    oldest_latest_evidence_age_seconds: Decimal
    lowest_average_source_rank_score: Decimal
    lowest_average_independence_score: Decimal
    highest_contradiction_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_family_count",
            "evidence_count",
            "pass_source_family_count",
            "watch_source_family_count",
            "block_source_family_count",
            "stale_high_source_rank_count",
            "low_source_rank_fast_update_count",
            "low_independence_count",
            "contradiction_risk_count",
            "highest_matrix_risk_score",
            "oldest_latest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lowest_average_source_rank_score",
            "lowest_average_independence_score",
            "highest_contradiction_risk_score",
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
        reject_unsafe_surface_fields("source authority freshness matrix report", self)
        require_paper_only_flags("matrix report", self)
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


def build_research_source_authority_freshness_matrix_report(
    inputs: list[ResearchSourceAuthorityFreshnessMatrixInput]
    | tuple[ResearchSourceAuthorityFreshnessMatrixInput, ...],
    *,
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityFreshnessMatrixReport:
    if type(config) is not ResearchSourceAuthorityFreshnessMatrixConfig:
        raise ValueError("config must be a ResearchSourceAuthorityFreshnessMatrixConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _matrix_rows(
        _normalize_inputs(inputs, generated_at=generated_at_utc),
        config=config,
        generated_at=generated_at_utc,
    )
    return ResearchSourceAuthorityFreshnessMatrixReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_family_count=_count(len(rows)),
        evidence_count=_sum_rows(rows, "evidence_count"),
        pass_source_family_count=_status_count(rows, "pass"),
        watch_source_family_count=_status_count(rows, "watch"),
        block_source_family_count=_status_count(rows, "block"),
        stale_high_source_rank_count=_reason_count(
            rows,
            (
                STALE_HIGH_SOURCE_RANK_WATCH_REASON,
                STALE_HIGH_SOURCE_RANK_BLOCK_REASON,
            ),
        ),
        low_source_rank_fast_update_count=_reason_count(
            rows,
            (
                LOW_SOURCE_RANK_FAST_UPDATE_WATCH_REASON,
                LOW_SOURCE_RANK_FAST_UPDATE_BLOCK_REASON,
            ),
        ),
        low_independence_count=_reason_count(
            rows,
            (LOW_INDEPENDENCE_WATCH_REASON, LOW_INDEPENDENCE_BLOCK_REASON),
        ),
        contradiction_risk_count=_reason_count(
            rows,
            (CONTRADICTION_RISK_WATCH_REASON, CONTRADICTION_RISK_BLOCK_REASON),
        ),
        highest_matrix_risk_score=max(
            (row.matrix_risk_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_latest_evidence_age_seconds=max(
            (row.latest_evidence_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_average_source_rank_score=min(
            (row.average_source_rank_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        lowest_average_independence_score=min(
            (row.average_independence_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_contradiction_risk_score=max(
            (row.contradiction_risk_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_authority_freshness_matrix_report_payload(
    report: ResearchSourceAuthorityFreshnessMatrixReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityFreshnessMatrixReport:
        raise ValueError("report must be a ResearchSourceAuthorityFreshnessMatrixReport")
    validate_research_source_authority_freshness_matrix_report_digest(report)
    reject_unsafe_surface_fields("source authority freshness matrix report", report)
    require_paper_only_flags("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_source_authority_freshness_matrix_report_digest(
    report: ResearchSourceAuthorityFreshnessMatrixReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityFreshnessMatrixReport:
        raise ValueError("report must be a ResearchSourceAuthorityFreshnessMatrixReport")
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_freshness_matrix_report_digest(
    report: ResearchSourceAuthorityFreshnessMatrixReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityFreshnessMatrixReport:
        raise ValueError("report must be a ResearchSourceAuthorityFreshnessMatrixReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceAuthorityFreshnessMatrixInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceAuthorityFreshnessMatrixInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityFreshnessMatrixInput",
            )
        require_paper_only_flags("input", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be in the future")
    return tuple(sorted(rows, key=lambda row: (row.source_family, row.evidence_observed_at)))


def _matrix_rows(
    inputs: tuple[ResearchSourceAuthorityFreshnessMatrixInput, ...],
    *,
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...]:
    grouped: dict[str, list[ResearchSourceAuthorityFreshnessMatrixInput]] = {}
    for row in inputs:
        grouped.setdefault(row.source_family, []).append(row)
    return tuple(
        sorted(
            (
                _matrix_row(
                    family_rows=tuple(family_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for family_rows in grouped.values()
            ),
            key=_row_sort_key,
        ),
    )


def _matrix_row(
    *,
    family_rows: tuple[ResearchSourceAuthorityFreshnessMatrixInput, ...],
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityFreshnessMatrixRow:
    ages = tuple(_age_seconds(generated_at, row.evidence_observed_at) for row in family_rows)
    evidence_count = _count(len(family_rows))
    latest_age = min(ages, default=ZERO).quantize(QUANT)
    average_age = _average(ages)
    average_source_rank = _average(tuple(row.source_rank_score for row in family_rows))
    average_independence = _average(tuple(row.independence_score for row in family_rows))
    contradiction_risk = max(
        (row.contradiction_risk_score for row in family_rows),
        default=ZERO,
    ).quantize(QUANT)
    reason_codes = _row_reason_codes(
        latest_evidence_age_seconds=latest_age,
        average_source_rank_score=average_source_rank,
        average_independence_score=average_independence,
        contradiction_risk_score=contradiction_risk,
        config=config,
    )
    return ResearchSourceAuthorityFreshnessMatrixRow(
        source_family=family_rows[0].source_family,
        evidence_count=evidence_count,
        latest_evidence_age_seconds=latest_age,
        average_evidence_age_seconds=average_age,
        average_source_rank_score=average_source_rank,
        source_rank_band=_source_rank_band(average_source_rank, config=config),
        freshness_band=_freshness_band(latest_age, config=config),
        average_independence_score=average_independence,
        independence_band=_independence_band(average_independence, config=config),
        contradiction_risk_score=contradiction_risk,
        matrix_risk_score=_matrix_risk_score(
            latest_evidence_age_seconds=latest_age,
            average_source_rank_score=average_source_rank,
            average_independence_score=average_independence,
            contradiction_risk_score=contradiction_risk,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    latest_evidence_age_seconds: Decimal,
    average_source_rank_score: Decimal,
    average_independence_score: Decimal,
    contradiction_risk_score: Decimal,
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if average_source_rank_score >= config.high_source_rank_threshold:
        if latest_evidence_age_seconds >= config.stale_age_seconds:
            reasons.append(STALE_HIGH_SOURCE_RANK_BLOCK_REASON)
        elif latest_evidence_age_seconds > config.fresh_age_seconds:
            reasons.append(STALE_HIGH_SOURCE_RANK_WATCH_REASON)
    if (
        latest_evidence_age_seconds <= config.fresh_update_age_seconds
        and average_source_rank_score < config.low_source_rank_threshold
    ):
        if average_source_rank_score <= config.critical_low_source_rank_threshold:
            reasons.append(LOW_SOURCE_RANK_FAST_UPDATE_BLOCK_REASON)
        else:
            reasons.append(LOW_SOURCE_RANK_FAST_UPDATE_WATCH_REASON)
    if average_independence_score <= config.independence_block_threshold:
        reasons.append(LOW_INDEPENDENCE_BLOCK_REASON)
    elif average_independence_score < config.independence_watch_threshold:
        reasons.append(LOW_INDEPENDENCE_WATCH_REASON)
    if contradiction_risk_score >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_RISK_BLOCK_REASON)
    elif contradiction_risk_score >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_RISK_WATCH_REASON)
    if not reasons:
        reasons.append(BALANCED_REASON)
    return tuple(
        reason for reason in ROW_REASON_CODES if reason in reasons
    )


def _matrix_risk_score(
    *,
    latest_evidence_age_seconds: Decimal,
    average_source_rank_score: Decimal,
    average_independence_score: Decimal,
    contradiction_risk_score: Decimal,
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        source_rank_gap = ONE - average_source_rank_score
        independence_gap = ONE - average_independence_score
        score = ZERO
        if (
            average_source_rank_score >= config.high_source_rank_threshold
            and latest_evidence_age_seconds > config.fresh_age_seconds
        ):
            score += (
                min(latest_evidence_age_seconds / config.stale_age_seconds, ONE)
                * Decimal("0.340000")
            )
        if (
            latest_evidence_age_seconds <= config.fresh_update_age_seconds
            and average_source_rank_score < config.low_source_rank_threshold
        ):
            score += source_rank_gap * Decimal("0.200000")
        if average_independence_score < config.independence_watch_threshold:
            score += independence_gap * Decimal("0.200000")
        if contradiction_risk_score >= config.contradiction_watch_threshold:
            score += contradiction_risk_score * Decimal("0.300000")
        if score == ZERO:
            score = (
                source_rank_gap * Decimal("0.200000")
                + contradiction_risk_score * Decimal("0.050000")
            )
        return score.quantize(QUANT)


def _source_rank_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
) -> str:
    if value >= config.high_source_rank_threshold:
        return "high"
    if value < config.low_source_rank_threshold:
        return "low"
    return "medium"


def _freshness_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
) -> str:
    if value <= config.fresh_update_age_seconds:
        return "fast"
    if value <= config.fresh_age_seconds:
        return "current"
    if value < config.stale_age_seconds:
        return "aging"
    return "stale"


def _independence_band(
    value: Decimal,
    *,
    config: ResearchSourceAuthorityFreshnessMatrixConfig,
) -> str:
    if value <= config.independence_block_threshold:
        return "low"
    if value < config.independence_watch_threshold:
        return "thin"
    return "independent"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (BALANCED_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...],
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
    return (BALANCED_REASON,)


def _row_sort_key(row: ResearchSourceAuthorityFreshnessMatrixRow) -> tuple[Decimal, str]:
    return (-row.matrix_risk_score, row.source_family)


def _status_count(
    rows: tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _sum_rows(
    rows: tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...],
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


def _validate_config(config: ResearchSourceAuthorityFreshnessMatrixConfig) -> None:
    if config.fresh_update_age_seconds > config.fresh_age_seconds:
        raise ValueError("fresh_update_age_seconds must not exceed fresh_age_seconds")
    if config.fresh_age_seconds >= config.stale_age_seconds:
        raise ValueError("fresh_age_seconds must be less than stale_age_seconds")
    if config.critical_low_source_rank_threshold > config.low_source_rank_threshold:
        raise ValueError(
            "critical_low_source_rank_threshold must not exceed low_source_rank_threshold",
        )
    if config.low_source_rank_threshold > config.high_source_rank_threshold:
        raise ValueError("low_source_rank_threshold must not exceed high_source_rank_threshold")
    if config.independence_block_threshold > config.independence_watch_threshold:
        raise ValueError("independence_block_threshold must not exceed independence_watch_threshold")
    if config.contradiction_watch_threshold > config.contradiction_block_threshold:
        raise ValueError(
            "contradiction_watch_threshold must not exceed contradiction_block_threshold",
        )


def _validate_row(row: ResearchSourceAuthorityFreshnessMatrixRow) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.latest_evidence_age_seconds > row.average_evidence_age_seconds:
        raise ValueError("latest_evidence_age_seconds must not exceed average")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (BALANCED_REASON,):
        raise ValueError("pass rows must be balanced")


def _validate_report(report: ResearchSourceAuthorityFreshnessMatrixReport) -> None:
    if report.source_family_count != _count(len(report.rows)):
        raise ValueError("source_family_count must match rows")
    if report.evidence_count != _sum_rows(report.rows, "evidence_count"):
        raise ValueError("evidence_count must match rows")
    for status, field_name in (
        ("pass", "pass_source_family_count"),
        ("watch", "watch_source_family_count"),
        ("block", "block_source_family_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "stale_high_source_rank_count",
            (STALE_HIGH_SOURCE_RANK_WATCH_REASON, STALE_HIGH_SOURCE_RANK_BLOCK_REASON),
        ),
        (
            "low_source_rank_fast_update_count",
            (
                LOW_SOURCE_RANK_FAST_UPDATE_WATCH_REASON,
                LOW_SOURCE_RANK_FAST_UPDATE_BLOCK_REASON,
            ),
        ),
        (
            "low_independence_count",
            (LOW_INDEPENDENCE_WATCH_REASON, LOW_INDEPENDENCE_BLOCK_REASON),
        ),
        (
            "contradiction_risk_count",
            (CONTRADICTION_RISK_WATCH_REASON, CONTRADICTION_RISK_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_matrix_risk_score != max(
        (row.matrix_risk_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_matrix_risk_score must match rows")
    if report.oldest_latest_evidence_age_seconds != max(
        (row.latest_evidence_age_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("oldest_latest_evidence_age_seconds must match rows")
    if report.lowest_average_source_rank_score != min(
        (row.average_source_rank_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_average_source_rank_score must match rows")
    if report.lowest_average_independence_score != min(
        (row.average_independence_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("lowest_average_independence_score must match rows")
    if report.highest_contradiction_risk_score != max(
        (row.contradiction_risk_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_contradiction_risk_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic matrix risk sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityFreshnessMatrixRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityFreshnessMatrixRow:
            raise ValueError("rows must contain ResearchSourceAuthorityFreshnessMatrixRow")
        require_paper_only_flags("matrix row", row)
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
    if type(value) is not str or value not in RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_source_rank_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("high", "medium", "low"):
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_freshness_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("fast", "current", "aging", "stale"):
        raise ValueError(f"{field_name} must be fast, current, aging, or stale")


def _require_independence_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("independent", "thin", "low"):
        raise ValueError(f"{field_name} must be independent, thin, or low")


def _require_public_source_family(field_name: str, value: object) -> str:
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
    report: ResearchSourceAuthorityFreshnessMatrixReport,
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
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_FRESHNESS_MATRIX_STATUSES",
    "ResearchSourceAuthorityFreshnessMatrixConfig",
    "ResearchSourceAuthorityFreshnessMatrixInput",
    "ResearchSourceAuthorityFreshnessMatrixReport",
    "ResearchSourceAuthorityFreshnessMatrixRow",
    "build_research_source_authority_freshness_matrix_report",
    "research_source_authority_freshness_matrix_report_digest",
    "research_source_authority_freshness_matrix_report_payload",
    "validate_research_source_authority_freshness_matrix_report_digest",
)
