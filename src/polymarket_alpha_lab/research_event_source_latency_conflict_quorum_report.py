"""Pure report-only event source latency/conflict quorum report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Iterable, Mapping


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION",
    "ResearchEventSourceLatencyConflictQuorumConfig",
    "ResearchEventSourceLatencyConflictQuorumObservation",
    "ResearchEventSourceLatencyConflictQuorumReport",
    "ResearchEventSourceLatencyConflictQuorumRow",
    "build_research_event_source_latency_conflict_quorum_report",
    "research_event_source_latency_conflict_quorum_report_payload",
)


DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION = (
    "research-event-source-latency-conflict-quorum-report"
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
SAFE_REASON_CODES = (
    "empty_observations",
    "latency_watch",
    "latency_block",
    "quorum_gap_watch",
    "quorum_gap_block",
    "conflict_watch",
    "conflict_block",
    "latency_conflict_quorum_pass",
    "latency_conflict_quorum_watch",
    "latency_conflict_quorum_block",
)
UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "".join(("mar", "ket")),
    "slug",
    "question",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("tra", "de")),
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "sizing",
    "recommendation",
    "source_id",
    "source_url",
    "source_text",
)
UNSAFE_PUBLIC_VALUE_PATTERNS = (
    "://",
    "credential",
    "password",
    "postgres",
    "private",
    *UNSAFE_PUBLIC_TERMS,
)

PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "event_digest",
    "evidence_group_digest",
    "first_signal_seen_seconds",
    "quorum_confirmed_seconds",
    "latency_seconds",
    "supporting_evidence_count",
    "conflicting_evidence_count",
    "total_evidence_count",
    "quorum_ratio",
    "quorum_gap_pressure",
    "latency_pressure",
    "conflict_ratio",
    "latency_conflict_quorum_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_PAYLOAD_FIELDS = (
    *PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "generated_at",
    "status",
    "observation_count",
    "event_count",
    "evidence_group_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_latency_seconds",
    "average_quorum_ratio",
    "max_latency_pressure",
    "max_quorum_gap_pressure",
    "max_conflict_ratio",
    "average_latency_conflict_quorum_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_PAYLOAD_FIELDS = (
    *PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


@dataclass(frozen=True)
class ResearchEventSourceLatencyConflictQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION
    )
    latency_watch_seconds: Decimal = Decimal("900.000000")
    latency_block_seconds: Decimal = Decimal("3600.000000")
    target_quorum_count: Decimal = Decimal("3.000000")
    quorum_watch_ratio: Decimal = Decimal("0.750000")
    quorum_block_ratio: Decimal = Decimal("0.500000")
    conflict_watch_ratio: Decimal = Decimal("0.250000")
    conflict_block_ratio: Decimal = Decimal("0.500000")
    score_watch_threshold: Decimal = Decimal("0.200000")
    score_block_threshold: Decimal = Decimal("0.650000")
    latency_weight: Decimal = Decimal("0.300000")
    quorum_gap_weight: Decimal = Decimal("0.300000")
    conflict_weight: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceLatencyConflictQuorumConfig:
            raise TypeError(
                "ResearchEventSourceLatencyConflictQuorumConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchEventSourceLatencyConflictQuorumConfig,
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("latency_watch_seconds", "latency_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_quorum_count",
            _normalize_positive_whole_decimal(
                "target_quorum_count",
                self.target_quorum_count,
            ),
        )
        for field_name in (
            "quorum_watch_ratio",
            "quorum_block_ratio",
            "conflict_watch_ratio",
            "conflict_block_ratio",
            "score_watch_threshold",
            "score_block_threshold",
            "latency_weight",
            "quorum_gap_weight",
            "conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.latency_block_seconds <= self.latency_watch_seconds:
            raise ValueError("latency_block_seconds must exceed latency_watch_seconds")
        if self.quorum_block_ratio >= self.quorum_watch_ratio:
            raise ValueError("quorum_block_ratio must be below quorum_watch_ratio")
        if self.conflict_block_ratio <= self.conflict_watch_ratio:
            raise ValueError("conflict_block_ratio must exceed conflict_watch_ratio")
        if self.score_block_threshold <= self.score_watch_threshold:
            raise ValueError("score_block_threshold must exceed score_watch_threshold")
        if self.latency_weight + self.quorum_gap_weight + self.conflict_weight != ONE:
            raise ValueError("score weights must sum to one")
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceLatencyConflictQuorumObservation:
    event_digest: str
    evidence_group_digest: str
    first_signal_seen_seconds: Decimal
    quorum_confirmed_seconds: Decimal
    supporting_evidence_count: Decimal
    conflicting_evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceLatencyConflictQuorumObservation:
            raise TypeError(
                "ResearchEventSourceLatencyConflictQuorumObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchEventSourceLatencyConflictQuorumObservation,
        )
        _require_sha256_digest("event_digest", self.event_digest)
        _require_sha256_digest("evidence_group_digest", self.evidence_group_digest)
        for field_name in ("first_signal_seen_seconds", "quorum_confirmed_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("supporting_evidence_count", "conflicting_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.quorum_confirmed_seconds < self.first_signal_seen_seconds:
            raise ValueError(
                "quorum_confirmed_seconds must be at or after "
                "first_signal_seen_seconds",
            )
        if self.supporting_evidence_count + self.conflicting_evidence_count <= ZERO:
            raise ValueError("total evidence count must be positive")
        _reject_unsafe_public_payload("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventSourceLatencyConflictQuorumRow:
    config_version: str
    event_digest: str
    evidence_group_digest: str
    first_signal_seen_seconds: Decimal
    quorum_confirmed_seconds: Decimal
    latency_seconds: Decimal
    supporting_evidence_count: Decimal
    conflicting_evidence_count: Decimal
    total_evidence_count: Decimal
    quorum_ratio: Decimal
    quorum_gap_pressure: Decimal
    latency_pressure: Decimal
    conflict_ratio: Decimal
    latency_conflict_quorum_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceLatencyConflictQuorumRow:
            raise TypeError(
                "ResearchEventSourceLatencyConflictQuorumRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventSourceLatencyConflictQuorumRow)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_sha256_digest("event_digest", self.event_digest)
        _require_sha256_digest("evidence_group_digest", self.evidence_group_digest)
        for field_name in (
            "first_signal_seen_seconds",
            "quorum_confirmed_seconds",
            "latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "supporting_evidence_count",
            "conflicting_evidence_count",
            "total_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quorum_ratio",
            "quorum_gap_pressure",
            "latency_pressure",
            "conflict_ratio",
            "latency_conflict_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_derived_validation_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventSourceLatencyConflictQuorumReport:
    config_version: str
    generated_at: datetime
    status: str
    observation_count: Decimal
    event_count: Decimal
    evidence_group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_latency_seconds: Decimal
    average_quorum_ratio: Decimal
    max_latency_pressure: Decimal
    max_quorum_gap_pressure: Decimal
    max_conflict_ratio: Decimal
    average_latency_conflict_quorum_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventSourceLatencyConflictQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceLatencyConflictQuorumReport:
            raise TypeError(
                "ResearchEventSourceLatencyConflictQuorumReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventSourceLatencyConflictQuorumReport)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in (
            "observation_count",
            "event_count",
            "evidence_group_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_latency_seconds",
            _normalize_nonnegative_decimal(
                "average_latency_seconds",
                self.average_latency_seconds,
            ),
        )
        for field_name in (
            "average_quorum_ratio",
            "max_latency_pressure",
            "max_quorum_gap_pressure",
            "max_conflict_ratio",
            "average_latency_conflict_quorum_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)
        _validate_report_consistency(self)


def build_research_event_source_latency_conflict_quorum_report(
    observations: Iterable[ResearchEventSourceLatencyConflictQuorumObservation],
    *,
    generated_at: datetime,
    config: ResearchEventSourceLatencyConflictQuorumConfig | None = None,
) -> ResearchEventSourceLatencyConflictQuorumReport:
    """Build a deterministic local report-only latency/conflict quorum snapshot."""

    if config is None:
        config = ResearchEventSourceLatencyConflictQuorumConfig()
    _require_exact_type("config", config, ResearchEventSourceLatencyConflictQuorumConfig)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config)
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventSourceLatencyConflictQuorumReport(
        config_version=config.config_version,
        generated_at=generated_at,
        status=_report_status(rows),
        observation_count=_count(len(normalized_observations)),
        event_count=_count(len({row.event_digest for row in rows})),
        evidence_group_count=_count(len({row.evidence_group_digest for row in rows})),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        average_latency_seconds=_average(tuple(row.latency_seconds for row in rows)),
        average_quorum_ratio=_average(tuple(row.quorum_ratio for row in rows)),
        max_latency_pressure=_max_decimal(tuple(row.latency_pressure for row in rows)),
        max_quorum_gap_pressure=_max_decimal(
            tuple(row.quorum_gap_pressure for row in rows),
        ),
        max_conflict_ratio=_max_decimal(tuple(row.conflict_ratio for row in rows)),
        average_latency_conflict_quorum_score=_average(
            tuple(row.latency_conflict_quorum_score for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_source_latency_conflict_quorum_report_payload(
    report: ResearchEventSourceLatencyConflictQuorumReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchEventSourceLatencyConflictQuorumReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError("report must be a ResearchEventSourceLatencyConflictQuorumReport")


def _row_from_observation(
    observation: ResearchEventSourceLatencyConflictQuorumObservation,
    config: ResearchEventSourceLatencyConflictQuorumConfig,
) -> ResearchEventSourceLatencyConflictQuorumRow:
    _require_exact_type(
        "observation",
        observation,
        ResearchEventSourceLatencyConflictQuorumObservation,
    )
    _require_hard_flags("observation", observation)
    latency_seconds = _quantize_decimal(
        observation.quorum_confirmed_seconds - observation.first_signal_seen_seconds,
    )
    total_evidence_count = _quantize_decimal(
        observation.supporting_evidence_count + observation.conflicting_evidence_count,
    )
    quorum_ratio = _ratio(observation.supporting_evidence_count, config.target_quorum_count)
    quorum_gap_pressure = _quantize_decimal(ONE - quorum_ratio)
    latency_pressure = _pressure(latency_seconds, config.latency_block_seconds)
    conflict_ratio = _ratio(observation.conflicting_evidence_count, total_evidence_count)
    score = _quantize_decimal(
        (latency_pressure * config.latency_weight)
        + (quorum_gap_pressure * config.quorum_gap_weight)
        + (conflict_ratio * config.conflict_weight),
    )
    status = _row_status(
        score,
        config=config,
        quorum_ratio=quorum_ratio,
        conflict_ratio=conflict_ratio,
    )
    return ResearchEventSourceLatencyConflictQuorumRow(
        config_version=config.config_version,
        event_digest=observation.event_digest,
        evidence_group_digest=observation.evidence_group_digest,
        first_signal_seen_seconds=observation.first_signal_seen_seconds,
        quorum_confirmed_seconds=observation.quorum_confirmed_seconds,
        latency_seconds=latency_seconds,
        supporting_evidence_count=observation.supporting_evidence_count,
        conflicting_evidence_count=observation.conflicting_evidence_count,
        total_evidence_count=total_evidence_count,
        quorum_ratio=quorum_ratio,
        quorum_gap_pressure=quorum_gap_pressure,
        latency_pressure=latency_pressure,
        conflict_ratio=conflict_ratio,
        latency_conflict_quorum_score=score,
        status=status,
        reason_codes=_row_reason_codes(
            latency_seconds=latency_seconds,
            quorum_ratio=quorum_ratio,
            conflict_ratio=conflict_ratio,
            status=status,
            config=config,
        ),
    )


def _row_status(
    score: Decimal,
    *,
    config: ResearchEventSourceLatencyConflictQuorumConfig,
    quorum_ratio: Decimal,
    conflict_ratio: Decimal,
) -> str:
    if (
        score >= config.score_block_threshold
        or quorum_ratio < config.quorum_block_ratio
        or conflict_ratio >= config.conflict_block_ratio
    ):
        return "block"
    if (
        score >= config.score_watch_threshold
        or quorum_ratio < config.quorum_watch_ratio
        or conflict_ratio >= config.conflict_watch_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    latency_seconds: Decimal,
    quorum_ratio: Decimal,
    conflict_ratio: Decimal,
    status: str,
    config: ResearchEventSourceLatencyConflictQuorumConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if latency_seconds >= config.latency_block_seconds:
        reason_codes.append("latency_block")
    elif latency_seconds >= config.latency_watch_seconds:
        reason_codes.append("latency_watch")
    if quorum_ratio < config.quorum_block_ratio:
        reason_codes.append("quorum_gap_block")
    elif quorum_ratio < config.quorum_watch_ratio:
        reason_codes.append("quorum_gap_watch")
    if conflict_ratio >= config.conflict_block_ratio:
        reason_codes.append("conflict_block")
    elif conflict_ratio >= config.conflict_watch_ratio:
        reason_codes.append("conflict_watch")
    reason_codes.append(f"latency_conflict_quorum_{status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[ResearchEventSourceLatencyConflictQuorumRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventSourceLatencyConflictQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_public_payload_without_digest(
    report: ResearchEventSourceLatencyConflictQuorumReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "generated_at": _datetime_payload(report.generated_at),
        "status": report.status,
        "observation_count": _decimal_payload(report.observation_count),
        "event_count": _decimal_payload(report.event_count),
        "evidence_group_count": _decimal_payload(report.evidence_group_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_latency_seconds": _decimal_payload(report.average_latency_seconds),
        "average_quorum_ratio": _decimal_payload(report.average_quorum_ratio),
        "max_latency_pressure": _decimal_payload(report.max_latency_pressure),
        "max_quorum_gap_pressure": _decimal_payload(report.max_quorum_gap_pressure),
        "max_conflict_ratio": _decimal_payload(report.max_conflict_ratio),
        "average_latency_conflict_quorum_score": _decimal_payload(
            report.average_latency_conflict_quorum_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(
    row: ResearchEventSourceLatencyConflictQuorumRow,
) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchEventSourceLatencyConflictQuorumRow,
) -> dict[str, object]:
    return {
        "config_version": row.config_version,
        "event_digest": row.event_digest,
        "evidence_group_digest": row.evidence_group_digest,
        "first_signal_seen_seconds": _decimal_payload(row.first_signal_seen_seconds),
        "quorum_confirmed_seconds": _decimal_payload(row.quorum_confirmed_seconds),
        "latency_seconds": _decimal_payload(row.latency_seconds),
        "supporting_evidence_count": _decimal_payload(row.supporting_evidence_count),
        "conflicting_evidence_count": _decimal_payload(row.conflicting_evidence_count),
        "total_evidence_count": _decimal_payload(row.total_evidence_count),
        "quorum_ratio": _decimal_payload(row.quorum_ratio),
        "quorum_gap_pressure": _decimal_payload(row.quorum_gap_pressure),
        "latency_pressure": _decimal_payload(row.latency_pressure),
        "conflict_ratio": _decimal_payload(row.conflict_ratio),
        "latency_conflict_quorum_score": _decimal_payload(
            row.latency_conflict_quorum_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(
    row: ResearchEventSourceLatencyConflictQuorumRow,
) -> str:
    return _derived_validation_digest(
        "research_event_source_latency_conflict_quorum_report_row",
        _row_public_payload_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(
    report: ResearchEventSourceLatencyConflictQuorumReport,
) -> str:
    return _derived_validation_digest(
        "research_event_source_latency_conflict_quorum_report",
        _report_public_payload_without_digest(report),
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _derived_validation_digest(
    label: str,
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> str:
    canonical = json.dumps(
        {field_name: payload[field_name] for field_name in field_names},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()


def _validate_row_derived_validation_digest(
    row: ResearchEventSourceLatencyConflictQuorumRow,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchEventSourceLatencyConflictQuorumReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_row_consistency(row: ResearchEventSourceLatencyConflictQuorumRow) -> None:
    if row.quorum_confirmed_seconds < row.first_signal_seen_seconds:
        raise ValueError("quorum_confirmed_seconds must be at or after first signal")
    if row.latency_seconds != _quantize_decimal(
        row.quorum_confirmed_seconds - row.first_signal_seen_seconds,
    ):
        raise ValueError("latency_seconds must match signal and quorum timing")
    if row.total_evidence_count != _quantize_decimal(
        row.supporting_evidence_count + row.conflicting_evidence_count,
    ):
        raise ValueError("total_evidence_count must match evidence counts")
    if row.total_evidence_count <= ZERO:
        raise ValueError("total evidence count must be positive")
    if f"latency_conflict_quorum_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include the row status reason")


def _validate_report_consistency(
    report: ResearchEventSourceLatencyConflictQuorumReport,
) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.event_count != _count(len({row.event_digest for row in report.rows})):
        raise ValueError("event_count must match rows")
    if report.evidence_group_count != _count(
        len({row.evidence_group_digest for row in report.rows}),
    ):
        raise ValueError("evidence_group_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_latency_seconds != _average(
        tuple(row.latency_seconds for row in report.rows),
    ):
        raise ValueError("average_latency_seconds must match rows")
    if report.average_quorum_ratio != _average(
        tuple(row.quorum_ratio for row in report.rows),
    ):
        raise ValueError("average_quorum_ratio must match rows")
    if report.max_latency_pressure != _max_decimal(
        tuple(row.latency_pressure for row in report.rows),
    ):
        raise ValueError("max_latency_pressure must match rows")
    if report.max_quorum_gap_pressure != _max_decimal(
        tuple(row.quorum_gap_pressure for row in report.rows),
    ):
        raise ValueError("max_quorum_gap_pressure must match rows")
    if report.max_conflict_ratio != _max_decimal(tuple(row.conflict_ratio for row in report.rows)):
        raise ValueError("max_conflict_ratio must match rows")
    if report.average_latency_conflict_quorum_score != _average(
        tuple(row.latency_conflict_quorum_score for row in report.rows),
    ):
        raise ValueError("average_latency_conflict_quorum_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_PAYLOAD_FIELDS, "report")
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_status("status", payload["status"])
    for field_name in (
        "observation_count",
        "event_count",
        "evidence_group_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    _require_decimal_payload_string(
        "average_latency_seconds",
        payload["average_latency_seconds"],
    )
    for field_name in (
        "average_quorum_ratio",
        "max_latency_pressure",
        "max_quorum_gap_pressure",
        "max_conflict_ratio",
        "average_latency_conflict_quorum_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain row payload dictionaries")
        _reject_unsafe_public_payload("row payload", row_payload)
        _validate_public_row_payload(row_payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _normalize_sha256(DERIVED_VALIDATION_DIGEST_FIELD, payload[DERIVED_VALIDATION_DIGEST_FIELD])
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_event_source_latency_conflict_quorum_report",
        payload,
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_ROW_PAYLOAD_FIELDS, "row")
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_EVENT_SOURCE_LATENCY_CONFLICT_QUORUM_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_sha256_digest("event_digest", payload["event_digest"])
    _require_sha256_digest("evidence_group_digest", payload["evidence_group_digest"])
    for field_name in (
        "first_signal_seen_seconds",
        "quorum_confirmed_seconds",
        "latency_seconds",
        "supporting_evidence_count",
        "conflicting_evidence_count",
        "total_evidence_count",
    ):
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            whole=field_name.endswith("_count"),
        )
    for field_name in (
        "quorum_ratio",
        "quorum_gap_pressure",
        "latency_pressure",
        "conflict_ratio",
        "latency_conflict_quorum_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_status("status", payload["status"])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    _normalize_sha256(DERIVED_VALIDATION_DIGEST_FIELD, payload[DERIVED_VALIDATION_DIGEST_FIELD])
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_event_source_latency_conflict_quorum_report_row",
        payload,
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match row payload fields")


def _require_exact_payload_fields(
    payload: dict[str, object],
    field_names: tuple[str, ...],
    label: str,
) -> None:
    missing = [field_name for field_name in field_names if field_name not in payload]
    if missing:
        raise ValueError(f"{missing[0]} is required")
    extra = sorted(set(payload) - set(field_names))
    if extra:
        raise ValueError(f"unexpected {label} payload field: {extra[0]}")


def _normalize_observations(
    values: Iterable[ResearchEventSourceLatencyConflictQuorumObservation],
) -> tuple[ResearchEventSourceLatencyConflictQuorumObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in observations:
        _require_exact_type(
            "observation",
            observation,
            ResearchEventSourceLatencyConflictQuorumObservation,
        )
        _require_hard_flags("observation", observation)
        _reject_unsafe_public_payload("observation", observation)
    return observations


def _normalize_rows(
    values: Iterable[ResearchEventSourceLatencyConflictQuorumRow],
) -> tuple[ResearchEventSourceLatencyConflictQuorumRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        _require_exact_type("row", row, ResearchEventSourceLatencyConflictQuorumRow)
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        _validate_row_derived_validation_digest(row)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(row: ResearchEventSourceLatencyConflictQuorumRow) -> tuple[object, ...]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        -row.latency_conflict_quorum_score,
        row.event_digest,
        row.evidence_group_digest,
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(decimal_value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize_decimal(decimal_value)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return min(ONE, _quantize_decimal(numerator / denominator))


def _pressure(value: Decimal, block_value: Decimal) -> Decimal:
    return min(ONE, _ratio(value, block_value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize_decimal(value), "f")


def _require_datetime_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    _as_utc(field_name, parsed)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:  # pragma: no cover - defensive Decimal adapter.
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if _decimal_payload(decimal_value) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    if probability:
        decimal_value = _normalize_probability_decimal(field_name, decimal_value)
    else:
        decimal_value = _normalize_nonnegative_decimal(field_name, decimal_value)
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal string")
    return decimal_value


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    unique: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if reason_code not in SAFE_REASON_CODES:
            raise ValueError(f"{field_name} contains unknown reason code")
        if reason_code not in unique:
            unique.append(reason_code)
    return tuple(
        reason_code for reason_code in SAFE_REASON_CODES if reason_code in unique
    )


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _normalize_sha256(field_name: str, value: object) -> str:
    _require_sha256_digest(field_name, value)
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if isinstance(value, _DictFlags):
        return value[field_name]
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(label, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    for unsafe_term in UNSAFE_PUBLIC_TERMS:
        if unsafe_term in lowered:
            raise ValueError(f"unsafe public {label}: {unsafe_term}")
    for unsafe_pattern in UNSAFE_PUBLIC_VALUE_PATTERNS:
        if unsafe_pattern in lowered:
            raise ValueError(f"unsafe public {label}: {unsafe_pattern}")


class _DictFlags:
    def __init__(self, value: dict[str, object]) -> None:
        self.value = value

    def __getitem__(self, key: str) -> object:
        if key not in self.value:
            raise ValueError(f"{key} is required")
        return self.value[key]
