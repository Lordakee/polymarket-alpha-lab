"""Report-only event resolution finality confidence scoring."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_RESOLUTION_FINALITY_CONFIDENCE_REPORT_CONFIG_VERSION = (
    "research-event-resolution-finality-confidence-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

NO_FINALITY_EVIDENCE_REASON = "no_finality_evidence"
PASS_REASON = "resolution_finality_confidence_pass"
WATCH_REASON = "resolution_finality_confidence_watch"
BLOCK_REASON = "resolution_finality_confidence_block"
CONFIDENCE_BELOW_PASS_REASON = "finality_confidence_below_pass"
CONFIDENCE_BELOW_WATCH_REASON = "finality_confidence_below_watch"
PRIMARY_BELOW_PASS_REASON = "primary_evidence_below_pass"
PRIMARY_BELOW_WATCH_REASON = "primary_evidence_below_watch"
CORROBORATION_BELOW_PASS_REASON = "corroboration_below_pass"
CORROBORATION_BELOW_WATCH_REASON = "corroboration_below_watch"
CLARITY_BELOW_PASS_REASON = "criteria_clarity_below_pass"
CLARITY_BELOW_WATCH_REASON = "criteria_clarity_below_watch"
DISPUTE_WATCH_REASON = "dispute_risk_watch"
DISPUTE_BLOCK_REASON = "dispute_risk_block"
REVISION_WATCH_REASON = "revision_risk_watch"
REVISION_BLOCK_REASON = "revision_risk_block"
LAG_WATCH_REASON = "finality_lag_watch"
LAG_BLOCK_REASON = "finality_lag_block"

REASON_CODES = (
    NO_FINALITY_EVIDENCE_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    CONFIDENCE_BELOW_PASS_REASON,
    CONFIDENCE_BELOW_WATCH_REASON,
    PRIMARY_BELOW_PASS_REASON,
    PRIMARY_BELOW_WATCH_REASON,
    CORROBORATION_BELOW_PASS_REASON,
    CORROBORATION_BELOW_WATCH_REASON,
    CLARITY_BELOW_PASS_REASON,
    CLARITY_BELOW_WATCH_REASON,
    DISPUTE_WATCH_REASON,
    DISPUTE_BLOCK_REASON,
    REVISION_WATCH_REASON,
    REVISION_BLOCK_REASON,
    LAG_WATCH_REASON,
    LAG_BLOCK_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        _join_parts("cand", "idate", "_id"),
        _join_parts("mar", "ket", "_id"),
        _join_parts("sl", "ug"),
        _join_parts("ques", "tion"),
        _join_parts("sou", "rce", "_url"),
        _join_parts("sou", "rce", "_text"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("si", "zing"),
        _join_parts("recomm", "endation"),
        _join_parts("au", "th"),
        _join_parts("pri", "vate"),
        _join_parts("acc", "ount"),
        _join_parts("li", "ve"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
    ),
)

UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        _join_parts("cand", "idate"),
        _join_parts("mar", "ket"),
        _join_parts("http", "s"),
        "http://",
        "://",
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("d", "sn"),
        _join_parts("au", "th"),
        _join_parts("pri", "vate"),
        _join_parts("li", "ve"),
    ),
)


@dataclass(frozen=True)
class ResearchEventResolutionFinalityConfidenceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_FINALITY_CONFIDENCE_REPORT_CONFIG_VERSION
    )
    pass_confidence_score: Decimal = Decimal("0.750000")
    watch_confidence_score: Decimal = Decimal("0.500000")
    pass_primary_evidence_score: Decimal = Decimal("0.700000")
    watch_primary_evidence_score: Decimal = Decimal("0.400000")
    pass_corroboration_score: Decimal = Decimal("0.700000")
    watch_corroboration_score: Decimal = Decimal("0.400000")
    pass_criteria_clarity_score: Decimal = Decimal("0.700000")
    watch_criteria_clarity_score: Decimal = Decimal("0.400000")
    watch_dispute_risk_score: Decimal = Decimal("0.250000")
    block_dispute_risk_score: Decimal = Decimal("0.600000")
    watch_revision_risk_score: Decimal = Decimal("0.250000")
    block_revision_risk_score: Decimal = Decimal("0.600000")
    watch_finality_lag_seconds: Decimal = Decimal("3600.000000")
    block_finality_lag_seconds: Decimal = Decimal("86400.000000")
    primary_evidence_weight: Decimal = Decimal("0.300000")
    corroboration_weight: Decimal = Decimal("0.250000")
    criteria_clarity_weight: Decimal = Decimal("0.200000")
    dispute_resistance_weight: Decimal = Decimal("0.150000")
    revision_resistance_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionFinalityConfidenceConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_confidence_score",
            "watch_confidence_score",
            "pass_primary_evidence_score",
            "watch_primary_evidence_score",
            "pass_corroboration_score",
            "watch_corroboration_score",
            "pass_criteria_clarity_score",
            "watch_criteria_clarity_score",
            "watch_dispute_risk_score",
            "block_dispute_risk_score",
            "watch_revision_risk_score",
            "block_revision_risk_score",
            "primary_evidence_weight",
            "corroboration_weight",
            "criteria_clarity_weight",
            "dispute_resistance_weight",
            "revision_resistance_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_finality_lag_seconds",
            "block_finality_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_confidence_score <= self.watch_confidence_score:
            raise ValueError("pass_confidence_score must exceed watch_confidence_score")
        if self.pass_primary_evidence_score <= self.watch_primary_evidence_score:
            raise ValueError(
                "pass_primary_evidence_score must exceed watch_primary_evidence_score",
            )
        if self.pass_corroboration_score <= self.watch_corroboration_score:
            raise ValueError(
                "pass_corroboration_score must exceed watch_corroboration_score",
            )
        if self.pass_criteria_clarity_score <= self.watch_criteria_clarity_score:
            raise ValueError(
                "pass_criteria_clarity_score must exceed watch_criteria_clarity_score",
            )
        if self.block_dispute_risk_score <= self.watch_dispute_risk_score:
            raise ValueError("block_dispute_risk_score must exceed watch_dispute_risk_score")
        if self.block_revision_risk_score <= self.watch_revision_risk_score:
            raise ValueError(
                "block_revision_risk_score must exceed watch_revision_risk_score",
            )
        if self.block_finality_lag_seconds <= self.watch_finality_lag_seconds:
            raise ValueError(
                "block_finality_lag_seconds must exceed watch_finality_lag_seconds",
            )
        weight_sum = _quantize(
            self.primary_evidence_weight
            + self.corroboration_weight
            + self.criteria_clarity_weight
            + self.dispute_resistance_weight
            + self.revision_resistance_weight,
        )
        if weight_sum != ONE:
            raise ValueError("confidence weights must sum to 1")
        require_paper_only_flags("finality confidence config", self)


@dataclass(frozen=True)
class ResearchEventResolutionFinalityEvidenceRow:
    event_key: str
    resolution_family: str
    evidence_family: str
    resolution_effective_at: datetime
    observed_at: datetime
    primary_evidence_score: Decimal
    corroboration_score: Decimal
    criteria_clarity_score: Decimal
    dispute_risk_score: Decimal
    revision_risk_score: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionFinalityEvidenceRow, "evidence row")
        for field_name in ("event_key", "resolution_family", "evidence_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "resolution_effective_at",
            _as_utc("resolution_effective_at", self.resolution_effective_at),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        if self.observed_at < self.resolution_effective_at:
            raise ValueError("observed_at must not be before resolution_effective_at")
        for field_name in (
            "primary_evidence_score",
            "corroboration_score",
            "criteria_clarity_score",
            "dispute_risk_score",
            "revision_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_input_reason_codes(self.upstream_reason_codes),
        )
        require_paper_only_flags("finality confidence evidence row", self)


@dataclass(frozen=True)
class ResearchEventResolutionFinalityConfidenceRow:
    event_key: str
    resolution_family: str
    evidence_family: str
    resolution_effective_at: datetime
    observed_at: datetime
    finality_lag_seconds: Decimal
    primary_evidence_score: Decimal
    corroboration_score: Decimal
    criteria_clarity_score: Decimal
    dispute_risk_score: Decimal
    revision_risk_score: Decimal
    primary_evidence_weight: Decimal
    corroboration_weight: Decimal
    criteria_clarity_weight: Decimal
    dispute_resistance_weight: Decimal
    revision_resistance_weight: Decimal
    finality_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionFinalityConfidenceRow, "row")
        for field_name in ("event_key", "resolution_family", "evidence_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "resolution_effective_at",
            _as_utc("resolution_effective_at", self.resolution_effective_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.observed_at < self.resolution_effective_at:
            raise ValueError("observed_at must not be before resolution_effective_at")
        object.__setattr__(
            self,
            "finality_lag_seconds",
            _normalize_nonnegative_decimal(
                "finality_lag_seconds",
                self.finality_lag_seconds,
            ),
        )
        for field_name in (
            "primary_evidence_score",
            "corroboration_score",
            "criteria_clarity_score",
            "dispute_risk_score",
            "revision_risk_score",
            "primary_evidence_weight",
            "corroboration_weight",
            "criteria_clarity_weight",
            "dispute_resistance_weight",
            "revision_resistance_weight",
            "finality_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("finality confidence row", self)


@dataclass(frozen=True)
class ResearchEventResolutionFinalityConfidenceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionFinalityConfidenceReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        require_paper_only_flags("finality confidence reason count", self)


@dataclass(frozen=True)
class ResearchEventResolutionFinalityConfidenceReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_finality_confidence_score: Decimal | None
    max_finality_lag_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionFinalityConfidenceRow, ...]
    reason_code_counts: tuple[
        ResearchEventResolutionFinalityConfidenceReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionFinalityConfidenceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_finality_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_finality_confidence_score",
            _normalize_optional_probability(
                "average_finality_confidence_score",
                self.average_finality_confidence_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        require_paper_only_flags("finality confidence report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
            _require_report_validation_digest(self)


def build_research_event_resolution_finality_confidence_report(
    evidence_rows: Iterable[ResearchEventResolutionFinalityEvidenceRow],
    *,
    config: ResearchEventResolutionFinalityConfidenceConfig,
    generated_at: datetime,
) -> ResearchEventResolutionFinalityConfidenceReport:
    if type(config) is not ResearchEventResolutionFinalityConfidenceConfig:
        raise ValueError("config must be a ResearchEventResolutionFinalityConfidenceConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(evidence_rows, generated_at=generated_at_utc)
    rows = _sort_rows(tuple(_build_row(row, config=config) for row in inputs))
    reason_codes = _report_reason_codes(rows)

    return ResearchEventResolutionFinalityConfidenceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_finality_confidence_score=_average_score(rows),
        max_finality_lag_seconds=_max_lag(rows),
        status=_report_status(reason_codes),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_event_resolution_finality_confidence_report_to_payload(
    report: ResearchEventResolutionFinalityConfidenceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionFinalityConfidenceReport:
        raise ValueError("report must be a ResearchEventResolutionFinalityConfidenceReport")
    _validate_public_numeric_types(report)
    _require_report_validation_digest(report)
    require_paper_only_flags("finality confidence report", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report JSON value must be an object")
    validate_research_event_resolution_finality_confidence_public_payload(ready)
    return ready


def validate_research_event_resolution_finality_confidence_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("finality confidence payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    row: ResearchEventResolutionFinalityEvidenceRow,
    *,
    config: ResearchEventResolutionFinalityConfidenceConfig,
) -> ResearchEventResolutionFinalityConfidenceRow:
    lag_seconds = _age_seconds(row.observed_at, row.resolution_effective_at)
    confidence_score = _confidence_score(row, config)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        finality_lag_seconds=lag_seconds,
        finality_confidence_score=confidence_score,
    )
    return ResearchEventResolutionFinalityConfidenceRow(
        event_key=row.event_key,
        resolution_family=row.resolution_family,
        evidence_family=row.evidence_family,
        resolution_effective_at=row.resolution_effective_at,
        observed_at=row.observed_at,
        finality_lag_seconds=lag_seconds,
        primary_evidence_score=row.primary_evidence_score,
        corroboration_score=row.corroboration_score,
        criteria_clarity_score=row.criteria_clarity_score,
        dispute_risk_score=row.dispute_risk_score,
        revision_risk_score=row.revision_risk_score,
        primary_evidence_weight=config.primary_evidence_weight,
        corroboration_weight=config.corroboration_weight,
        criteria_clarity_weight=config.criteria_clarity_weight,
        dispute_resistance_weight=config.dispute_resistance_weight,
        revision_resistance_weight=config.revision_resistance_weight,
        finality_confidence_score=confidence_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _confidence_score(
    row: ResearchEventResolutionFinalityEvidenceRow,
    config: ResearchEventResolutionFinalityConfidenceConfig,
) -> Decimal:
    return _quantize(
        row.primary_evidence_score * config.primary_evidence_weight
        + row.corroboration_score * config.corroboration_weight
        + row.criteria_clarity_score * config.criteria_clarity_weight
        + (ONE - row.dispute_risk_score) * config.dispute_resistance_weight
        + (ONE - row.revision_risk_score) * config.revision_resistance_weight,
    )


def _row_reason_codes(
    row: ResearchEventResolutionFinalityEvidenceRow,
    *,
    config: ResearchEventResolutionFinalityConfidenceConfig,
    finality_lag_seconds: Decimal,
    finality_confidence_score: Decimal,
) -> tuple[str, ...]:
    reasons = [
        _status_reason(
            finality_confidence_score=finality_confidence_score,
            primary_evidence_score=row.primary_evidence_score,
            corroboration_score=row.corroboration_score,
            criteria_clarity_score=row.criteria_clarity_score,
            dispute_risk_score=row.dispute_risk_score,
            revision_risk_score=row.revision_risk_score,
            finality_lag_seconds=finality_lag_seconds,
            config=config,
        ),
    ]
    _append_threshold_reason(
        reasons,
        value=finality_confidence_score,
        watch_threshold=config.watch_confidence_score,
        pass_threshold=config.pass_confidence_score,
        watch_reason=CONFIDENCE_BELOW_WATCH_REASON,
        pass_reason=CONFIDENCE_BELOW_PASS_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=row.primary_evidence_score,
        watch_threshold=config.watch_primary_evidence_score,
        pass_threshold=config.pass_primary_evidence_score,
        watch_reason=PRIMARY_BELOW_WATCH_REASON,
        pass_reason=PRIMARY_BELOW_PASS_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=row.corroboration_score,
        watch_threshold=config.watch_corroboration_score,
        pass_threshold=config.pass_corroboration_score,
        watch_reason=CORROBORATION_BELOW_WATCH_REASON,
        pass_reason=CORROBORATION_BELOW_PASS_REASON,
    )
    _append_threshold_reason(
        reasons,
        value=row.criteria_clarity_score,
        watch_threshold=config.watch_criteria_clarity_score,
        pass_threshold=config.pass_criteria_clarity_score,
        watch_reason=CLARITY_BELOW_WATCH_REASON,
        pass_reason=CLARITY_BELOW_PASS_REASON,
    )
    _append_risk_reason(
        reasons,
        value=row.dispute_risk_score,
        watch_threshold=config.watch_dispute_risk_score,
        block_threshold=config.block_dispute_risk_score,
        watch_reason=DISPUTE_WATCH_REASON,
        block_reason=DISPUTE_BLOCK_REASON,
    )
    _append_risk_reason(
        reasons,
        value=row.revision_risk_score,
        watch_threshold=config.watch_revision_risk_score,
        block_threshold=config.block_revision_risk_score,
        watch_reason=REVISION_WATCH_REASON,
        block_reason=REVISION_BLOCK_REASON,
    )
    _append_risk_reason(
        reasons,
        value=finality_lag_seconds,
        watch_threshold=config.watch_finality_lag_seconds,
        block_threshold=config.block_finality_lag_seconds,
        watch_reason=LAG_WATCH_REASON,
        block_reason=LAG_BLOCK_REASON,
    )
    reasons.extend(f"input_{reason_code}" for reason_code in row.upstream_reason_codes)
    return _normalize_reason_codes(tuple(reasons))


def _status_reason(
    *,
    finality_confidence_score: Decimal,
    primary_evidence_score: Decimal,
    corroboration_score: Decimal,
    criteria_clarity_score: Decimal,
    dispute_risk_score: Decimal,
    revision_risk_score: Decimal,
    finality_lag_seconds: Decimal,
    config: ResearchEventResolutionFinalityConfidenceConfig,
) -> str:
    if (
        finality_confidence_score < config.watch_confidence_score
        or primary_evidence_score < config.watch_primary_evidence_score
        or corroboration_score < config.watch_corroboration_score
        or criteria_clarity_score < config.watch_criteria_clarity_score
        or dispute_risk_score >= config.block_dispute_risk_score
        or revision_risk_score >= config.block_revision_risk_score
        or finality_lag_seconds >= config.block_finality_lag_seconds
    ):
        return BLOCK_REASON
    if (
        finality_confidence_score < config.pass_confidence_score
        or primary_evidence_score < config.pass_primary_evidence_score
        or corroboration_score < config.pass_corroboration_score
        or criteria_clarity_score < config.pass_criteria_clarity_score
        or dispute_risk_score >= config.watch_dispute_risk_score
        or revision_risk_score >= config.watch_revision_risk_score
        or finality_lag_seconds >= config.watch_finality_lag_seconds
    ):
        return WATCH_REASON
    return PASS_REASON


def _append_threshold_reason(
    reasons: list[str],
    *,
    value: Decimal,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
    watch_reason: str,
    pass_reason: str,
) -> None:
    if value < watch_threshold:
        reasons.append(watch_reason)
    elif value < pass_threshold:
        reasons.append(pass_reason)


def _append_risk_reason(
    reasons: list[str],
    *,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reasons.append(block_reason)
    elif value >= watch_threshold:
        reasons.append(watch_reason)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchEventResolutionFinalityEvidenceRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("evidence rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("evidence rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionFinalityEvidenceRow:
            raise ValueError("evidence rows must contain finality evidence rows")
        require_paper_only_flags("finality confidence evidence row", row)
        if row.resolution_effective_at > generated_at:
            raise ValueError("resolution_effective_at must not be in the future")
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if row.observed_at < row.resolution_effective_at:
            raise ValueError("observed_at must not be before resolution_effective_at")
        if row.event_key in seen:
            raise ValueError("event_key values must be unique")
        seen.add(row.event_key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (row.event_key, row.resolution_family, row.evidence_family),
        ),
    )


def _sort_rows(
    rows: tuple[ResearchEventResolutionFinalityConfidenceRow, ...],
) -> tuple[ResearchEventResolutionFinalityConfidenceRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                row.finality_confidence_score,
                -row.finality_lag_seconds,
                row.event_key,
                row.resolution_family,
                row.evidence_family,
            ),
        ),
    )


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionFinalityConfidenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_FINALITY_EVIDENCE_REASON,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    standard = tuple(reason_code for reason_code in REASON_CODES if reason_code in seen)
    extras = tuple(sorted(reason_code for reason_code in seen if reason_code not in REASON_CODES))
    return standard + extras


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionFinalityConfidenceRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventResolutionFinalityConfidenceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionFinalityConfidenceReasonCodeCount(
                reason_code=NO_FINALITY_EVIDENCE_REASON,
                count=_decimal_count(1),
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchEventResolutionFinalityConfidenceReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
        if counter[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchEventResolutionFinalityConfidenceRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average_score(
    rows: tuple[ResearchEventResolutionFinalityConfidenceRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.finality_confidence_score for row in rows), ZERO)
        / _decimal_count(len(rows)),
    )


def _max_lag(rows: tuple[ResearchEventResolutionFinalityConfidenceRow, ...]) -> Decimal:
    return max((row.finality_lag_seconds for row in rows), default=ZERO).quantize(QUANT)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if NO_FINALITY_EVIDENCE_REASON in reason_codes or BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _validate_row(row: ResearchEventResolutionFinalityConfidenceRow) -> None:
    expected_lag = _age_seconds(row.observed_at, row.resolution_effective_at)
    if row.finality_lag_seconds != expected_lag:
        raise ValueError("finality_lag_seconds must match observation lag")
    expected_score = _quantize(
        row.primary_evidence_score * row.primary_evidence_weight
        + row.corroboration_score * row.corroboration_weight
        + row.criteria_clarity_score * row.criteria_clarity_weight
        + (ONE - row.dispute_risk_score) * row.dispute_resistance_weight
        + (ONE - row.revision_risk_score) * row.revision_resistance_weight,
    )
    if row.finality_confidence_score != expected_score:
        raise ValueError("finality_confidence_score must match component scores")
    if _row_status(row.reason_codes) != row.status:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventResolutionFinalityConfidenceReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_finality_confidence_score != _average_score(report.rows):
        raise ValueError("average_finality_confidence_score must match rows")
    if report.max_finality_lag_seconds != _max_lag(report.rows):
        raise ValueError("max_finality_lag_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionFinalityConfidenceRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionFinalityConfidenceRow:
            raise ValueError("rows must contain finality confidence rows")
        require_paper_only_flags("finality confidence row", row)
        if row.event_key in seen:
            raise ValueError("rows must contain unique event_key values")
        seen.add(row.event_key)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchEventResolutionFinalityConfidenceReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventResolutionFinalityConfidenceReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        require_paper_only_flags("finality confidence reason count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    standard = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    extras = tuple(sorted(reason_code for reason_code in reason_codes if reason_code not in REASON_CODES))
    if standard + extras != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("upstream_reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_reason_code("upstream_reason_codes", reason_code)
    return tuple(sorted(set(reason_codes)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use lowercase reason code characters")


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("later datetime must not be before earlier datetime")
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND,
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    _reject_unsafe_string(field_name, value, UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe non-string key in {label}")
            _reject_unsafe_string(label, key, UNSAFE_PUBLIC_KEY_FRAGMENTS)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_string(label, value, UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _reject_unsafe_string(
    label: str,
    value: str,
    fragments: frozenset[str],
) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in fragments):
        raise ValueError(f"unsafe public value in {label}")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    _require_public_payload_dict_flags(payload)
    _require_nested_public_payload_flags(payload)


def _require_public_payload_dict_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")


def _require_nested_public_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        if any(
            field_name in value
            for field_name in ("paper_only", "report_only", "readonly")
        ):
            _require_public_payload_dict_flags(value)
        for item in value.values():
            _require_nested_public_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_nested_public_payload_flags(item)


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is bool or value is None or type(value) is str:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload metrics must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _validate_public_numeric_types(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _validate_public_numeric_types(getattr(value, field.name))
        return
    if type(value) in (list, tuple):
        for item in value:
            _validate_public_numeric_types(item)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return
    if type(value) is datetime:
        _as_utc("datetime value", value)
        return
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError("public report values must use Decimal metrics")


def _report_derived_validation_digest(
    report: ResearchEventResolutionFinalityConfidenceReport,
) -> str:
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a dict")
    return _public_payload_derived_validation_digest(payload)


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_report_validation_digest(
    report: ResearchEventResolutionFinalityConfidenceReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_FINALITY_CONFIDENCE_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionFinalityConfidenceConfig",
    "ResearchEventResolutionFinalityConfidenceReasonCodeCount",
    "ResearchEventResolutionFinalityConfidenceReport",
    "ResearchEventResolutionFinalityConfidenceRow",
    "ResearchEventResolutionFinalityEvidenceRow",
    "build_research_event_resolution_finality_confidence_report",
    "research_event_resolution_finality_confidence_report_to_payload",
    "validate_research_event_resolution_finality_confidence_public_payload",
)
