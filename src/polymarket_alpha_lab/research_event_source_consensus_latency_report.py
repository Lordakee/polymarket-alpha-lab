"""Pure report-only aggregate event source consensus latency report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Iterable, Mapping


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_CONSENSUS_LATENCY_REPORT_CONFIG_VERSION",
    "ResearchEventSourceConsensusLatencyConfig",
    "ResearchEventSourceConsensusLatencyObservation",
    "ResearchEventSourceConsensusLatencyReport",
    "ResearchEventSourceConsensusLatencyRow",
    "build_research_event_source_consensus_latency_report",
    "research_event_source_consensus_latency_report_payload",
)


DEFAULT_RESEARCH_EVENT_SOURCE_CONSENSUS_LATENCY_REPORT_CONFIG_VERSION = (
    "research-event-source-consensus-latency-report"
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
CONSENSUS_STATUSES = ("pass", "watch", "block")
SAFE_REASON_CODES = (
    "empty_observations",
    "time_to_quorum_watch",
    "time_to_quorum_block",
    "source_class_coverage_watch",
    "source_class_coverage_block",
    "stale_corroboration_watch",
    "stale_corroboration_block",
    "unresolved_disagreement_watch",
    "unresolved_disagreement_block",
    "manual_escalation_watch",
    "manual_escalation_block",
    "consensus_latency_pass",
    "consensus_latency_watch",
    "consensus_latency_block",
)
UNSAFE_PUBLIC_TERMS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
    "".join(("sign", "ing")),
    "".join(("mut", "ation")),
    "".join(("bu", "y")),
    "".join(("se", "ll")),
    "".join(("tra", "de")),
    "".join(("mar", "ket")),
    "".join(("source", "_id")),
)

PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "event_label",
    "source_class_label",
    "first_evidence_seen_seconds",
    "quorum_reached_seconds",
    "time_to_quorum_seconds",
    "expected_source_class_count",
    "observed_source_class_count",
    "source_class_coverage_ratio",
    "stale_corroboration_seconds",
    "stale_corroboration_pressure",
    "unresolved_disagreement_count",
    "unresolved_disagreement_pressure",
    "manual_review_overdue_seconds",
    "manual_escalation_urgency_score",
    "consensus_latency_score",
    "consensus_status",
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
    "consensus_status",
    "observation_count",
    "event_count",
    "source_class_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_time_to_quorum_seconds",
    "average_source_class_coverage_ratio",
    "max_stale_corroboration_pressure",
    "max_unresolved_disagreement_pressure",
    "max_manual_escalation_urgency_score",
    "average_consensus_latency_score",
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
class ResearchEventSourceConsensusLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_CONSENSUS_LATENCY_REPORT_CONFIG_VERSION
    )
    time_to_quorum_watch_seconds: Decimal = Decimal("900.000000")
    time_to_quorum_block_seconds: Decimal = Decimal("3600.000000")
    source_class_coverage_watch_ratio: Decimal = Decimal("0.800000")
    source_class_coverage_block_ratio: Decimal = Decimal("0.500000")
    stale_corroboration_watch_seconds: Decimal = Decimal("1800.000000")
    stale_corroboration_block_seconds: Decimal = Decimal("7200.000000")
    unresolved_disagreement_watch_count: Decimal = Decimal("1.000000")
    unresolved_disagreement_block_count: Decimal = Decimal("3.000000")
    manual_escalation_watch_seconds: Decimal = Decimal("300.000000")
    manual_escalation_block_seconds: Decimal = Decimal("1800.000000")
    consensus_watch_threshold: Decimal = Decimal("0.200000")
    consensus_block_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConsensusLatencyConfig:
            raise TypeError(
                "ResearchEventSourceConsensusLatencyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventSourceConsensusLatencyConfig)
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_CONSENSUS_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "time_to_quorum_watch_seconds",
            "time_to_quorum_block_seconds",
            "stale_corroboration_watch_seconds",
            "stale_corroboration_block_seconds",
            "manual_escalation_watch_seconds",
            "manual_escalation_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_disagreement_watch_count",
            "unresolved_disagreement_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_coverage_watch_ratio",
            "source_class_coverage_block_ratio",
            "consensus_watch_threshold",
            "consensus_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.time_to_quorum_block_seconds <= self.time_to_quorum_watch_seconds:
            raise ValueError(
                "time_to_quorum_block_seconds must exceed "
                "time_to_quorum_watch_seconds",
            )
        if (
            self.stale_corroboration_block_seconds
            <= self.stale_corroboration_watch_seconds
        ):
            raise ValueError(
                "stale_corroboration_block_seconds must exceed "
                "stale_corroboration_watch_seconds",
            )
        if (
            self.unresolved_disagreement_block_count
            <= self.unresolved_disagreement_watch_count
        ):
            raise ValueError(
                "unresolved_disagreement_block_count must exceed "
                "unresolved_disagreement_watch_count",
            )
        if self.manual_escalation_block_seconds <= self.manual_escalation_watch_seconds:
            raise ValueError(
                "manual_escalation_block_seconds must exceed "
                "manual_escalation_watch_seconds",
            )
        if self.source_class_coverage_block_ratio >= self.source_class_coverage_watch_ratio:
            raise ValueError(
                "source_class_coverage_block_ratio must be below "
                "source_class_coverage_watch_ratio",
            )
        if self.consensus_block_threshold <= self.consensus_watch_threshold:
            raise ValueError("consensus_block_threshold must exceed consensus_watch_threshold")
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceConsensusLatencyObservation:
    event_label: str
    source_class_label: str
    first_evidence_seen_seconds: Decimal
    quorum_reached_seconds: Decimal
    expected_source_class_count: Decimal
    observed_source_class_count: Decimal
    stale_corroboration_seconds: Decimal
    unresolved_disagreement_count: Decimal
    manual_review_overdue_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConsensusLatencyObservation:
            raise TypeError(
                "ResearchEventSourceConsensusLatencyObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchEventSourceConsensusLatencyObservation,
        )
        _require_public_label("event_label", self.event_label)
        _require_public_label("source_class_label", self.source_class_label)
        for field_name in (
            "first_evidence_seen_seconds",
            "quorum_reached_seconds",
            "stale_corroboration_seconds",
            "manual_review_overdue_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_source_class_count",
            _normalize_positive_whole_decimal(
                "expected_source_class_count",
                self.expected_source_class_count,
            ),
        )
        object.__setattr__(
            self,
            "observed_source_class_count",
            _normalize_nonnegative_whole_decimal(
                "observed_source_class_count",
                self.observed_source_class_count,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_disagreement_count",
            _normalize_nonnegative_whole_decimal(
                "unresolved_disagreement_count",
                self.unresolved_disagreement_count,
            ),
        )
        if self.quorum_reached_seconds < self.first_evidence_seen_seconds:
            raise ValueError(
                "quorum_reached_seconds must be at or after "
                "first_evidence_seen_seconds",
            )
        if self.observed_source_class_count > self.expected_source_class_count:
            raise ValueError(
                "observed_source_class_count must not exceed "
                "expected_source_class_count",
            )
        _reject_unsafe_public_payload("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventSourceConsensusLatencyRow:
    config_version: str
    event_label: str
    source_class_label: str
    first_evidence_seen_seconds: Decimal
    quorum_reached_seconds: Decimal
    time_to_quorum_seconds: Decimal
    expected_source_class_count: Decimal
    observed_source_class_count: Decimal
    source_class_coverage_ratio: Decimal
    stale_corroboration_seconds: Decimal
    stale_corroboration_pressure: Decimal
    unresolved_disagreement_count: Decimal
    unresolved_disagreement_pressure: Decimal
    manual_review_overdue_seconds: Decimal
    manual_escalation_urgency_score: Decimal
    consensus_latency_score: Decimal
    consensus_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConsensusLatencyRow:
            raise TypeError(
                "ResearchEventSourceConsensusLatencyRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventSourceConsensusLatencyRow)
        for field_name in ("config_version", "event_label", "source_class_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "first_evidence_seen_seconds",
            "quorum_reached_seconds",
            "time_to_quorum_seconds",
            "stale_corroboration_seconds",
            "manual_review_overdue_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_coverage_ratio",
            "stale_corroboration_pressure",
            "unresolved_disagreement_pressure",
            "manual_escalation_urgency_score",
            "consensus_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_source_class_count",
            "observed_source_class_count",
            "unresolved_disagreement_count",
        ):
            normalizer = (
                _normalize_positive_whole_decimal
                if field_name == "expected_source_class_count"
                else _normalize_nonnegative_whole_decimal
            )
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        _require_consensus_status("consensus_status", self.consensus_status)
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
class ResearchEventSourceConsensusLatencyReport:
    config_version: str
    generated_at: datetime
    consensus_status: str
    observation_count: Decimal
    event_count: Decimal
    source_class_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_time_to_quorum_seconds: Decimal
    average_source_class_coverage_ratio: Decimal
    max_stale_corroboration_pressure: Decimal
    max_unresolved_disagreement_pressure: Decimal
    max_manual_escalation_urgency_score: Decimal
    average_consensus_latency_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventSourceConsensusLatencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConsensusLatencyReport:
            raise TypeError(
                "ResearchEventSourceConsensusLatencyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventSourceConsensusLatencyReport)
        _require_public_label("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_consensus_status("consensus_status", self.consensus_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in (
            "observation_count",
            "event_count",
            "source_class_count",
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
            "average_time_to_quorum_seconds",
            _normalize_nonnegative_decimal(
                "average_time_to_quorum_seconds",
                self.average_time_to_quorum_seconds,
            ),
        )
        for field_name in (
            "average_source_class_coverage_ratio",
            "max_stale_corroboration_pressure",
            "max_unresolved_disagreement_pressure",
            "max_manual_escalation_urgency_score",
            "average_consensus_latency_score",
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


def build_research_event_source_consensus_latency_report(
    observations: Iterable[ResearchEventSourceConsensusLatencyObservation],
    *,
    generated_at: datetime,
    config: ResearchEventSourceConsensusLatencyConfig | None = None,
) -> ResearchEventSourceConsensusLatencyReport:
    """Build a deterministic local report-only consensus latency snapshot."""

    if config is None:
        config = ResearchEventSourceConsensusLatencyConfig()
    _require_exact_type("config", config, ResearchEventSourceConsensusLatencyConfig)
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
    return ResearchEventSourceConsensusLatencyReport(
        config_version=config.config_version,
        generated_at=generated_at,
        consensus_status=_report_status(rows),
        observation_count=_count(len(normalized_observations)),
        event_count=_count(len({observation.event_label for observation in normalized_observations})),
        source_class_count=_count(
            len({observation.source_class_label for observation in normalized_observations}),
        ),
        pass_count=_count(sum(1 for row in rows if row.consensus_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.consensus_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.consensus_status == "block")),
        average_time_to_quorum_seconds=_average(
            tuple(row.time_to_quorum_seconds for row in rows),
        ),
        average_source_class_coverage_ratio=_average(
            tuple(row.source_class_coverage_ratio for row in rows),
        ),
        max_stale_corroboration_pressure=_max_decimal(
            tuple(row.stale_corroboration_pressure for row in rows),
        ),
        max_unresolved_disagreement_pressure=_max_decimal(
            tuple(row.unresolved_disagreement_pressure for row in rows),
        ),
        max_manual_escalation_urgency_score=_max_decimal(
            tuple(row.manual_escalation_urgency_score for row in rows),
        ),
        average_consensus_latency_score=_average(
            tuple(row.consensus_latency_score for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_source_consensus_latency_report_payload(
    report: ResearchEventSourceConsensusLatencyReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchEventSourceConsensusLatencyReport:
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
    raise ValueError("report must be a ResearchEventSourceConsensusLatencyReport")


def _row_from_observation(
    observation: ResearchEventSourceConsensusLatencyObservation,
    config: ResearchEventSourceConsensusLatencyConfig,
) -> ResearchEventSourceConsensusLatencyRow:
    _require_exact_type(
        "observation",
        observation,
        ResearchEventSourceConsensusLatencyObservation,
    )
    _require_hard_flags("observation", observation)
    _reject_unsafe_public_payload("observation", observation)
    time_to_quorum = _quantize_decimal(
        observation.quorum_reached_seconds - observation.first_evidence_seen_seconds,
    )
    coverage_ratio = _ratio(
        observation.observed_source_class_count,
        observation.expected_source_class_count,
    )
    stale_pressure = _pressure(
        observation.stale_corroboration_seconds,
        config.stale_corroboration_block_seconds,
    )
    disagreement_pressure = _pressure(
        observation.unresolved_disagreement_count,
        config.unresolved_disagreement_block_count,
    )
    manual_urgency = _pressure(
        observation.manual_review_overdue_seconds,
        config.manual_escalation_block_seconds,
    )
    consensus_score = _average(
        (
            _pressure(time_to_quorum, config.time_to_quorum_block_seconds),
            ONE - coverage_ratio,
            stale_pressure,
            disagreement_pressure,
            manual_urgency,
        ),
    )
    consensus_status = _consensus_status(
        consensus_score,
        config=config,
        coverage_ratio=coverage_ratio,
    )
    return ResearchEventSourceConsensusLatencyRow(
        config_version=config.config_version,
        event_label=observation.event_label,
        source_class_label=observation.source_class_label,
        first_evidence_seen_seconds=observation.first_evidence_seen_seconds,
        quorum_reached_seconds=observation.quorum_reached_seconds,
        time_to_quorum_seconds=time_to_quorum,
        expected_source_class_count=observation.expected_source_class_count,
        observed_source_class_count=observation.observed_source_class_count,
        source_class_coverage_ratio=coverage_ratio,
        stale_corroboration_seconds=observation.stale_corroboration_seconds,
        stale_corroboration_pressure=stale_pressure,
        unresolved_disagreement_count=observation.unresolved_disagreement_count,
        unresolved_disagreement_pressure=disagreement_pressure,
        manual_review_overdue_seconds=observation.manual_review_overdue_seconds,
        manual_escalation_urgency_score=manual_urgency,
        consensus_latency_score=consensus_score,
        consensus_status=consensus_status,
        reason_codes=_row_reason_codes(
            observation,
            config=config,
            coverage_ratio=coverage_ratio,
            time_to_quorum=time_to_quorum,
            consensus_status=consensus_status,
        ),
    )


def _row_reason_codes(
    observation: ResearchEventSourceConsensusLatencyObservation,
    *,
    config: ResearchEventSourceConsensusLatencyConfig,
    coverage_ratio: Decimal,
    time_to_quorum: Decimal,
    consensus_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if time_to_quorum >= config.time_to_quorum_block_seconds:
        reason_codes.append("time_to_quorum_block")
    elif time_to_quorum >= config.time_to_quorum_watch_seconds:
        reason_codes.append("time_to_quorum_watch")
    if coverage_ratio < config.source_class_coverage_block_ratio:
        reason_codes.append("source_class_coverage_block")
    elif coverage_ratio < config.source_class_coverage_watch_ratio:
        reason_codes.append("source_class_coverage_watch")
    if observation.stale_corroboration_seconds >= config.stale_corroboration_block_seconds:
        reason_codes.append("stale_corroboration_block")
    elif observation.stale_corroboration_seconds >= config.stale_corroboration_watch_seconds:
        reason_codes.append("stale_corroboration_watch")
    if observation.unresolved_disagreement_count >= config.unresolved_disagreement_block_count:
        reason_codes.append("unresolved_disagreement_block")
    elif observation.unresolved_disagreement_count >= config.unresolved_disagreement_watch_count:
        reason_codes.append("unresolved_disagreement_watch")
    if observation.manual_review_overdue_seconds >= config.manual_escalation_block_seconds:
        reason_codes.append("manual_escalation_block")
    elif observation.manual_review_overdue_seconds >= config.manual_escalation_watch_seconds:
        reason_codes.append("manual_escalation_watch")
    reason_codes.append(f"consensus_latency_{consensus_status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _consensus_status(
    consensus_latency_score: Decimal,
    *,
    config: ResearchEventSourceConsensusLatencyConfig,
    coverage_ratio: Decimal,
) -> str:
    if (
        consensus_latency_score >= config.consensus_block_threshold
        or coverage_ratio < config.source_class_coverage_block_ratio
    ):
        return "block"
    if (
        consensus_latency_score >= config.consensus_watch_threshold
        or coverage_ratio < config.source_class_coverage_watch_ratio
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventSourceConsensusLatencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.consensus_status == "block" for row in rows):
        return "block"
    if any(row.consensus_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventSourceConsensusLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_public_payload_without_digest(
    report: ResearchEventSourceConsensusLatencyReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "generated_at": _datetime_payload(report.generated_at),
        "consensus_status": report.consensus_status,
        "observation_count": _decimal_payload(report.observation_count),
        "event_count": _decimal_payload(report.event_count),
        "source_class_count": _decimal_payload(report.source_class_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_time_to_quorum_seconds": _decimal_payload(
            report.average_time_to_quorum_seconds,
        ),
        "average_source_class_coverage_ratio": _decimal_payload(
            report.average_source_class_coverage_ratio,
        ),
        "max_stale_corroboration_pressure": _decimal_payload(
            report.max_stale_corroboration_pressure,
        ),
        "max_unresolved_disagreement_pressure": _decimal_payload(
            report.max_unresolved_disagreement_pressure,
        ),
        "max_manual_escalation_urgency_score": _decimal_payload(
            report.max_manual_escalation_urgency_score,
        ),
        "average_consensus_latency_score": _decimal_payload(
            report.average_consensus_latency_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: ResearchEventSourceConsensusLatencyRow) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchEventSourceConsensusLatencyRow,
) -> dict[str, object]:
    return {
        "config_version": row.config_version,
        "event_label": row.event_label,
        "source_class_label": row.source_class_label,
        "first_evidence_seen_seconds": _decimal_payload(row.first_evidence_seen_seconds),
        "quorum_reached_seconds": _decimal_payload(row.quorum_reached_seconds),
        "time_to_quorum_seconds": _decimal_payload(row.time_to_quorum_seconds),
        "expected_source_class_count": _decimal_payload(row.expected_source_class_count),
        "observed_source_class_count": _decimal_payload(row.observed_source_class_count),
        "source_class_coverage_ratio": _decimal_payload(row.source_class_coverage_ratio),
        "stale_corroboration_seconds": _decimal_payload(row.stale_corroboration_seconds),
        "stale_corroboration_pressure": _decimal_payload(
            row.stale_corroboration_pressure,
        ),
        "unresolved_disagreement_count": _decimal_payload(row.unresolved_disagreement_count),
        "unresolved_disagreement_pressure": _decimal_payload(
            row.unresolved_disagreement_pressure,
        ),
        "manual_review_overdue_seconds": _decimal_payload(row.manual_review_overdue_seconds),
        "manual_escalation_urgency_score": _decimal_payload(
            row.manual_escalation_urgency_score,
        ),
        "consensus_latency_score": _decimal_payload(row.consensus_latency_score),
        "consensus_status": row.consensus_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(row: ResearchEventSourceConsensusLatencyRow) -> str:
    return _derived_validation_digest(
        "research_event_source_consensus_latency_report_row",
        _row_public_payload_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(
    report: ResearchEventSourceConsensusLatencyReport,
) -> str:
    return _derived_validation_digest(
        "research_event_source_consensus_latency_report",
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
    row: ResearchEventSourceConsensusLatencyRow,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchEventSourceConsensusLatencyReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_row_consistency(row: ResearchEventSourceConsensusLatencyRow) -> None:
    if row.quorum_reached_seconds < row.first_evidence_seen_seconds:
        raise ValueError("quorum_reached_seconds must be at or after first evidence")
    if row.time_to_quorum_seconds != _quantize_decimal(
        row.quorum_reached_seconds - row.first_evidence_seen_seconds,
    ):
        raise ValueError("time_to_quorum_seconds must match evidence and quorum timing")
    if row.observed_source_class_count > row.expected_source_class_count:
        raise ValueError(
            "observed_source_class_count must not exceed expected_source_class_count",
        )
    if row.source_class_coverage_ratio != _ratio(
        row.observed_source_class_count,
        row.expected_source_class_count,
    ):
        raise ValueError("source_class_coverage_ratio must match source class counts")
    if f"consensus_latency_{row.consensus_status}" not in row.reason_codes:
        raise ValueError("reason_codes must include the consensus status reason")


def _validate_report_consistency(
    report: ResearchEventSourceConsensusLatencyReport,
) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.event_count != _count(len({row.event_label for row in report.rows})):
        raise ValueError("event_count must match rows")
    if report.source_class_count != _count(
        len({row.source_class_label for row in report.rows}),
    ):
        raise ValueError("source_class_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in report.rows if row.consensus_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.consensus_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in report.rows if row.consensus_status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_time_to_quorum_seconds != _average(
        tuple(row.time_to_quorum_seconds for row in report.rows),
    ):
        raise ValueError("average_time_to_quorum_seconds must match rows")
    if report.average_source_class_coverage_ratio != _average(
        tuple(row.source_class_coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_source_class_coverage_ratio must match rows")
    if report.max_stale_corroboration_pressure != _max_decimal(
        tuple(row.stale_corroboration_pressure for row in report.rows),
    ):
        raise ValueError("max_stale_corroboration_pressure must match rows")
    if report.max_unresolved_disagreement_pressure != _max_decimal(
        tuple(row.unresolved_disagreement_pressure for row in report.rows),
    ):
        raise ValueError("max_unresolved_disagreement_pressure must match rows")
    if report.max_manual_escalation_urgency_score != _max_decimal(
        tuple(row.manual_escalation_urgency_score for row in report.rows),
    ):
        raise ValueError("max_manual_escalation_urgency_score must match rows")
    if report.average_consensus_latency_score != _average(
        tuple(row.consensus_latency_score for row in report.rows),
    ):
        raise ValueError("average_consensus_latency_score must match rows")
    if report.consensus_status != _report_status(report.rows):
        raise ValueError("consensus_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_PAYLOAD_FIELDS, "report")
    _require_public_label("config_version", payload["config_version"])
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_consensus_status("consensus_status", payload["consensus_status"])
    for field_name in (
        "observation_count",
        "event_count",
        "source_class_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    _require_decimal_payload_string(
        "average_time_to_quorum_seconds",
        payload["average_time_to_quorum_seconds"],
    )
    for field_name in (
        "average_source_class_coverage_ratio",
        "max_stale_corroboration_pressure",
        "max_unresolved_disagreement_pressure",
        "max_manual_escalation_urgency_score",
        "average_consensus_latency_score",
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
        "research_event_source_consensus_latency_report",
        payload,
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_ROW_PAYLOAD_FIELDS, "row")
    for field_name in ("config_version", "event_label", "source_class_label"):
        _require_public_label(field_name, payload[field_name])
    for field_name in (
        "first_evidence_seen_seconds",
        "quorum_reached_seconds",
        "time_to_quorum_seconds",
        "expected_source_class_count",
        "observed_source_class_count",
        "stale_corroboration_seconds",
        "unresolved_disagreement_count",
        "manual_review_overdue_seconds",
    ):
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            whole=field_name
            in {
                "expected_source_class_count",
                "observed_source_class_count",
                "unresolved_disagreement_count",
            },
        )
    for field_name in (
        "source_class_coverage_ratio",
        "stale_corroboration_pressure",
        "unresolved_disagreement_pressure",
        "manual_escalation_urgency_score",
        "consensus_latency_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_consensus_status("consensus_status", payload["consensus_status"])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    _normalize_sha256(DERIVED_VALIDATION_DIGEST_FIELD, payload[DERIVED_VALIDATION_DIGEST_FIELD])
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_event_source_consensus_latency_report_row",
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
    values: Iterable[ResearchEventSourceConsensusLatencyObservation],
) -> tuple[ResearchEventSourceConsensusLatencyObservation, ...]:
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
            ResearchEventSourceConsensusLatencyObservation,
        )
        _require_hard_flags("observation", observation)
        _reject_unsafe_public_payload("observation", observation)
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.event_label,
                observation.source_class_label,
                observation.first_evidence_seen_seconds,
            ),
        ),
    )


def _normalize_rows(value: object) -> tuple[ResearchEventSourceConsensusLatencyRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchEventSourceConsensusLatencyRow] = []
    for row in value:
        _require_exact_type("row", row, ResearchEventSourceConsensusLatencyRow)
        _require_hard_flags("row", row)
        _validate_row_derived_validation_digest(row)
        rows.append(row)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchEventSourceConsensusLatencyRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -row.consensus_latency_score,
        -row.time_to_quorum_seconds,
        row.event_label,
        row.source_class_label,
    )


def _pressure(value: Decimal, block_threshold: Decimal) -> Decimal:
    if block_threshold <= ZERO:
        raise ValueError("block threshold must be positive")
    return _cap_probability(value / block_threshold)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _cap_probability(numerator / denominator)


def _cap_probability(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_label(field_name, reason_code)
        if reason_code not in SAFE_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in SAFE_REASON_CODES if reason_code in seen)


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    codes: list[str] = []
    for reason_code in value:
        _require_public_label(field_name, reason_code)
        if reason_code not in SAFE_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        codes.append(reason_code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(codes)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public aggregate label")
    return value


def _require_consensus_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in CONSENSUS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return str(value)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_datetime_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
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
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(parsed)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if str(normalized) != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal string")
    return normalized


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} numeric values must be Decimal-backed")
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
