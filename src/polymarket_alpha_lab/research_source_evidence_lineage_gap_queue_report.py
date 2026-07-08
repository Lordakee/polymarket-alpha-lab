"""Pure report-only source evidence lineage gap queue report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping


DEFAULT_RESEARCH_SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_REPORT_CONFIG_VERSION = (
    "research-source-evidence-lineage-gap-queue-report-v0"
)
SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

SOURCE_AUTHORITY_GAP_REASON = "source_authority_gap"
LINEAGE_COMPLETENESS_GAP_REASON = "lineage_completeness_gap"
FRESHNESS_GAP_REASON = "freshness_gap"
CONTRADICTION_PRESSURE_REASON = "contradiction_pressure"
EXTRACTION_CONFIDENCE_GAP_REASON = "extraction_confidence_gap"
MISSING_FIELD_GAP_REASON = "missing_field_gap"
DEADLINE_PROXIMITY_REASON = "deadline_proximity_pressure"

STATUS_REASON_BY_STATUS = {
    "pass": "source_evidence_lineage_gap_pass",
    "watch": "source_evidence_lineage_gap_watch",
    "block": "source_evidence_lineage_gap_block",
}
REPORT_REASON_BY_STATUS = {
    "pass": "source_evidence_lineage_gap_report_pass",
    "watch": "source_evidence_lineage_gap_report_watch",
    "block": "source_evidence_lineage_gap_report_block",
}

ROW_REASON_CODES = (
    SOURCE_AUTHORITY_GAP_REASON,
    LINEAGE_COMPLETENESS_GAP_REASON,
    FRESHNESS_GAP_REASON,
    CONTRADICTION_PRESSURE_REASON,
    EXTRACTION_CONFIDENCE_GAP_REASON,
    MISSING_FIELD_GAP_REASON,
    DEADLINE_PROXIMITY_REASON,
    STATUS_REASON_BY_STATUS["pass"],
    STATUS_REASON_BY_STATUS["watch"],
    STATUS_REASON_BY_STATUS["block"],
)
REPORT_REASON_CODES = (
    REPORT_REASON_BY_STATUS["pass"],
    REPORT_REASON_BY_STATUS["watch"],
    REPORT_REASON_BY_STATUS["block"],
    *ROW_REASON_CODES,
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "wallet",
        "order",
        "trade",
        "live",
        "raw",
        "scrape",
        "database",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "http://",
        "https://",
        "www.",
        "source_url",
        "source_text",
        "raw_text",
        "postgres://",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "wallet",
        "order",
        "trade",
        "live",
        "raw_source",
        "scrape",
        "database",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_REPORT_CONFIG_VERSION",
    "SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_STATUSES",
    "ResearchSourceEvidenceLineageGapQueueConfig",
    "ResearchSourceEvidenceLineageGapObservation",
    "ResearchSourceEvidenceLineageGapQueueReasonCodeCount",
    "ResearchSourceEvidenceLineageGapQueueReport",
    "ResearchSourceEvidenceLineageGapQueueRow",
    "build_research_source_evidence_lineage_gap_queue_report",
    "research_source_evidence_lineage_gap_queue_report_digest",
    "research_source_evidence_lineage_gap_queue_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchSourceEvidenceLineageGapQueueConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_REPORT_CONFIG_VERSION
    )
    watch_score_threshold: Decimal = Decimal("0.350000")
    block_score_threshold: Decimal = Decimal("0.700000")
    max_freshness_age_hours: Decimal = Decimal("96.000000")
    deadline_proximity_window_hours: Decimal = Decimal("57.600000")
    source_authority_gap_weight: Decimal = Decimal("0.254167")
    lineage_completeness_gap_weight: Decimal = Decimal("0.283333")
    freshness_gap_weight: Decimal = Decimal("0.100000")
    contradiction_pressure_weight: Decimal = Decimal("0.120833")
    extraction_confidence_gap_weight: Decimal = Decimal("0.050000")
    missing_field_gap_weight: Decimal = Decimal("0.011667")
    deadline_proximity_weight: Decimal = Decimal("0.180000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceEvidenceLineageGapQueueConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_score_threshold",
            "block_score_threshold",
            "source_authority_gap_weight",
            "lineage_completeness_gap_weight",
            "freshness_gap_weight",
            "contradiction_pressure_weight",
            "extraction_confidence_gap_weight",
            "missing_field_gap_weight",
            "deadline_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_freshness_age_hours", "deadline_proximity_window_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceLineageGapObservation(_FinalDataclass):
    evidence_label: str
    source_authority_score: Decimal
    lineage_completeness_score: Decimal
    latest_evidence_at: datetime
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    missing_field_count: Decimal
    required_field_count: Decimal
    deadline_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceEvidenceLineageGapObservation, "observation")
        _require_public_label("evidence_label", self.evidence_label)
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(self, "deadline_at", _as_utc("deadline_at", self.deadline_at))
        for field_name in (
            "source_authority_score",
            "lineage_completeness_score",
            "contradiction_pressure",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_field_count",
            _require_nonnegative_count_decimal(
                "missing_field_count",
                self.missing_field_count,
            ),
        )
        object.__setattr__(
            self,
            "required_field_count",
            _require_positive_count_decimal(
                "required_field_count",
                self.required_field_count,
            ),
        )
        if self.missing_field_count > self.required_field_count:
            raise ValueError("missing_field_count must not exceed required_field_count")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceLineageGapQueueRow(_FinalDataclass):
    evidence_label: str
    queue_status: str
    generated_at: datetime
    latest_evidence_at: datetime
    evidence_age_hours: Decimal
    deadline_at: datetime
    deadline_proximity_hours: Decimal
    source_authority_score: Decimal
    source_authority_gap_score: Decimal
    lineage_completeness_score: Decimal
    lineage_completeness_gap_score: Decimal
    freshness_gap_score: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    extraction_confidence_gap_score: Decimal
    missing_field_count: Decimal
    required_field_count: Decimal
    missing_field_gap_score: Decimal
    deadline_proximity_score: Decimal
    lineage_gap_score: Decimal
    reason_codes: tuple[str, ...]
    validation_config: InitVar[ResearchSourceEvidenceLineageGapQueueConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        validation_config: ResearchSourceEvidenceLineageGapQueueConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchSourceEvidenceLineageGapQueueRow, "row")
        if validation_config is None:
            validation_config = ResearchSourceEvidenceLineageGapQueueConfig()
        elif type(validation_config) is not ResearchSourceEvidenceLineageGapQueueConfig:
            raise ValueError(
                "validation_config must be a ResearchSourceEvidenceLineageGapQueueConfig",
            )
        _require_public_label("evidence_label", self.evidence_label)
        _require_status("queue_status", self.queue_status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(self, "deadline_at", _as_utc("deadline_at", self.deadline_at))
        for field_name in ("evidence_age_hours", "deadline_proximity_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("missing_field_count", "required_field_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_field_count <= ZERO:
            raise ValueError("required_field_count must be positive")
        for field_name in (
            "source_authority_score",
            "source_authority_gap_score",
            "lineage_completeness_score",
            "lineage_completeness_gap_score",
            "freshness_gap_score",
            "contradiction_pressure",
            "extraction_confidence",
            "extraction_confidence_gap_score",
            "missing_field_gap_score",
            "deadline_proximity_score",
            "lineage_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceLineageGapQueueReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    queue_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceEvidenceLineageGapQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "queue_ratio",
            _require_ratio_decimal("queue_ratio", self.queue_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceLineageGapQueueReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    status: str
    queue_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_lineage_gap_score: Decimal
    max_lineage_gap_score: Decimal
    average_source_authority_gap_score: Decimal
    average_lineage_completeness_gap_score: Decimal
    average_freshness_gap_score: Decimal
    average_contradiction_pressure: Decimal
    average_extraction_confidence_gap_score: Decimal
    average_missing_field_gap_score: Decimal
    average_deadline_proximity_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceEvidenceLineageGapQueueReasonCodeCount, ...]
    rows: tuple[ResearchSourceEvidenceLineageGapQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceEvidenceLineageGapQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("queue_item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_lineage_gap_score",
            "max_lineage_gap_score",
            "average_source_authority_gap_score",
            "average_lineage_completeness_gap_score",
            "average_freshness_gap_score",
            "average_contradiction_pressure",
            "average_extraction_confidence_gap_score",
            "average_missing_field_gap_score",
            "average_deadline_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            expected_digest = _report_digest_from_values(_report_values_without_digest(self))
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_evidence_lineage_gap_queue_report_payload(self)


def build_research_source_evidence_lineage_gap_queue_report(
    observations: Sequence[ResearchSourceEvidenceLineageGapObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceLineageGapQueueConfig | None = None,
) -> ResearchSourceEvidenceLineageGapQueueReport:
    """Build a deterministic local queue of evidence lineage gaps."""

    if config is None:
        config = ResearchSourceEvidenceLineageGapQueueConfig()
    if type(config) is not ResearchSourceEvidenceLineageGapQueueConfig:
        raise ValueError("config must be a ResearchSourceEvidenceLineageGapQueueConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.latest_evidence_at > generated_at:
            raise ValueError("latest_evidence_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    generated_at=generated_at,
                    config=config,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": status,
        "queue_item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_lineage_gap_score": _average(tuple(row.lineage_gap_score for row in rows)),
        "max_lineage_gap_score": max(
            (row.lineage_gap_score for row in rows),
            default=ZERO,
        ),
        "average_source_authority_gap_score": _average(
            tuple(row.source_authority_gap_score for row in rows),
        ),
        "average_lineage_completeness_gap_score": _average(
            tuple(row.lineage_completeness_gap_score for row in rows),
        ),
        "average_freshness_gap_score": _average(
            tuple(row.freshness_gap_score for row in rows),
        ),
        "average_contradiction_pressure": _average(
            tuple(row.contradiction_pressure for row in rows),
        ),
        "average_extraction_confidence_gap_score": _average(
            tuple(row.extraction_confidence_gap_score for row in rows),
        ),
        "average_missing_field_gap_score": _average(
            tuple(row.missing_field_gap_score for row in rows),
        ),
        "average_deadline_proximity_score": _average_deadline_proximity_score(
            rows,
            config,
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceEvidenceLineageGapQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_evidence_lineage_gap_queue_report_payload(
    report: ResearchSourceEvidenceLineageGapQueueReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceEvidenceLineageGapQueueReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchSourceEvidenceLineageGapQueueReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_flags(payload)
    _validate_payload_statuses(payload)
    _validate_payload_digest(payload)
    return payload


def research_source_evidence_lineage_gap_queue_report_digest(
    report: ResearchSourceEvidenceLineageGapQueueReport | Mapping[str, Any],
) -> str:
    payload = research_source_evidence_lineage_gap_queue_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_observation(
    observation: ResearchSourceEvidenceLineageGapObservation,
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceLineageGapQueueConfig,
) -> ResearchSourceEvidenceLineageGapQueueRow:
    evidence_age_hours = _duration_hours(observation.latest_evidence_at, generated_at)
    deadline_hours = _future_duration_hours(generated_at, observation.deadline_at)
    source_authority_gap = _clamp_ratio(ONE - observation.source_authority_score)
    lineage_completeness_gap = _clamp_ratio(ONE - observation.lineage_completeness_score)
    freshness_gap = _clamp_ratio(
        _safe_ratio(evidence_age_hours, config.max_freshness_age_hours),
    )
    extraction_gap = _clamp_ratio(ONE - observation.extraction_confidence)
    missing_field_gap = _clamp_ratio(
        _safe_ratio(observation.missing_field_count, observation.required_field_count),
    )
    deadline_score = _clamp_ratio(
        _safe_ratio(
            max(config.deadline_proximity_window_hours - deadline_hours, ZERO),
            config.deadline_proximity_window_hours,
        ),
    )
    lineage_gap_score = _clamp_ratio(
        (source_authority_gap * config.source_authority_gap_weight)
        + (lineage_completeness_gap * config.lineage_completeness_gap_weight)
        + (freshness_gap * config.freshness_gap_weight)
        + (observation.contradiction_pressure * config.contradiction_pressure_weight)
        + (extraction_gap * config.extraction_confidence_gap_weight)
        + (missing_field_gap * config.missing_field_gap_weight)
        + (deadline_score * config.deadline_proximity_weight),
    )
    queue_status = _queue_status(lineage_gap_score, config)
    return ResearchSourceEvidenceLineageGapQueueRow(
        evidence_label=observation.evidence_label,
        queue_status=queue_status,
        generated_at=generated_at,
        latest_evidence_at=observation.latest_evidence_at,
        evidence_age_hours=evidence_age_hours,
        deadline_at=observation.deadline_at,
        deadline_proximity_hours=deadline_hours,
        source_authority_score=observation.source_authority_score,
        source_authority_gap_score=source_authority_gap,
        lineage_completeness_score=observation.lineage_completeness_score,
        lineage_completeness_gap_score=lineage_completeness_gap,
        freshness_gap_score=freshness_gap,
        contradiction_pressure=observation.contradiction_pressure,
        extraction_confidence=observation.extraction_confidence,
        extraction_confidence_gap_score=extraction_gap,
        missing_field_count=observation.missing_field_count,
        required_field_count=observation.required_field_count,
        missing_field_gap_score=missing_field_gap,
        deadline_proximity_score=deadline_score,
        lineage_gap_score=lineage_gap_score,
        reason_codes=_row_reason_codes(
            queue_status=queue_status,
            source_authority_gap_score=source_authority_gap,
            lineage_completeness_gap_score=lineage_completeness_gap,
            freshness_gap_score=freshness_gap,
            contradiction_pressure=observation.contradiction_pressure,
            extraction_confidence_gap_score=extraction_gap,
            missing_field_gap_score=missing_field_gap,
            deadline_proximity_score=deadline_score,
        ),
        validation_config=config,
    )


def _row_reason_codes(
    *,
    queue_status: str,
    source_authority_gap_score: Decimal,
    lineage_completeness_gap_score: Decimal,
    freshness_gap_score: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence_gap_score: Decimal,
    missing_field_gap_score: Decimal,
    deadline_proximity_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_authority_gap_score >= Decimal("0.250000"):
        reasons.append(SOURCE_AUTHORITY_GAP_REASON)
    if lineage_completeness_gap_score >= Decimal("0.250000"):
        reasons.append(LINEAGE_COMPLETENESS_GAP_REASON)
    if freshness_gap_score >= Decimal("0.500000"):
        reasons.append(FRESHNESS_GAP_REASON)
    if contradiction_pressure >= Decimal("0.250000"):
        reasons.append(CONTRADICTION_PRESSURE_REASON)
    if extraction_confidence_gap_score >= Decimal("0.250000"):
        reasons.append(EXTRACTION_CONFIDENCE_GAP_REASON)
    if missing_field_gap_score > ZERO:
        reasons.append(MISSING_FIELD_GAP_REASON)
    if deadline_proximity_score >= Decimal("0.500000"):
        reasons.append(DEADLINE_PROXIMITY_REASON)
    reasons.append(STATUS_REASON_BY_STATUS[queue_status])
    return _require_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _queue_status(
    lineage_gap_score: Decimal,
    config: ResearchSourceEvidenceLineageGapQueueConfig,
) -> str:
    if lineage_gap_score >= config.block_score_threshold:
        return "block"
    if lineage_gap_score >= config.watch_score_threshold:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceEvidenceLineageGapQueueRow, ...]) -> str:
    if any(row.queue_status == "block" for row in rows):
        return "block"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceLineageGapQueueRow, ...],
    status: str,
) -> tuple[str, ...]:
    row_reasons = {reason for row in rows for reason in row.reason_codes}
    return (
        REPORT_REASON_BY_STATUS[status],
        *(reason for reason in ROW_REASON_CODES if reason in row_reasons),
    )


def _reason_code_counts(
    rows: tuple[ResearchSourceEvidenceLineageGapQueueRow, ...],
) -> tuple[ResearchSourceEvidenceLineageGapQueueReasonCodeCount, ...]:
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchSourceEvidenceLineageGapQueueReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            queue_ratio=_safe_ratio(_decimal_count(counts[reason_code]), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if counts[reason_code]
    )


def _normalize_observations(
    observations: Sequence[ResearchSourceEvidenceLineageGapObservation],
) -> tuple[ResearchSourceEvidenceLineageGapObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchSourceEvidenceLineageGapObservation:
            raise ValueError(
                "observations must contain ResearchSourceEvidenceLineageGapObservation",
            )
        if observation.evidence_label in seen:
            raise ValueError("evidence_label values must be unique")
        seen.add(observation.evidence_label)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchSourceEvidenceLineageGapQueueRow, ...],
) -> tuple[ResearchSourceEvidenceLineageGapQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceEvidenceLineageGapQueueRow:
            raise ValueError("rows must contain ResearchSourceEvidenceLineageGapQueueRow")
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != sorted_rows:
        raise ValueError("rows must be sorted by queue priority")
    if len({row.evidence_label for row in normalized}) != len(normalized):
        raise ValueError("rows must have unique evidence_label values")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceEvidenceLineageGapQueueReasonCodeCount, ...],
) -> tuple[ResearchSourceEvidenceLineageGapQueueReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchSourceEvidenceLineageGapQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceEvidenceLineageGapQueueReasonCodeCount",
            )
    expected = tuple(
        sorted(
            normalized,
            key=lambda item: ROW_REASON_CODES.index(item.reason_code),
        ),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted by reason code order")
    return normalized


def _row_sort_key(row: ResearchSourceEvidenceLineageGapQueueRow) -> tuple[Decimal, str]:
    return (-row.lineage_gap_score, row.evidence_label)


def _status_count(
    rows: tuple[ResearchSourceEvidenceLineageGapQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.queue_status == status)


def _validate_config(config: ResearchSourceEvidenceLineageGapQueueConfig) -> None:
    if config.block_score_threshold <= config.watch_score_threshold:
        raise ValueError("block_score_threshold must exceed watch_score_threshold")
    weight_sum = (
        config.source_authority_gap_weight
        + config.lineage_completeness_gap_weight
        + config.freshness_gap_weight
        + config.contradiction_pressure_weight
        + config.extraction_confidence_gap_weight
        + config.missing_field_gap_weight
        + config.deadline_proximity_weight
    )
    if _quantize_decimal(weight_sum) != ONE:
        raise ValueError("lineage gap component weights must sum to 1.000000")


def _validate_row(
    row: ResearchSourceEvidenceLineageGapQueueRow,
    config: ResearchSourceEvidenceLineageGapQueueConfig,
) -> None:
    if row.latest_evidence_at > row.generated_at:
        raise ValueError("latest_evidence_at must not be after generated_at")
    if row.missing_field_count > row.required_field_count:
        raise ValueError("missing_field_count must not exceed required_field_count")
    if row.source_authority_gap_score != _clamp_ratio(ONE - row.source_authority_score):
        raise ValueError("source_authority_gap_score must match source_authority_score")
    if row.lineage_completeness_gap_score != _clamp_ratio(
        ONE - row.lineage_completeness_score,
    ):
        raise ValueError(
            "lineage_completeness_gap_score must match lineage_completeness_score",
        )
    if row.extraction_confidence_gap_score != _clamp_ratio(
        ONE - row.extraction_confidence,
    ):
        raise ValueError("extraction_confidence_gap_score must match extraction_confidence")
    if row.queue_status != _queue_status(row.lineage_gap_score, config):
        raise ValueError("queue_status must match lineage_gap_score")


def _validate_report(report: ResearchSourceEvidenceLineageGapQueueReport) -> None:
    rows = report.rows
    if report.queue_item_count != _decimal_count(len(rows)):
        raise ValueError("queue_item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match rows")


def _report_values_without_digest(
    report: ResearchSourceEvidenceLineageGapQueueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(values)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or DIGEST_RE.fullmatch(digest) is None:
        raise ValueError("derived_validation_digest must be a SHA-256 digest")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    expected = _report_digest_from_values(unsigned)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _validate_payload_flags(payload: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_payload_statuses(payload: Mapping[str, object]) -> None:
    status = payload.get("status")
    if status not in SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("rows must contain objects")
        row_status = row.get("queue_status")
        if row_status not in SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_STATUSES:
            raise ValueError("queue_status must be pass, watch, or block")
        for field_name in ("paper_only", "report_only", "readonly"):
            if row.get(field_name) is not True:
                raise ValueError(f"row {field_name} must be True")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return f"{_quantize_decimal(value):f}"
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers and isinstance(value, list):
            raise ValueError(f"{label} must not expose mutable list payloads")
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) is str and _has_unsafe_public_value(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_key(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS)


def _has_unsafe_public_value(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    fragments = UNSAFE_PUBLIC_KEY_FRAGMENTS | UNSAFE_PUBLIC_VALUE_FRAGMENTS
    return any(fragment in normalized for fragment in fragments)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe public label")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in SOURCE_EVIDENCE_LINEAGE_GAP_QUEUE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} is not a supported reason code")
    return value


def _require_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, value, allowed) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicate reason codes")
    if normalized != tuple(value for value in allowed if value in normalized):
        raise ValueError(f"{field_name} must follow canonical reason code order")
    return normalized


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(_require_decimal(field_name, value))
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(_require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize_decimal(Decimal(value))


def _duration_hours(started_at: datetime, finished_at: datetime) -> Decimal:
    if finished_at < started_at:
        raise ValueError("finished_at must not be before started_at")
    return _quantize_decimal(
        _safe_ratio(_duration_seconds(started_at, finished_at), SECONDS_PER_HOUR),
    )


def _future_duration_hours(started_at: datetime, finished_at: datetime) -> Decimal:
    if finished_at <= started_at:
        return ZERO
    return _duration_hours(started_at, finished_at)


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    return Decimal(delta.days * 86400 + delta.seconds) + (
        Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    return numerator / denominator


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize_decimal(value)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(sum(values, ZERO) / _decimal_count(len(values)))


def _average_deadline_proximity_score(
    rows: tuple[ResearchSourceEvidenceLineageGapQueueRow, ...],
    config: ResearchSourceEvidenceLineageGapQueueConfig,
) -> Decimal:
    if not rows:
        return ZERO
    scores = tuple(
        _safe_ratio(
            max(config.deadline_proximity_window_hours - row.deadline_proximity_hours, ZERO),
            config.deadline_proximity_window_hours,
        )
        for row in rows
    )
    return _quantize_decimal(sum(scores, ZERO) / _decimal_count(len(scores)))


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
