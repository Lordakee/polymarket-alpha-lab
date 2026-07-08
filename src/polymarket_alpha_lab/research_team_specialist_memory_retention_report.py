"""Pure report-only specialist memory retention reducer."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-retention-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SPECIALIST_MEMORY_RETENTION_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
COMPONENT_COUNT = Decimal("4.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_OBSERVATIONS_REASON = "specialist_memory_retention_no_observations"
CLEAR_REASON = "specialist_memory_retention_clear"
MEMORY_FRESHNESS_BLOCK_REASON = "memory_freshness_block"
MEMORY_FRESHNESS_WATCH_REASON = "memory_freshness_watch"
CALIBRATION_UPTAKE_BLOCK_REASON = "calibration_uptake_block"
CALIBRATION_UPTAKE_WATCH_REASON = "calibration_uptake_watch"
CONFLICT_CARRY_FORWARD_BLOCK_REASON = "conflict_carry_forward_block"
CONFLICT_CARRY_FORWARD_WATCH_REASON = "conflict_carry_forward_watch"
RETRIEVAL_COVERAGE_BLOCK_REASON = "retrieval_coverage_block"
RETRIEVAL_COVERAGE_WATCH_REASON = "retrieval_coverage_watch"

ROW_REASON_CODE_SEQUENCE = (
    MEMORY_FRESHNESS_BLOCK_REASON,
    MEMORY_FRESHNESS_WATCH_REASON,
    CALIBRATION_UPTAKE_BLOCK_REASON,
    CALIBRATION_UPTAKE_WATCH_REASON,
    CONFLICT_CARRY_FORWARD_BLOCK_REASON,
    CONFLICT_CARRY_FORWARD_WATCH_REASON,
    RETRIEVAL_COVERAGE_BLOCK_REASON,
    RETRIEVAL_COVERAGE_WATCH_REASON,
    CLEAR_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_OBSERVATIONS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "specialist_memory_retention_report_clear"
REPORT_BLOCK_PRESENT_REASON = "specialist_memory_retention_block_present"
REPORT_WATCH_PRESENT_REASON = "specialist_memory_retention_watch_present"
REPORT_MEMORY_FRESHNESS_GAP_REASON = "memory_freshness_gap_present"
REPORT_CALIBRATION_UPTAKE_GAP_REASON = "calibration_uptake_gap_present"
REPORT_CONFLICT_CARRY_FORWARD_REASON = "conflict_carry_forward_present"
REPORT_RETRIEVAL_COVERAGE_GAP_REASON = "retrieval_coverage_gap_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_MEMORY_FRESHNESS_GAP_REASON,
    REPORT_CALIBRATION_UPTAKE_GAP_REASON,
    REPORT_CONFLICT_CARRY_FORWARD_REASON,
    REPORT_RETRIEVAL_COVERAGE_GAP_REASON,
    REPORT_CLEAR_REASON,
)

NEXT_REVIEW_STEPS = {
    STATUS_PASS: "reuse_specialist_memory_for_research",
    STATUS_WATCH: "review_specialist_memory_retention_before_reuse",
    STATUS_BLOCK: "block_specialist_memory_reuse_until_review",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "did", "ate"),
    _join_parts("mar", "ket"),
    _join_parts("s", "lug"),
    _join_parts("quest", "ion"),
    _join_parts("u", "rl"),
    _join_parts("sou", "rce", "_", "text"),
    _join_parts("sou", "rce", "_", "id"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("li", "ve"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    _join_parts("priv", "ate"),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_REPORT_CONFIG_VERSION",
    "SPECIALIST_MEMORY_RETENTION_STATUSES",
    "ResearchTeamSpecialistMemoryRetentionConfig",
    "ResearchTeamSpecialistMemoryRetentionDomainCoverage",
    "ResearchTeamSpecialistMemoryRetentionObservation",
    "ResearchTeamSpecialistMemoryRetentionReasonCodeCount",
    "ResearchTeamSpecialistMemoryRetentionReport",
    "ResearchTeamSpecialistMemoryRetentionRow",
    "build_research_team_specialist_memory_retention_report",
    "research_team_specialist_memory_retention_report_digest",
    "research_team_specialist_memory_retention_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_REPORT_CONFIG_VERSION
    )
    min_pass_memory_freshness_ratio: Decimal = Decimal("0.750000")
    min_watch_memory_freshness_ratio: Decimal = Decimal("0.500000")
    min_pass_calibration_uptake_ratio: Decimal = Decimal("0.700000")
    min_watch_calibration_uptake_ratio: Decimal = Decimal("0.500000")
    max_pass_conflict_carry_forward_ratio: Decimal = Decimal("0.100000")
    max_watch_conflict_carry_forward_ratio: Decimal = Decimal("0.250000")
    min_pass_retrieval_coverage_ratio: Decimal = Decimal("0.800000")
    min_watch_retrieval_coverage_ratio: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionConfig:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryRetentionConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_RETENTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in (
            "min_pass_memory_freshness_ratio",
            "min_watch_memory_freshness_ratio",
            "min_pass_calibration_uptake_ratio",
            "min_watch_calibration_uptake_ratio",
            "max_pass_conflict_carry_forward_ratio",
            "max_watch_conflict_carry_forward_ratio",
            "min_pass_retrieval_coverage_ratio",
            "min_watch_retrieval_coverage_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if self.min_watch_memory_freshness_ratio > self.min_pass_memory_freshness_ratio:
            raise ValueError("min_watch_memory_freshness_ratio must not exceed pass")
        if self.min_watch_calibration_uptake_ratio > self.min_pass_calibration_uptake_ratio:
            raise ValueError("min_watch_calibration_uptake_ratio must not exceed pass")
        if (
            self.max_pass_conflict_carry_forward_ratio
            > self.max_watch_conflict_carry_forward_ratio
        ):
            raise ValueError(
                "max_pass_conflict_carry_forward_ratio must not exceed watch",
            )
        if self.min_watch_retrieval_coverage_ratio > self.min_pass_retrieval_coverage_ratio:
            raise ValueError("min_watch_retrieval_coverage_ratio must not exceed pass")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionObservation:
    domain_label: str
    specialist_label: str
    observed_at: datetime
    long_term_memory_count: Decimal
    fresh_long_term_memory_count: Decimal
    calibration_event_count: Decimal
    calibration_uptake_count: Decimal
    unresolved_conflict_count: Decimal
    carried_forward_conflict_count: Decimal
    retrieval_attempt_count: Decimal
    successful_retrieval_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionObservation:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryRetentionObservation,
            "observation",
        )
        for name in ("domain_label", "specialist_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "long_term_memory_count",
            "calibration_event_count",
            "retrieval_attempt_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "fresh_long_term_memory_count",
            "calibration_uptake_count",
            "unresolved_conflict_count",
            "carried_forward_conflict_count",
            "successful_retrieval_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _validate_observation_counts(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionRow:
    domain_label: str
    specialist_label: str
    observed_at: datetime
    snapshot_age_seconds: Decimal
    long_term_memory_count: Decimal
    fresh_long_term_memory_count: Decimal
    calibration_event_count: Decimal
    calibration_uptake_count: Decimal
    unresolved_conflict_count: Decimal
    carried_forward_conflict_count: Decimal
    retrieval_attempt_count: Decimal
    successful_retrieval_count: Decimal
    memory_freshness_ratio: Decimal
    calibration_uptake_ratio: Decimal
    conflict_carry_forward_ratio: Decimal
    retrieval_coverage_ratio: Decimal
    retention_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionRow:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryRetentionRow, "row")
        for name in ("domain_label", "specialist_label"):
            object.__setattr__(self, name, _require_public_label(name, getattr(self, name)))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "snapshot_age_seconds",
            _require_nonnegative_decimal("snapshot_age_seconds", self.snapshot_age_seconds),
        )
        for name in (
            "long_term_memory_count",
            "calibration_event_count",
            "retrieval_attempt_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "fresh_long_term_memory_count",
            "calibration_uptake_count",
            "unresolved_conflict_count",
            "carried_forward_conflict_count",
            "successful_retrieval_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "memory_freshness_ratio",
            "calibration_uptake_ratio",
            "conflict_carry_forward_ratio",
            "retrieval_coverage_ratio",
            "retention_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionDomainCoverage:
    domain_label: str
    specialist_count: Decimal
    long_term_memory_count: Decimal
    fresh_long_term_memory_count: Decimal
    retrieval_attempt_count: Decimal
    successful_retrieval_count: Decimal
    memory_freshness_ratio: Decimal
    retrieval_coverage_ratio: Decimal
    worst_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionDomainCoverage:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionDomainCoverage does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryRetentionDomainCoverage,
            "domain coverage",
        )
        object.__setattr__(
            self,
            "domain_label",
            _require_public_label("domain_label", self.domain_label),
        )
        for name in (
            "specialist_count",
            "long_term_memory_count",
            "retrieval_attempt_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in ("fresh_long_term_memory_count", "successful_retrieval_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in ("memory_freshness_ratio", "retrieval_coverage_ratio"):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "worst_status",
            _require_status("worst_status", self.worst_status),
        )
        _validate_domain_coverage(self)
        _require_hard_flags("domain coverage", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistMemoryRetentionReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryRetentionReport:
    generated_at: datetime
    config_version: str
    status: str
    next_review_step: str
    observation_count: Decimal
    domain_count: Decimal
    specialist_count: Decimal
    long_term_memory_count: Decimal
    fresh_long_term_memory_count: Decimal
    calibration_event_count: Decimal
    calibration_uptake_count: Decimal
    unresolved_conflict_count: Decimal
    carried_forward_conflict_count: Decimal
    retrieval_attempt_count: Decimal
    successful_retrieval_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    memory_freshness_ratio: Decimal
    calibration_uptake_ratio: Decimal
    conflict_carry_forward_ratio: Decimal
    retrieval_coverage_ratio: Decimal
    retention_score: Decimal
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...]
    domain_coverage: tuple[ResearchTeamSpecialistMemoryRetentionDomainCoverage, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistMemoryRetentionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistMemoryRetentionReport:
            raise TypeError(
                "ResearchTeamSpecialistMemoryRetentionReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistMemoryRetentionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "next_review_step",
            _require_public_label("next_review_step", self.next_review_step),
        )
        for name in (
            "observation_count",
            "domain_count",
            "specialist_count",
            "long_term_memory_count",
            "fresh_long_term_memory_count",
            "calibration_event_count",
            "calibration_uptake_count",
            "unresolved_conflict_count",
            "carried_forward_conflict_count",
            "retrieval_attempt_count",
            "successful_retrieval_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "memory_freshness_ratio",
            "calibration_uptake_ratio",
            "conflict_carry_forward_ratio",
            "retrieval_coverage_ratio",
            "retention_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "domain_coverage",
            _normalize_domain_coverage(self.domain_coverage),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_specialist_memory_retention_report_payload(self)


def build_research_team_specialist_memory_retention_report(
    observations: Iterable[ResearchTeamSpecialistMemoryRetentionObservation],
    *,
    config: ResearchTeamSpecialistMemoryRetentionConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryRetentionReport:
    cfg = config or ResearchTeamSpecialistMemoryRetentionConfig()
    if type(cfg) is not ResearchTeamSpecialistMemoryRetentionConfig:
        raise ValueError(
            "config must be exactly ResearchTeamSpecialistMemoryRetentionConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamSpecialistMemoryRetentionReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_report_status(rows),
        next_review_step=NEXT_REVIEW_STEPS[_report_status(rows)],
        observation_count=_count_decimal(len(normalized_observations)),
        domain_count=_count_decimal(len({row.domain_label for row in rows})),
        specialist_count=_count_decimal(
            len({(row.domain_label, row.specialist_label) for row in rows}),
        ),
        long_term_memory_count=_sum_decimal(row.long_term_memory_count for row in rows),
        fresh_long_term_memory_count=_sum_decimal(
            row.fresh_long_term_memory_count for row in rows
        ),
        calibration_event_count=_sum_decimal(row.calibration_event_count for row in rows),
        calibration_uptake_count=_sum_decimal(row.calibration_uptake_count for row in rows),
        unresolved_conflict_count=_sum_decimal(
            (row.unresolved_conflict_count for row in rows),
        ),
        carried_forward_conflict_count=_sum_decimal(
            (row.carried_forward_conflict_count for row in rows),
        ),
        retrieval_attempt_count=_sum_decimal(row.retrieval_attempt_count for row in rows),
        successful_retrieval_count=_sum_decimal(
            row.successful_retrieval_count for row in rows
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        memory_freshness_ratio=_aggregate_memory_freshness_ratio(rows),
        calibration_uptake_ratio=_aggregate_calibration_uptake_ratio(rows),
        conflict_carry_forward_ratio=_aggregate_conflict_carry_forward_ratio(rows),
        retrieval_coverage_ratio=_aggregate_retrieval_coverage_ratio(rows),
        retention_score=_aggregate_retention_score(rows),
        rows=rows,
        domain_coverage=_domain_coverage(rows),
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows, len(normalized_observations)),
    )


def research_team_specialist_memory_retention_report_payload(
    value: object,
) -> dict[str, Any]:
    _require_supported_payload_input(value)
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    _validate_payload_digest(payload)
    return payload


def research_team_specialist_memory_retention_report_digest(
    report: ResearchTeamSpecialistMemoryRetentionReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistMemoryRetentionReport:
        raise ValueError("report must be exactly ResearchTeamSpecialistMemoryRetentionReport")
    return report.derived_validation_digest


def _row_from_observation(
    observation: ResearchTeamSpecialistMemoryRetentionObservation,
    *,
    config: ResearchTeamSpecialistMemoryRetentionConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryRetentionRow:
    memory_freshness_ratio = _safe_divide(
        observation.fresh_long_term_memory_count,
        observation.long_term_memory_count,
    )
    calibration_uptake_ratio = _safe_divide(
        observation.calibration_uptake_count,
        observation.calibration_event_count,
    )
    conflict_carry_forward_ratio = _safe_divide(
        observation.carried_forward_conflict_count,
        observation.unresolved_conflict_count,
    )
    retrieval_coverage_ratio = _safe_divide(
        observation.successful_retrieval_count,
        observation.retrieval_attempt_count,
    )
    reason_codes = _row_reason_codes(
        memory_freshness_ratio=memory_freshness_ratio,
        calibration_uptake_ratio=calibration_uptake_ratio,
        conflict_carry_forward_ratio=conflict_carry_forward_ratio,
        retrieval_coverage_ratio=retrieval_coverage_ratio,
        config=config,
    )
    return ResearchTeamSpecialistMemoryRetentionRow(
        domain_label=observation.domain_label,
        specialist_label=observation.specialist_label,
        observed_at=observation.observed_at,
        snapshot_age_seconds=_age_seconds(generated_at, observation.observed_at),
        long_term_memory_count=observation.long_term_memory_count,
        fresh_long_term_memory_count=observation.fresh_long_term_memory_count,
        calibration_event_count=observation.calibration_event_count,
        calibration_uptake_count=observation.calibration_uptake_count,
        unresolved_conflict_count=observation.unresolved_conflict_count,
        carried_forward_conflict_count=observation.carried_forward_conflict_count,
        retrieval_attempt_count=observation.retrieval_attempt_count,
        successful_retrieval_count=observation.successful_retrieval_count,
        memory_freshness_ratio=memory_freshness_ratio,
        calibration_uptake_ratio=calibration_uptake_ratio,
        conflict_carry_forward_ratio=conflict_carry_forward_ratio,
        retrieval_coverage_ratio=retrieval_coverage_ratio,
        retention_score=_retention_score(
            memory_freshness_ratio=memory_freshness_ratio,
            calibration_uptake_ratio=calibration_uptake_ratio,
            conflict_carry_forward_ratio=conflict_carry_forward_ratio,
            retrieval_coverage_ratio=retrieval_coverage_ratio,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    memory_freshness_ratio: Decimal,
    calibration_uptake_ratio: Decimal,
    conflict_carry_forward_ratio: Decimal,
    retrieval_coverage_ratio: Decimal,
    config: ResearchTeamSpecialistMemoryRetentionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_freshness_ratio < config.min_watch_memory_freshness_ratio:
        reason_codes.append(MEMORY_FRESHNESS_BLOCK_REASON)
    elif memory_freshness_ratio < config.min_pass_memory_freshness_ratio:
        reason_codes.append(MEMORY_FRESHNESS_WATCH_REASON)
    if calibration_uptake_ratio < config.min_watch_calibration_uptake_ratio:
        reason_codes.append(CALIBRATION_UPTAKE_BLOCK_REASON)
    elif calibration_uptake_ratio < config.min_pass_calibration_uptake_ratio:
        reason_codes.append(CALIBRATION_UPTAKE_WATCH_REASON)
    if conflict_carry_forward_ratio > config.max_watch_conflict_carry_forward_ratio:
        reason_codes.append(CONFLICT_CARRY_FORWARD_BLOCK_REASON)
    elif conflict_carry_forward_ratio > config.max_pass_conflict_carry_forward_ratio:
        reason_codes.append(CONFLICT_CARRY_FORWARD_WATCH_REASON)
    if retrieval_coverage_ratio < config.min_watch_retrieval_coverage_ratio:
        reason_codes.append(RETRIEVAL_COVERAGE_BLOCK_REASON)
    elif retrieval_coverage_ratio < config.min_pass_retrieval_coverage_ratio:
        reason_codes.append(RETRIEVAL_COVERAGE_WATCH_REASON)
    return tuple(reason_codes) or (CLEAR_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
    observation_count: int,
) -> tuple[str, ...]:
    if observation_count == 0:
        return (NO_OBSERVATIONS_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if _row_reason_count(
        rows,
        (MEMORY_FRESHNESS_BLOCK_REASON, MEMORY_FRESHNESS_WATCH_REASON),
    ):
        reason_codes.append(REPORT_MEMORY_FRESHNESS_GAP_REASON)
    if _row_reason_count(
        rows,
        (CALIBRATION_UPTAKE_BLOCK_REASON, CALIBRATION_UPTAKE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_CALIBRATION_UPTAKE_GAP_REASON)
    if _row_reason_count(
        rows,
        (CONFLICT_CARRY_FORWARD_BLOCK_REASON, CONFLICT_CARRY_FORWARD_WATCH_REASON),
    ):
        reason_codes.append(REPORT_CONFLICT_CARRY_FORWARD_REASON)
    if _row_reason_count(
        rows,
        (RETRIEVAL_COVERAGE_BLOCK_REASON, RETRIEVAL_COVERAGE_WATCH_REASON),
    ):
        reason_codes.append(REPORT_RETRIEVAL_COVERAGE_GAP_REASON)
    return tuple(reason_codes) or (REPORT_CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistMemoryRetentionReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_total = _count_decimal(len(rows))
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    return tuple(
        ResearchTeamSpecialistMemoryRetentionReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counter[reason_code]),
            row_ratio=_safe_divide(_count_decimal(counter[reason_code]), row_total),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if counter[reason_code] > 0
    )


def _domain_coverage(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionDomainCoverage, ...]:
    domain_labels = sorted({row.domain_label for row in rows})
    return tuple(_domain_coverage_for_label(domain_label, rows) for domain_label in domain_labels)


def _domain_coverage_for_label(
    domain_label: str,
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> ResearchTeamSpecialistMemoryRetentionDomainCoverage:
    domain_rows = tuple(row for row in rows if row.domain_label == domain_label)
    long_term_memory_count = _sum_decimal(row.long_term_memory_count for row in domain_rows)
    fresh_long_term_memory_count = _sum_decimal(
        row.fresh_long_term_memory_count for row in domain_rows
    )
    retrieval_attempt_count = _sum_decimal(row.retrieval_attempt_count for row in domain_rows)
    successful_retrieval_count = _sum_decimal(
        row.successful_retrieval_count for row in domain_rows
    )
    return ResearchTeamSpecialistMemoryRetentionDomainCoverage(
        domain_label=domain_label,
        specialist_count=_count_decimal(len({row.specialist_label for row in domain_rows})),
        long_term_memory_count=long_term_memory_count,
        fresh_long_term_memory_count=fresh_long_term_memory_count,
        retrieval_attempt_count=retrieval_attempt_count,
        successful_retrieval_count=successful_retrieval_count,
        memory_freshness_ratio=_safe_divide(
            fresh_long_term_memory_count,
            long_term_memory_count,
        ),
        retrieval_coverage_ratio=_safe_divide(
            successful_retrieval_count,
            retrieval_attempt_count,
        ),
        worst_status=_report_status(domain_rows),
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_count(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchTeamSpecialistMemoryRetentionRow) -> tuple[int, str, str]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.domain_label,
        row.specialist_label,
    )


def _normalize_observations(
    observations: Iterable[ResearchTeamSpecialistMemoryRetentionObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamSpecialistMemoryRetentionObservation, ...]:
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchTeamSpecialistMemoryRetentionObservation:
            raise ValueError(
                "observations must contain exactly "
                "ResearchTeamSpecialistMemoryRetentionObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    keys = tuple((item.domain_label, item.specialist_label) for item in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("domain_label and specialist_label pairs must be unique")
    return tuple(sorted(normalized, key=lambda item: (item.domain_label, item.specialist_label)))


def _normalize_rows(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryRetentionRow:
            raise ValueError(
                "rows must contain exactly ResearchTeamSpecialistMemoryRetentionRow",
            )
        _require_hard_flags("row", row)
    keys = tuple((row.domain_label, row.specialist_label) for row in rows)
    if len(set(keys)) != len(keys):
        raise ValueError("rows domain_label and specialist_label pairs must be unique")
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_domain_coverage(
    values: tuple[ResearchTeamSpecialistMemoryRetentionDomainCoverage, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionDomainCoverage, ...]:
    if type(values) is not tuple:
        raise ValueError("domain_coverage must be a tuple")
    for value in values:
        if type(value) is not ResearchTeamSpecialistMemoryRetentionDomainCoverage:
            raise ValueError(
                "domain_coverage must contain exactly "
                "ResearchTeamSpecialistMemoryRetentionDomainCoverage",
            )
        _require_hard_flags("domain coverage", value)
    labels = tuple(value.domain_label for value in values)
    if len(set(labels)) != len(labels):
        raise ValueError("domain_coverage domain_label values must be unique")
    return tuple(sorted(values, key=lambda value: value.domain_label))


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamSpecialistMemoryRetentionReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistMemoryRetentionReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamSpecialistMemoryRetentionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchTeamSpecialistMemoryRetentionReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    reason_codes = tuple(count.reason_code for count in counts)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return tuple(sorted(counts, key=lambda count: COUNT_REASON_CODE_SEQUENCE.index(count.reason_code)))


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must be unique")
    for value in values:
        _require_member(name, value, allowed)
    return tuple(sorted(values, key=allowed.index))


def _validate_observation_counts(
    observation: ResearchTeamSpecialistMemoryRetentionObservation,
) -> None:
    if observation.fresh_long_term_memory_count > observation.long_term_memory_count:
        raise ValueError(
            "fresh_long_term_memory_count must not exceed long_term_memory_count",
        )
    if observation.calibration_uptake_count > observation.calibration_event_count:
        raise ValueError("calibration_uptake_count must not exceed calibration_event_count")
    if observation.carried_forward_conflict_count > observation.unresolved_conflict_count:
        raise ValueError(
            "carried_forward_conflict_count must not exceed unresolved_conflict_count",
        )
    if observation.successful_retrieval_count > observation.retrieval_attempt_count:
        raise ValueError(
            "successful_retrieval_count must not exceed retrieval_attempt_count",
        )


def _validate_row(row: ResearchTeamSpecialistMemoryRetentionRow) -> None:
    if row.fresh_long_term_memory_count > row.long_term_memory_count:
        raise ValueError(
            "fresh_long_term_memory_count must not exceed long_term_memory_count",
        )
    if row.calibration_uptake_count > row.calibration_event_count:
        raise ValueError("calibration_uptake_count must not exceed calibration_event_count")
    if row.carried_forward_conflict_count > row.unresolved_conflict_count:
        raise ValueError(
            "carried_forward_conflict_count must not exceed unresolved_conflict_count",
        )
    if row.successful_retrieval_count > row.retrieval_attempt_count:
        raise ValueError(
            "successful_retrieval_count must not exceed retrieval_attempt_count",
        )
    expected_ratios = {
        "memory_freshness_ratio": _safe_divide(
            row.fresh_long_term_memory_count,
            row.long_term_memory_count,
        ),
        "calibration_uptake_ratio": _safe_divide(
            row.calibration_uptake_count,
            row.calibration_event_count,
        ),
        "conflict_carry_forward_ratio": _safe_divide(
            row.carried_forward_conflict_count,
            row.unresolved_conflict_count,
        ),
        "retrieval_coverage_ratio": _safe_divide(
            row.successful_retrieval_count,
            row.retrieval_attempt_count,
        ),
    }
    for name, expected in expected_ratios.items():
        if getattr(row, name) != expected:
            raise ValueError(f"{name} must match row counts")
    expected_score = _retention_score(
        memory_freshness_ratio=row.memory_freshness_ratio,
        calibration_uptake_ratio=row.calibration_uptake_ratio,
        conflict_carry_forward_ratio=row.conflict_carry_forward_ratio,
        retrieval_coverage_ratio=row.retrieval_coverage_ratio,
    )
    if row.retention_score != expected_score:
        raise ValueError("retention_score must match row ratios")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_domain_coverage(
    value: ResearchTeamSpecialistMemoryRetentionDomainCoverage,
) -> None:
    if value.fresh_long_term_memory_count > value.long_term_memory_count:
        raise ValueError(
            "fresh_long_term_memory_count must not exceed long_term_memory_count",
        )
    if value.successful_retrieval_count > value.retrieval_attempt_count:
        raise ValueError(
            "successful_retrieval_count must not exceed retrieval_attempt_count",
        )
    if value.memory_freshness_ratio != _safe_divide(
        value.fresh_long_term_memory_count,
        value.long_term_memory_count,
    ):
        raise ValueError("memory_freshness_ratio must match domain counts")
    if value.retrieval_coverage_ratio != _safe_divide(
        value.successful_retrieval_count,
        value.retrieval_attempt_count,
    ):
        raise ValueError("retrieval_coverage_ratio must match domain counts")


def _validate_report(report: ResearchTeamSpecialistMemoryRetentionReport) -> None:
    expected_counts = {
        "observation_count": _count_decimal(len(report.rows)),
        "domain_count": _count_decimal(len({row.domain_label for row in report.rows})),
        "specialist_count": _count_decimal(
            len({(row.domain_label, row.specialist_label) for row in report.rows}),
        ),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
    }
    for name, expected in expected_counts.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    expected_sums = {
        "long_term_memory_count": _sum_decimal(
            row.long_term_memory_count for row in report.rows
        ),
        "fresh_long_term_memory_count": _sum_decimal(
            row.fresh_long_term_memory_count for row in report.rows
        ),
        "calibration_event_count": _sum_decimal(
            row.calibration_event_count for row in report.rows
        ),
        "calibration_uptake_count": _sum_decimal(
            row.calibration_uptake_count for row in report.rows
        ),
        "unresolved_conflict_count": _sum_decimal(
            row.unresolved_conflict_count for row in report.rows
        ),
        "carried_forward_conflict_count": _sum_decimal(
            row.carried_forward_conflict_count for row in report.rows
        ),
        "retrieval_attempt_count": _sum_decimal(
            row.retrieval_attempt_count for row in report.rows
        ),
        "successful_retrieval_count": _sum_decimal(
            row.successful_retrieval_count for row in report.rows
        ),
    }
    for name, expected in expected_sums.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    expected_ratios = {
        "memory_freshness_ratio": _aggregate_memory_freshness_ratio(report.rows),
        "calibration_uptake_ratio": _aggregate_calibration_uptake_ratio(report.rows),
        "conflict_carry_forward_ratio": _aggregate_conflict_carry_forward_ratio(
            report.rows,
        ),
        "retrieval_coverage_ratio": _aggregate_retrieval_coverage_ratio(report.rows),
        "retention_score": _aggregate_retention_score(report.rows),
    }
    for name, expected in expected_ratios.items():
        if getattr(report, name) != expected:
            raise ValueError(f"{name} must match rows")
    if report.domain_coverage != _domain_coverage(report.rows):
        raise ValueError("domain_coverage must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.observation_count)):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.status]:
        raise ValueError("next_review_step must match status")


def _aggregate_memory_freshness_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.fresh_long_term_memory_count for row in rows),
        _sum_decimal(row.long_term_memory_count for row in rows),
    )


def _aggregate_calibration_uptake_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.calibration_uptake_count for row in rows),
        _sum_decimal(row.calibration_event_count for row in rows),
    )


def _aggregate_conflict_carry_forward_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.carried_forward_conflict_count for row in rows),
        _sum_decimal(row.unresolved_conflict_count for row in rows),
    )


def _aggregate_retrieval_coverage_ratio(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> Decimal:
    return _safe_divide(
        _sum_decimal(row.successful_retrieval_count for row in rows),
        _sum_decimal(row.retrieval_attempt_count for row in rows),
    )


def _aggregate_retention_score(
    rows: tuple[ResearchTeamSpecialistMemoryRetentionRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _retention_score(
        memory_freshness_ratio=_aggregate_memory_freshness_ratio(rows),
        calibration_uptake_ratio=_aggregate_calibration_uptake_ratio(rows),
        conflict_carry_forward_ratio=_aggregate_conflict_carry_forward_ratio(rows),
        retrieval_coverage_ratio=_aggregate_retrieval_coverage_ratio(rows),
    )


def _retention_score(
    *,
    memory_freshness_ratio: Decimal,
    calibration_uptake_ratio: Decimal,
    conflict_carry_forward_ratio: Decimal,
    retrieval_coverage_ratio: Decimal,
) -> Decimal:
    return _quantize_decimal(
        (
            memory_freshness_ratio
            + calibration_uptake_ratio
            + (ONE - conflict_carry_forward_ratio)
            + retrieval_coverage_ratio
        )
        / COMPONENT_COUNT,
    )


def _require_supported_payload_input(value: object) -> None:
    if type(value) is dict:
        return
    if type(value) in (
        ResearchTeamSpecialistMemoryRetentionConfig,
        ResearchTeamSpecialistMemoryRetentionObservation,
        ResearchTeamSpecialistMemoryRetentionRow,
        ResearchTeamSpecialistMemoryRetentionDomainCoverage,
        ResearchTeamSpecialistMemoryRetentionReasonCodeCount,
        ResearchTeamSpecialistMemoryRetentionReport,
    ):
        _require_hard_flags("payload input", value)
        return
    raise ValueError(
        "value must be a research team specialist memory retention dataclass or dict",
    )


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) is dict:
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_payload_flags(value: object, field_path: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in value:
                raise ValueError(f"{field_path}.{flag} must be present")
            if value[flag] is not True:
                raise ValueError(f"{field_path}.{flag} must be True")
        for key, item in value.items():
            if type(item) is dict:
                _validate_payload_flags(item, f"{field_path}.{key}")
            elif type(item) is list:
                for index, child in enumerate(item):
                    if type(child) is dict:
                        _validate_payload_flags(child, f"{field_path}.{key}.{index}")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        return
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    if digest != _digest_payload(payload):
        raise ValueError("derived_validation_digest must match payload")


def _derived_validation_digest(report: ResearchTeamSpecialistMemoryRetentionReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload field or value")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{name} must not have surrounding whitespace")
    if len(value) > 96:
        raise ValueError(f"{name} must be short")
    allowed_characters = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-",
    )
    if any(character not in allowed_characters for character in value):
        raise ValueError(f"{name} must be a public-safe aggregate label")
    _reject_unsafe_public_text(value)
    return value


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{name} exceeds required decimal precision")
    return _quantize_decimal(value)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_status(name: str, value: str) -> str:
    return _require_member(name, value, SPECIALIST_MEMORY_RETENTION_STATUSES)


def _require_member(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")
    return value


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    int(value, 16)
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(value, name) is not True:
            raise ValueError(f"{label} {name} must be True")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.microsecond != 0:
        raise ValueError(f"{name} must be a whole second")
    return value.astimezone(UTC)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    micros = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _require_nonnegative_decimal(
        "snapshot_age_seconds",
        _quantize_decimal(micros / MICROSECONDS_PER_SECOND),
    )


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(DECIMAL_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
        return total.quantize(DECIMAL_QUANTUM)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)
