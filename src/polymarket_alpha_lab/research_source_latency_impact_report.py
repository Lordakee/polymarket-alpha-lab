"""Pure report-only aggregate source-latency impact report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Iterable, Mapping


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_LATENCY_IMPACT_REPORT_CONFIG_VERSION",
    "ResearchSourceLatencyImpactConfig",
    "ResearchSourceLatencyImpactObservation",
    "ResearchSourceLatencyImpactReport",
    "ResearchSourceLatencyImpactRow",
    "build_research_source_latency_impact_report",
    "research_source_latency_impact_report_payload",
)


DEFAULT_RESEARCH_SOURCE_LATENCY_IMPACT_REPORT_CONFIG_VERSION = (
    "research-source-latency-impact-report"
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DOMAIN_LIKE_RE = re.compile(
    r"(?:^|[._-])[a-z0-9-]+\."
    r"(?:ai|app|co|com|dev|edu|gov|io|net|org|test|xyz)"
    r"(?:$|[._-])",
)
RAW_PUBLIC_ID_RE = re.compile(
    r"(?:^|[._-])0x[0-9a-f]{8,}(?:$|[._-])"
    r"|(?:^|[._-])[0-9a-f]{8}-[0-9a-f]{4}-"
    r"[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?:$|[._-])",
)
IMPACT_STATUSES = ("pass", "watch", "block")
SAFE_REASON_CODES = (
    "empty_observations",
    "retrieval_delay_watch",
    "retrieval_delay_block",
    "stale_evidence_watch",
    "stale_evidence_block",
    "source_class_coverage_watch",
    "source_class_coverage_block",
    "contradiction_lag_watch",
    "contradiction_lag_block",
    "recheck_urgency_watch",
    "recheck_urgency_block",
    "latency_impact_pass",
    "latency_impact_watch",
    "latency_impact_block",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "private_key",
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_text",
    "raw_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "decision_label",
    "source_class_label",
    "retrieval_delay_seconds",
    "evidence_age_seconds",
    "stale_evidence_pressure",
    "source_class_expected_count",
    "source_class_observed_count",
    "source_class_coverage_ratio",
    "contradiction_lag_seconds",
    "contradiction_lag_pressure",
    "recheck_overdue_seconds",
    "recheck_urgency_score",
    "latency_impact_score",
    "impact_status",
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
    "impact_status",
    "observation_count",
    "decision_count",
    "source_class_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_retrieval_delay_seconds",
    "average_stale_evidence_pressure",
    "average_source_class_coverage_ratio",
    "max_contradiction_lag_seconds",
    "max_recheck_urgency_score",
    "average_latency_impact_score",
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
class ResearchSourceLatencyImpactConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_LATENCY_IMPACT_REPORT_CONFIG_VERSION
    retrieval_delay_watch_seconds: Decimal = Decimal("600.000000")
    retrieval_delay_block_seconds: Decimal = Decimal("1800.000000")
    stale_evidence_watch_seconds: Decimal = Decimal("1800.000000")
    stale_evidence_block_seconds: Decimal = Decimal("7200.000000")
    source_class_coverage_watch_ratio: Decimal = Decimal("0.800000")
    source_class_coverage_block_ratio: Decimal = Decimal("0.500000")
    contradiction_lag_watch_seconds: Decimal = Decimal("900.000000")
    contradiction_lag_block_seconds: Decimal = Decimal("3600.000000")
    recheck_urgency_watch_seconds: Decimal = Decimal("300.000000")
    recheck_urgency_block_seconds: Decimal = Decimal("1800.000000")
    impact_watch_threshold: Decimal = Decimal("0.200000")
    impact_block_threshold: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceLatencyImpactConfig:
            raise TypeError(
                "ResearchSourceLatencyImpactConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceLatencyImpactConfig)
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_LATENCY_IMPACT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "retrieval_delay_watch_seconds",
            "retrieval_delay_block_seconds",
            "stale_evidence_watch_seconds",
            "stale_evidence_block_seconds",
            "contradiction_lag_watch_seconds",
            "contradiction_lag_block_seconds",
            "recheck_urgency_watch_seconds",
            "recheck_urgency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_coverage_watch_ratio",
            "source_class_coverage_block_ratio",
            "impact_watch_threshold",
            "impact_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.retrieval_delay_block_seconds <= self.retrieval_delay_watch_seconds:
            raise ValueError(
                "retrieval_delay_block_seconds must exceed retrieval_delay_watch_seconds",
            )
        if self.stale_evidence_block_seconds <= self.stale_evidence_watch_seconds:
            raise ValueError(
                "stale_evidence_block_seconds must exceed stale_evidence_watch_seconds",
            )
        if self.contradiction_lag_block_seconds <= self.contradiction_lag_watch_seconds:
            raise ValueError(
                "contradiction_lag_block_seconds must exceed "
                "contradiction_lag_watch_seconds",
            )
        if self.recheck_urgency_block_seconds <= self.recheck_urgency_watch_seconds:
            raise ValueError(
                "recheck_urgency_block_seconds must exceed "
                "recheck_urgency_watch_seconds",
            )
        if self.source_class_coverage_block_ratio >= self.source_class_coverage_watch_ratio:
            raise ValueError(
                "source_class_coverage_block_ratio must be below "
                "source_class_coverage_watch_ratio",
            )
        if self.impact_block_threshold <= self.impact_watch_threshold:
            raise ValueError("impact_block_threshold must exceed impact_watch_threshold")
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceLatencyImpactObservation:
    decision_label: str
    source_class_label: str
    retrieval_delay_seconds: Decimal
    evidence_age_seconds: Decimal
    source_class_expected_count: Decimal
    source_class_observed_count: Decimal
    contradiction_lag_seconds: Decimal
    recheck_overdue_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceLatencyImpactObservation:
            raise TypeError(
                "ResearchSourceLatencyImpactObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("observation", self, ResearchSourceLatencyImpactObservation)
        _require_public_label("decision_label", self.decision_label)
        _require_public_label("source_class_label", self.source_class_label)
        for field_name in (
            "retrieval_delay_seconds",
            "evidence_age_seconds",
            "contradiction_lag_seconds",
            "recheck_overdue_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_class_expected_count",
            _normalize_positive_whole_decimal(
                "source_class_expected_count",
                self.source_class_expected_count,
            ),
        )
        object.__setattr__(
            self,
            "source_class_observed_count",
            _normalize_nonnegative_whole_decimal(
                "source_class_observed_count",
                self.source_class_observed_count,
            ),
        )
        if self.source_class_observed_count > self.source_class_expected_count:
            raise ValueError(
                "source_class_observed_count must not exceed "
                "source_class_expected_count",
            )
        _reject_unsafe_public_payload("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceLatencyImpactRow:
    config_version: str
    decision_label: str
    source_class_label: str
    retrieval_delay_seconds: Decimal
    evidence_age_seconds: Decimal
    stale_evidence_pressure: Decimal
    source_class_expected_count: Decimal
    source_class_observed_count: Decimal
    source_class_coverage_ratio: Decimal
    contradiction_lag_seconds: Decimal
    contradiction_lag_pressure: Decimal
    recheck_overdue_seconds: Decimal
    recheck_urgency_score: Decimal
    latency_impact_score: Decimal
    impact_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceLatencyImpactRow:
            raise TypeError("ResearchSourceLatencyImpactRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceLatencyImpactRow)
        for field_name in ("config_version", "decision_label", "source_class_label"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "retrieval_delay_seconds",
            "evidence_age_seconds",
            "contradiction_lag_seconds",
            "recheck_overdue_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_evidence_pressure",
            "source_class_coverage_ratio",
            "contradiction_lag_pressure",
            "recheck_urgency_score",
            "latency_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_class_expected_count",
            _normalize_positive_whole_decimal(
                "source_class_expected_count",
                self.source_class_expected_count,
            ),
        )
        object.__setattr__(
            self,
            "source_class_observed_count",
            _normalize_nonnegative_whole_decimal(
                "source_class_observed_count",
                self.source_class_observed_count,
            ),
        )
        _require_impact_status("impact_status", self.impact_status)
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
class ResearchSourceLatencyImpactReport:
    config_version: str
    generated_at: datetime
    impact_status: str
    observation_count: Decimal
    decision_count: Decimal
    source_class_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_retrieval_delay_seconds: Decimal
    average_stale_evidence_pressure: Decimal
    average_source_class_coverage_ratio: Decimal
    max_contradiction_lag_seconds: Decimal
    max_recheck_urgency_score: Decimal
    average_latency_impact_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceLatencyImpactRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceLatencyImpactReport:
            raise TypeError("ResearchSourceLatencyImpactReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceLatencyImpactReport)
        _require_public_label("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_impact_status("impact_status", self.impact_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in (
            "observation_count",
            "decision_count",
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
        for field_name in (
            "average_retrieval_delay_seconds",
            "max_contradiction_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_stale_evidence_pressure",
            "average_source_class_coverage_ratio",
            "max_recheck_urgency_score",
            "average_latency_impact_score",
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


def build_research_source_latency_impact_report(
    observations: Iterable[ResearchSourceLatencyImpactObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceLatencyImpactConfig | None = None,
) -> ResearchSourceLatencyImpactReport:
    """Build a deterministic local report-only aggregate latency impact snapshot."""

    if config is None:
        config = ResearchSourceLatencyImpactConfig()
    _require_exact_type("config", config, ResearchSourceLatencyImpactConfig)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(observation, config) for observation in normalized_observations),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceLatencyImpactReport(
        config_version=config.config_version,
        generated_at=generated_at,
        impact_status=_report_status(rows),
        observation_count=_count(len(normalized_observations)),
        decision_count=_count(
            len({observation.decision_label for observation in normalized_observations}),
        ),
        source_class_count=_count(
            len({observation.source_class_label for observation in normalized_observations}),
        ),
        pass_count=_count(sum(1 for row in rows if row.impact_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.impact_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.impact_status == "block")),
        average_retrieval_delay_seconds=_average(
            tuple(row.retrieval_delay_seconds for row in rows),
        ),
        average_stale_evidence_pressure=_average(
            tuple(row.stale_evidence_pressure for row in rows),
        ),
        average_source_class_coverage_ratio=_average(
            tuple(row.source_class_coverage_ratio for row in rows),
        ),
        max_contradiction_lag_seconds=_max_decimal(
            tuple(row.contradiction_lag_seconds for row in rows),
        ),
        max_recheck_urgency_score=_max_decimal(
            tuple(row.recheck_urgency_score for row in rows),
        ),
        average_latency_impact_score=_average(
            tuple(row.latency_impact_score for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_latency_impact_report_payload(
    report: ResearchSourceLatencyImpactReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceLatencyImpactReport:
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
    raise ValueError("report must be a ResearchSourceLatencyImpactReport")


def _row_from_observation(
    observation: ResearchSourceLatencyImpactObservation,
    config: ResearchSourceLatencyImpactConfig,
) -> ResearchSourceLatencyImpactRow:
    _require_exact_type("observation", observation, ResearchSourceLatencyImpactObservation)
    _require_hard_flags("observation", observation)
    _reject_unsafe_public_payload("observation", observation)
    stale_pressure = _pressure(
        observation.evidence_age_seconds,
        config.stale_evidence_block_seconds,
    )
    coverage_ratio = _ratio(
        observation.source_class_observed_count,
        observation.source_class_expected_count,
    )
    contradiction_pressure = _pressure(
        observation.contradiction_lag_seconds,
        config.contradiction_lag_block_seconds,
    )
    recheck_urgency = _pressure(
        observation.recheck_overdue_seconds,
        config.recheck_urgency_block_seconds,
    )
    latency_impact_score = _average(
        (
            _pressure(
                observation.retrieval_delay_seconds,
                config.retrieval_delay_block_seconds,
            ),
            stale_pressure,
            ONE - coverage_ratio,
            contradiction_pressure,
            recheck_urgency,
        ),
    )
    impact_status = _impact_status(
        latency_impact_score,
        config=config,
        coverage_ratio=coverage_ratio,
    )
    return ResearchSourceLatencyImpactRow(
        config_version=config.config_version,
        decision_label=observation.decision_label,
        source_class_label=observation.source_class_label,
        retrieval_delay_seconds=observation.retrieval_delay_seconds,
        evidence_age_seconds=observation.evidence_age_seconds,
        stale_evidence_pressure=stale_pressure,
        source_class_expected_count=observation.source_class_expected_count,
        source_class_observed_count=observation.source_class_observed_count,
        source_class_coverage_ratio=coverage_ratio,
        contradiction_lag_seconds=observation.contradiction_lag_seconds,
        contradiction_lag_pressure=contradiction_pressure,
        recheck_overdue_seconds=observation.recheck_overdue_seconds,
        recheck_urgency_score=recheck_urgency,
        latency_impact_score=latency_impact_score,
        impact_status=impact_status,
        reason_codes=_row_reason_codes(
            observation,
            config=config,
            coverage_ratio=coverage_ratio,
            impact_status=impact_status,
        ),
    )


def _row_reason_codes(
    observation: ResearchSourceLatencyImpactObservation,
    *,
    config: ResearchSourceLatencyImpactConfig,
    coverage_ratio: Decimal,
    impact_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.retrieval_delay_seconds >= config.retrieval_delay_block_seconds:
        reason_codes.append("retrieval_delay_block")
    elif observation.retrieval_delay_seconds >= config.retrieval_delay_watch_seconds:
        reason_codes.append("retrieval_delay_watch")
    if observation.evidence_age_seconds >= config.stale_evidence_block_seconds:
        reason_codes.append("stale_evidence_block")
    elif observation.evidence_age_seconds >= config.stale_evidence_watch_seconds:
        reason_codes.append("stale_evidence_watch")
    if coverage_ratio < config.source_class_coverage_block_ratio:
        reason_codes.append("source_class_coverage_block")
    elif coverage_ratio < config.source_class_coverage_watch_ratio:
        reason_codes.append("source_class_coverage_watch")
    if observation.contradiction_lag_seconds >= config.contradiction_lag_block_seconds:
        reason_codes.append("contradiction_lag_block")
    elif observation.contradiction_lag_seconds >= config.contradiction_lag_watch_seconds:
        reason_codes.append("contradiction_lag_watch")
    if observation.recheck_overdue_seconds >= config.recheck_urgency_block_seconds:
        reason_codes.append("recheck_urgency_block")
    elif observation.recheck_overdue_seconds >= config.recheck_urgency_watch_seconds:
        reason_codes.append("recheck_urgency_watch")
    reason_codes.append(f"latency_impact_{impact_status}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _impact_status(
    latency_impact_score: Decimal,
    *,
    config: ResearchSourceLatencyImpactConfig,
    coverage_ratio: Decimal,
) -> str:
    if (
        latency_impact_score >= config.impact_block_threshold
        or coverage_ratio < config.source_class_coverage_block_ratio
    ):
        return "block"
    if (
        latency_impact_score >= config.impact_watch_threshold
        or coverage_ratio < config.source_class_coverage_watch_ratio
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceLatencyImpactRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.impact_status == "block" for row in rows):
        return "block"
    if any(row.impact_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchSourceLatencyImpactRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_public_payload_without_digest(
    report: ResearchSourceLatencyImpactReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "generated_at": _datetime_payload(report.generated_at),
        "impact_status": report.impact_status,
        "observation_count": _decimal_payload(report.observation_count),
        "decision_count": _decimal_payload(report.decision_count),
        "source_class_count": _decimal_payload(report.source_class_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_retrieval_delay_seconds": _decimal_payload(
            report.average_retrieval_delay_seconds,
        ),
        "average_stale_evidence_pressure": _decimal_payload(
            report.average_stale_evidence_pressure,
        ),
        "average_source_class_coverage_ratio": _decimal_payload(
            report.average_source_class_coverage_ratio,
        ),
        "max_contradiction_lag_seconds": _decimal_payload(
            report.max_contradiction_lag_seconds,
        ),
        "max_recheck_urgency_score": _decimal_payload(
            report.max_recheck_urgency_score,
        ),
        "average_latency_impact_score": _decimal_payload(
            report.average_latency_impact_score,
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: ResearchSourceLatencyImpactRow) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_without_digest(
    row: ResearchSourceLatencyImpactRow,
) -> dict[str, object]:
    return {
        "config_version": row.config_version,
        "decision_label": row.decision_label,
        "source_class_label": row.source_class_label,
        "retrieval_delay_seconds": _decimal_payload(row.retrieval_delay_seconds),
        "evidence_age_seconds": _decimal_payload(row.evidence_age_seconds),
        "stale_evidence_pressure": _decimal_payload(row.stale_evidence_pressure),
        "source_class_expected_count": _decimal_payload(row.source_class_expected_count),
        "source_class_observed_count": _decimal_payload(row.source_class_observed_count),
        "source_class_coverage_ratio": _decimal_payload(row.source_class_coverage_ratio),
        "contradiction_lag_seconds": _decimal_payload(row.contradiction_lag_seconds),
        "contradiction_lag_pressure": _decimal_payload(row.contradiction_lag_pressure),
        "recheck_overdue_seconds": _decimal_payload(row.recheck_overdue_seconds),
        "recheck_urgency_score": _decimal_payload(row.recheck_urgency_score),
        "latency_impact_score": _decimal_payload(row.latency_impact_score),
        "impact_status": row.impact_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(row: ResearchSourceLatencyImpactRow) -> str:
    return _derived_validation_digest(
        "research_source_latency_impact_report_row",
        _row_public_payload_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(report: ResearchSourceLatencyImpactReport) -> str:
    return _derived_validation_digest(
        "research_source_latency_impact_report",
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


def _validate_row_derived_validation_digest(row: ResearchSourceLatencyImpactRow) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchSourceLatencyImpactReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_row_consistency(row: ResearchSourceLatencyImpactRow) -> None:
    if row.source_class_observed_count > row.source_class_expected_count:
        raise ValueError(
            "source_class_observed_count must not exceed source_class_expected_count",
        )
    if row.source_class_coverage_ratio != _ratio(
        row.source_class_observed_count,
        row.source_class_expected_count,
    ):
        raise ValueError("source_class_coverage_ratio must match source class counts")
    if f"latency_impact_{row.impact_status}" not in row.reason_codes:
        raise ValueError("reason_codes must include the impact status reason")


def _validate_report_consistency(report: ResearchSourceLatencyImpactReport) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.decision_count != _count(len({row.decision_label for row in report.rows})):
        raise ValueError("decision_count must match rows")
    if report.source_class_count != _count(
        len({row.source_class_label for row in report.rows}),
    ):
        raise ValueError("source_class_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in report.rows if row.impact_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.impact_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in report.rows if row.impact_status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_retrieval_delay_seconds != _average(
        tuple(row.retrieval_delay_seconds for row in report.rows),
    ):
        raise ValueError("average_retrieval_delay_seconds must match rows")
    if report.average_stale_evidence_pressure != _average(
        tuple(row.stale_evidence_pressure for row in report.rows),
    ):
        raise ValueError("average_stale_evidence_pressure must match rows")
    if report.average_source_class_coverage_ratio != _average(
        tuple(row.source_class_coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_source_class_coverage_ratio must match rows")
    if report.max_contradiction_lag_seconds != _max_decimal(
        tuple(row.contradiction_lag_seconds for row in report.rows),
    ):
        raise ValueError("max_contradiction_lag_seconds must match rows")
    if report.max_recheck_urgency_score != _max_decimal(
        tuple(row.recheck_urgency_score for row in report.rows),
    ):
        raise ValueError("max_recheck_urgency_score must match rows")
    if report.average_latency_impact_score != _average(
        tuple(row.latency_impact_score for row in report.rows),
    ):
        raise ValueError("average_latency_impact_score must match rows")
    if report.impact_status != _report_status(report.rows):
        raise ValueError("impact_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_PAYLOAD_FIELDS, "report")
    _require_public_label("config_version", payload["config_version"])
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_impact_status("impact_status", payload["impact_status"])
    for field_name in (
        "observation_count",
        "decision_count",
        "source_class_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "average_retrieval_delay_seconds",
        "max_contradiction_lag_seconds",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    for field_name in (
        "average_stale_evidence_pressure",
        "average_source_class_coverage_ratio",
        "max_recheck_urgency_score",
        "average_latency_impact_score",
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
        "research_source_latency_impact_report",
        payload,
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_ROW_PAYLOAD_FIELDS, "row")
    for field_name in ("config_version", "decision_label", "source_class_label"):
        _require_public_label(field_name, payload[field_name])
    for field_name in (
        "retrieval_delay_seconds",
        "evidence_age_seconds",
        "source_class_expected_count",
        "source_class_observed_count",
        "contradiction_lag_seconds",
        "recheck_overdue_seconds",
    ):
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            whole=field_name
            in {
                "source_class_expected_count",
                "source_class_observed_count",
            },
        )
    for field_name in (
        "stale_evidence_pressure",
        "source_class_coverage_ratio",
        "contradiction_lag_pressure",
        "recheck_urgency_score",
        "latency_impact_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_impact_status("impact_status", payload["impact_status"])
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    _normalize_sha256(DERIVED_VALIDATION_DIGEST_FIELD, payload[DERIVED_VALIDATION_DIGEST_FIELD])
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_source_latency_impact_report_row",
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
    values: Iterable[ResearchSourceLatencyImpactObservation],
) -> tuple[ResearchSourceLatencyImpactObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in observations:
        _require_exact_type("observation", observation, ResearchSourceLatencyImpactObservation)
        _require_hard_flags("observation", observation)
        _reject_unsafe_public_payload("observation", observation)
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.decision_label,
                observation.source_class_label,
                observation.retrieval_delay_seconds,
            ),
        ),
    )


def _normalize_rows(value: object) -> tuple[ResearchSourceLatencyImpactRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchSourceLatencyImpactRow] = []
    for row in value:
        _require_exact_type("row", row, ResearchSourceLatencyImpactRow)
        _require_hard_flags("row", row)
        _validate_row_derived_validation_digest(row)
        rows.append(row)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceLatencyImpactRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        -row.latency_impact_score,
        -row.retrieval_delay_seconds,
        row.decision_label,
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


def _require_impact_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in IMPACT_STATUSES:
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
    if DOMAIN_LIKE_RE.search(lowered) or RAW_PUBLIC_ID_RE.search(lowered):
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
