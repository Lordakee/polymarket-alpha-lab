"""Pure report-only source-claim resolution recheck priority report.

This module ranks caller-supplied resolution recheck observations for analyst
review. It performs no network access, persistence, wallet, auth, execution,
order, trade, sizing, or recommendation work.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_RECHECK_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-source-claim-resolution-recheck-priority-report-v0"
)

RESOLUTION_RECHECK_PRIORITY_STATUSES = ("pass", "watch", "block")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SEVEN = Decimal("7.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

UNSAFE_KEY_FRAGMENTS = (
    "raw_" + "candidate",
    "candidate_" + "id",
    "condition_" + "id",
    "market_" + "id",
    "market_" + "sl" + "ug",
    "market_" + "ques" + "tion",
    "sl" + "ug",
    "ques" + "tion",
    "source_" + "url",
    "source_" + "text",
    "raw_" + "text",
    "raw",
    "d" + "sn",
    "tab" + "le",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "private_",
)
UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "raw_" + "candidate",
    "candidate_" + "id",
    "condition_" + "id",
    "market_" + "id",
    "market_" + "sl" + "ug",
    "market_" + "ques" + "tion",
    "sl" + "ug",
    "ques" + "tion",
    "source_" + "url",
    "source_" + "text",
    "raw_" + "text",
    "d" + "sn",
    "tab" + "le",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "secret",
    "credential",
    "database",
    "network",
    "persist",
    "signing",
    "buy",
    "sell",
)

PUBLIC_ROW_FIELDS_WITHOUT_DIGEST = (
    "claim_bucket",
    "authority_bucket",
    "observed_age_seconds",
    "authority_age_seconds",
    "authority_staleness_score",
    "authority_match_score",
    "authority_mismatch_score",
    "resolution_evidence_strength",
    "evidence_gap_score",
    "source_conflict_score",
    "revision_pressure_score",
    "unresolved_dependency_count",
    "required_dependency_count",
    "dependency_gap_score",
    "deadline_pressure_score",
    "resolution_recheck_priority_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_FIELDS = (
    *PUBLIC_ROW_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "generated_at",
    "status",
    "observation_count",
    "pass_count",
    "watch_count",
    "block_count",
    "authority_stale_count",
    "authority_mismatch_count",
    "evidence_gap_count",
    "conflict_count",
    "revision_pressure_count",
    "dependency_gap_count",
    "deadline_pressure_count",
    "average_resolution_recheck_priority_score",
    "max_resolution_recheck_priority_score",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS = (
    *PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_RECHECK_PRIORITY_REPORT_CONFIG_VERSION",
    "RESOLUTION_RECHECK_PRIORITY_STATUSES",
    "ResearchSourceClaimResolutionRecheckPriorityConfig",
    "ResearchSourceClaimResolutionRecheckPriorityObservation",
    "ResearchSourceClaimResolutionRecheckPriorityReport",
    "ResearchSourceClaimResolutionRecheckPriorityRow",
    "build_research_source_claim_resolution_recheck_priority_report",
    "research_source_claim_resolution_recheck_priority_report_digest",
    "research_source_claim_resolution_recheck_priority_report_payload",
    "validate_research_source_claim_resolution_recheck_priority_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionRecheckPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_RECHECK_PRIORITY_REPORT_CONFIG_VERSION
    )
    fresh_authority_age_seconds: Decimal = Decimal("3600.000000")
    stale_authority_age_seconds: Decimal = Decimal("86400.000000")
    deadline_pressure_window_seconds: Decimal = Decimal("172800.000000")
    watch_priority_score: Decimal = Decimal("0.250000")
    block_priority_score: Decimal = Decimal("0.700000")
    watch_authority_staleness_score: Decimal = Decimal("0.250000")
    block_authority_staleness_score: Decimal = Decimal("1.000000")
    min_authority_match_score: Decimal = Decimal("0.700000")
    block_authority_match_score: Decimal = Decimal("0.300000")
    min_resolution_evidence_strength: Decimal = Decimal("0.700000")
    block_resolution_evidence_strength: Decimal = Decimal("0.300000")
    watch_source_conflict_score: Decimal = Decimal("0.300000")
    block_source_conflict_score: Decimal = Decimal("0.700000")
    watch_revision_pressure_score: Decimal = Decimal("0.500000")
    block_revision_pressure_score: Decimal = Decimal("0.800000")
    watch_dependency_gap_score: Decimal = Decimal("0.250000")
    block_dependency_gap_score: Decimal = Decimal("0.800000")
    watch_deadline_pressure_score: Decimal = Decimal("0.500000")
    block_deadline_pressure_score: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimResolutionRecheckPriorityConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceClaimResolutionRecheckPriorityConfig,
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_RECHECK_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_authority_age_seconds",
            "stale_authority_age_seconds",
            "deadline_pressure_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_priority_score",
            "block_priority_score",
            "watch_authority_staleness_score",
            "block_authority_staleness_score",
            "min_authority_match_score",
            "block_authority_match_score",
            "min_resolution_evidence_strength",
            "block_resolution_evidence_strength",
            "watch_source_conflict_score",
            "block_source_conflict_score",
            "watch_revision_pressure_score",
            "block_revision_pressure_score",
            "watch_dependency_gap_score",
            "block_dependency_gap_score",
            "watch_deadline_pressure_score",
            "block_deadline_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_authority_age_seconds <= self.fresh_authority_age_seconds:
            raise ValueError(
                "stale_authority_age_seconds must exceed fresh_authority_age_seconds",
            )
        if self.block_priority_score <= self.watch_priority_score:
            raise ValueError("block_priority_score must exceed watch_priority_score")
        if self.block_authority_staleness_score < self.watch_authority_staleness_score:
            raise ValueError(
                "block_authority_staleness_score must be at least "
                "watch_authority_staleness_score",
            )
        if self.block_authority_match_score > self.min_authority_match_score:
            raise ValueError(
                "block_authority_match_score must not exceed min_authority_match_score",
            )
        if (
            self.block_resolution_evidence_strength
            > self.min_resolution_evidence_strength
        ):
            raise ValueError(
                "block_resolution_evidence_strength must not exceed "
                "min_resolution_evidence_strength",
            )
        if self.block_source_conflict_score < self.watch_source_conflict_score:
            raise ValueError(
                "block_source_conflict_score must be at least "
                "watch_source_conflict_score",
            )
        if self.block_revision_pressure_score < self.watch_revision_pressure_score:
            raise ValueError(
                "block_revision_pressure_score must be at least "
                "watch_revision_pressure_score",
            )
        if self.block_dependency_gap_score < self.watch_dependency_gap_score:
            raise ValueError(
                "block_dependency_gap_score must be at least watch_dependency_gap_score",
            )
        if self.block_deadline_pressure_score < self.watch_deadline_pressure_score:
            raise ValueError(
                "block_deadline_pressure_score must be at least "
                "watch_deadline_pressure_score",
            )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionRecheckPriorityObservation:
    claim_bucket: str
    authority_bucket: str
    private_recheck_reference: str
    private_resolution_reference: str
    private_evidence_reference: str
    observed_at: datetime
    resolution_authority_checked_at: datetime
    authority_match_score: Decimal
    resolution_evidence_strength: Decimal
    source_conflict_score: Decimal
    revision_pressure_score: Decimal
    unresolved_dependency_count: Decimal
    required_dependency_count: Decimal
    resolution_due_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimResolutionRecheckPriorityObservation does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchSourceClaimResolutionRecheckPriorityObservation,
        )
        for field_name in ("claim_bucket", "authority_bucket"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "private_recheck_reference",
            "private_resolution_reference",
            "private_evidence_reference",
        ):
            _require_private_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_authority_checked_at",
            _as_utc(
                "resolution_authority_checked_at",
                self.resolution_authority_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "resolution_due_at",
            _optional_as_utc("resolution_due_at", self.resolution_due_at),
        )
        for field_name in (
            "authority_match_score",
            "resolution_evidence_strength",
            "source_conflict_score",
            "revision_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_dependency_count",
            _normalize_nonnegative_whole_decimal(
                "unresolved_dependency_count",
                self.unresolved_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "required_dependency_count",
            _normalize_positive_whole_decimal(
                "required_dependency_count",
                self.required_dependency_count,
            ),
        )
        if self.unresolved_dependency_count > self.required_dependency_count:
            raise ValueError(
                "unresolved_dependency_count must not exceed required_dependency_count",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionRecheckPriorityRow:
    claim_bucket: str
    authority_bucket: str
    observed_age_seconds: Decimal
    authority_age_seconds: Decimal
    authority_staleness_score: Decimal
    authority_match_score: Decimal
    authority_mismatch_score: Decimal
    resolution_evidence_strength: Decimal
    evidence_gap_score: Decimal
    source_conflict_score: Decimal
    revision_pressure_score: Decimal
    unresolved_dependency_count: Decimal
    required_dependency_count: Decimal
    dependency_gap_score: Decimal
    deadline_pressure_score: Decimal
    resolution_recheck_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimResolutionRecheckPriorityRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceClaimResolutionRecheckPriorityRow)
        for field_name in ("claim_bucket", "authority_bucket"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "observed_age_seconds",
            "authority_age_seconds",
            "unresolved_dependency_count",
            "required_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_dependency_count",
            _normalize_positive_whole_decimal(
                "required_dependency_count",
                self.required_dependency_count,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_dependency_count",
            _normalize_nonnegative_whole_decimal(
                "unresolved_dependency_count",
                self.unresolved_dependency_count,
            ),
        )
        if self.unresolved_dependency_count > self.required_dependency_count:
            raise ValueError(
                "unresolved_dependency_count must not exceed required_dependency_count",
            )
        for field_name in (
            "authority_staleness_score",
            "authority_match_score",
            "authority_mismatch_score",
            "resolution_evidence_strength",
            "evidence_gap_score",
            "source_conflict_score",
            "revision_pressure_score",
            "dependency_gap_score",
            "deadline_pressure_score",
            "resolution_recheck_priority_score",
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
            _normalize_public_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_digest_from_values(_row_values_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_consistency(self)
        _validate_row_digest(self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionRecheckPriorityReport:
    config_version: str
    generated_at: datetime
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    authority_stale_count: Decimal
    authority_mismatch_count: Decimal
    evidence_gap_count: Decimal
    conflict_count: Decimal
    revision_pressure_count: Decimal
    dependency_gap_count: Decimal
    deadline_pressure_count: Decimal
    average_resolution_recheck_priority_score: Decimal
    max_resolution_recheck_priority_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceClaimResolutionRecheckPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceClaimResolutionRecheckPriorityReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceClaimResolutionRecheckPriorityReport)
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_RECHECK_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "authority_stale_count",
            "authority_mismatch_count",
            "evidence_gap_count",
            "conflict_count",
            "revision_pressure_count",
            "dependency_gap_count",
            "deadline_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_resolution_recheck_priority_score",
            "max_resolution_recheck_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_digest_from_values(_report_values_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_consistency(self)
        _validate_report_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_source_claim_resolution_recheck_priority_report_payload(self)


def build_research_source_claim_resolution_recheck_priority_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimResolutionRecheckPriorityConfig | None = None,
) -> ResearchSourceClaimResolutionRecheckPriorityReport:
    if config is None:
        config = ResearchSourceClaimResolutionRecheckPriorityConfig()
    _require_exact_type("config", config, ResearchSourceClaimResolutionRecheckPriorityConfig)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
        if observation.resolution_authority_checked_at > generated_at_utc:
            raise ValueError(
                "resolution_authority_checked_at must not be after generated_at",
            )
    rows = _normalize_rows(
        tuple(
            _row_for_observation(observation, config, generated_at_utc)
            for observation in normalized_observations
        ),
    )
    values: dict[str, object] = {
        "config_version": config.config_version,
        "generated_at": generated_at_utc,
        "status": _report_status(rows),
        "observation_count": _count(len(rows)),
        "pass_count": _row_status_count(rows, "pass"),
        "watch_count": _row_status_count(rows, "watch"),
        "block_count": _row_status_count(rows, "block"),
        "authority_stale_count": _count(
            sum(
                1
                for row in rows
                if row.authority_staleness_score >= config.watch_authority_staleness_score
            ),
        ),
        "authority_mismatch_count": _count(
            sum(
                1
                for row in rows
                if row.authority_match_score <= config.min_authority_match_score
            ),
        ),
        "evidence_gap_count": _count(
            sum(
                1
                for row in rows
                if row.resolution_evidence_strength
                <= config.min_resolution_evidence_strength
            ),
        ),
        "conflict_count": _count(
            sum(
                1
                for row in rows
                if row.source_conflict_score >= config.watch_source_conflict_score
            ),
        ),
        "revision_pressure_count": _count(
            sum(
                1
                for row in rows
                if row.revision_pressure_score >= config.watch_revision_pressure_score
            ),
        ),
        "dependency_gap_count": _count(
            sum(
                1
                for row in rows
                if row.dependency_gap_score >= config.watch_dependency_gap_score
            ),
        ),
        "deadline_pressure_count": _count(
            sum(
                1
                for row in rows
                if row.deadline_pressure_score >= config.watch_deadline_pressure_score
            ),
        ),
        "average_resolution_recheck_priority_score": _average(
            tuple(row.resolution_recheck_priority_score for row in rows),
        ),
        "max_resolution_recheck_priority_score": _max_decimal(
            tuple(row.resolution_recheck_priority_score for row in rows),
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimResolutionRecheckPriorityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_resolution_recheck_priority_report_payload(
    report: ResearchSourceClaimResolutionRecheckPriorityReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceClaimResolutionRecheckPriorityReport:
        _require_hard_flags("report", report)
        _validate_report_digest(report)
        payload = _json_ready(_report_values(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        _validate_public_report_payload(payload)
        return dict(payload)
    raise ValueError(
        "report must be a ResearchSourceClaimResolutionRecheckPriorityReport",
    )


def research_source_claim_resolution_recheck_priority_report_digest(
    report: ResearchSourceClaimResolutionRecheckPriorityReport,
) -> str:
    if type(report) is not ResearchSourceClaimResolutionRecheckPriorityReport:
        raise ValueError(
            "report must be a ResearchSourceClaimResolutionRecheckPriorityReport",
        )
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    return report.derived_validation_digest


def validate_research_source_claim_resolution_recheck_priority_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _reject_unsafe_public_payload("payload", payload)
        _validate_public_report_payload(payload)
        return True
    except (TypeError, ValueError):
        return False


def _row_for_observation(
    observation: ResearchSourceClaimResolutionRecheckPriorityObservation,
    config: ResearchSourceClaimResolutionRecheckPriorityConfig,
    generated_at: datetime,
) -> ResearchSourceClaimResolutionRecheckPriorityRow:
    observed_age_seconds = _datetime_delta_seconds(generated_at, observation.observed_at)
    authority_age_seconds = _datetime_delta_seconds(
        generated_at,
        observation.resolution_authority_checked_at,
    )
    authority_staleness_score = _authority_staleness_score(
        authority_age_seconds,
        config,
    )
    authority_mismatch_score = _cap_probability(ONE - observation.authority_match_score)
    evidence_gap_score = _cap_probability(
        ONE - observation.resolution_evidence_strength,
    )
    dependency_gap_score = _ratio(
        observation.unresolved_dependency_count,
        observation.required_dependency_count,
    )
    deadline_pressure_score = _deadline_pressure_score(
        observation.resolution_due_at,
        config,
        generated_at,
    )
    priority_score = _resolution_recheck_priority_score(
        authority_staleness_score=authority_staleness_score,
        authority_mismatch_score=authority_mismatch_score,
        evidence_gap_score=evidence_gap_score,
        source_conflict_score=observation.source_conflict_score,
        revision_pressure_score=observation.revision_pressure_score,
        dependency_gap_score=dependency_gap_score,
        deadline_pressure_score=deadline_pressure_score,
    )
    status = _row_status(
        authority_staleness_score=authority_staleness_score,
        authority_match_score=observation.authority_match_score,
        resolution_evidence_strength=observation.resolution_evidence_strength,
        source_conflict_score=observation.source_conflict_score,
        revision_pressure_score=observation.revision_pressure_score,
        dependency_gap_score=dependency_gap_score,
        deadline_pressure_score=deadline_pressure_score,
        resolution_recheck_priority_score=priority_score,
        config=config,
    )
    return ResearchSourceClaimResolutionRecheckPriorityRow(
        claim_bucket=observation.claim_bucket,
        authority_bucket=observation.authority_bucket,
        observed_age_seconds=observed_age_seconds,
        authority_age_seconds=authority_age_seconds,
        authority_staleness_score=authority_staleness_score,
        authority_match_score=observation.authority_match_score,
        authority_mismatch_score=authority_mismatch_score,
        resolution_evidence_strength=observation.resolution_evidence_strength,
        evidence_gap_score=evidence_gap_score,
        source_conflict_score=observation.source_conflict_score,
        revision_pressure_score=observation.revision_pressure_score,
        unresolved_dependency_count=observation.unresolved_dependency_count,
        required_dependency_count=observation.required_dependency_count,
        dependency_gap_score=dependency_gap_score,
        deadline_pressure_score=deadline_pressure_score,
        resolution_recheck_priority_score=priority_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            status=status,
            authority_staleness_score=authority_staleness_score,
            dependency_gap_score=dependency_gap_score,
            deadline_pressure_score=deadline_pressure_score,
            config=config,
        ),
    )


def _authority_staleness_score(
    authority_age_seconds: Decimal,
    config: ResearchSourceClaimResolutionRecheckPriorityConfig,
) -> Decimal:
    if authority_age_seconds <= config.fresh_authority_age_seconds:
        return ZERO
    if authority_age_seconds >= config.stale_authority_age_seconds:
        return ONE
    denominator = config.stale_authority_age_seconds - config.fresh_authority_age_seconds
    return _cap_probability(
        (authority_age_seconds - config.fresh_authority_age_seconds) / denominator,
    )


def _deadline_pressure_score(
    resolution_due_at: datetime | None,
    config: ResearchSourceClaimResolutionRecheckPriorityConfig,
    generated_at: datetime,
) -> Decimal:
    if resolution_due_at is None:
        return ZERO
    seconds_until_due = _datetime_delta_seconds(resolution_due_at, generated_at)
    if seconds_until_due <= ZERO:
        return ONE
    if seconds_until_due >= config.deadline_pressure_window_seconds:
        return ZERO
    return _cap_probability(
        ONE - (seconds_until_due / config.deadline_pressure_window_seconds),
    )


def _resolution_recheck_priority_score(
    *,
    authority_staleness_score: Decimal,
    authority_mismatch_score: Decimal,
    evidence_gap_score: Decimal,
    source_conflict_score: Decimal,
    revision_pressure_score: Decimal,
    dependency_gap_score: Decimal,
    deadline_pressure_score: Decimal,
) -> Decimal:
    return _cap_probability(
        (
            authority_staleness_score
            + authority_mismatch_score
            + evidence_gap_score
            + source_conflict_score
            + revision_pressure_score
            + dependency_gap_score
            + deadline_pressure_score
        )
        / SEVEN,
    )


def _row_status(
    *,
    authority_staleness_score: Decimal,
    authority_match_score: Decimal,
    resolution_evidence_strength: Decimal,
    source_conflict_score: Decimal,
    revision_pressure_score: Decimal,
    dependency_gap_score: Decimal,
    deadline_pressure_score: Decimal,
    resolution_recheck_priority_score: Decimal,
    config: ResearchSourceClaimResolutionRecheckPriorityConfig,
) -> str:
    if (
        resolution_recheck_priority_score >= config.block_priority_score
        or authority_staleness_score >= config.block_authority_staleness_score
        or authority_match_score <= config.block_authority_match_score
        or resolution_evidence_strength <= config.block_resolution_evidence_strength
        or source_conflict_score >= config.block_source_conflict_score
        or revision_pressure_score >= config.block_revision_pressure_score
        or dependency_gap_score >= config.block_dependency_gap_score
        or deadline_pressure_score >= config.block_deadline_pressure_score
    ):
        return "block"
    if (
        resolution_recheck_priority_score >= config.watch_priority_score
        or authority_staleness_score >= config.watch_authority_staleness_score
        or authority_match_score <= config.min_authority_match_score
        or resolution_evidence_strength <= config.min_resolution_evidence_strength
        or source_conflict_score >= config.watch_source_conflict_score
        or revision_pressure_score >= config.watch_revision_pressure_score
        or dependency_gap_score >= config.watch_dependency_gap_score
        or deadline_pressure_score >= config.watch_deadline_pressure_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observation: ResearchSourceClaimResolutionRecheckPriorityObservation,
    status: str,
    authority_staleness_score: Decimal,
    dependency_gap_score: Decimal,
    deadline_pressure_score: Decimal,
    config: ResearchSourceClaimResolutionRecheckPriorityConfig,
) -> tuple[str, ...]:
    reason_codes = {f"resolution_recheck_priority_{status}"}
    if authority_staleness_score >= config.block_authority_staleness_score:
        reason_codes.add("authority_staleness_block")
    elif authority_staleness_score >= config.watch_authority_staleness_score:
        reason_codes.add("authority_staleness_watch")
    else:
        reason_codes.add("authority_staleness_clear")
    if observation.authority_match_score <= config.block_authority_match_score:
        reason_codes.add("authority_mismatch_block")
    elif observation.authority_match_score <= config.min_authority_match_score:
        reason_codes.add("authority_mismatch_watch")
    else:
        reason_codes.add("authority_mismatch_clear")
    if (
        observation.resolution_evidence_strength
        <= config.block_resolution_evidence_strength
    ):
        reason_codes.add("evidence_gap_block")
    elif (
        observation.resolution_evidence_strength
        <= config.min_resolution_evidence_strength
    ):
        reason_codes.add("evidence_gap_watch")
    else:
        reason_codes.add("evidence_gap_clear")
    if observation.source_conflict_score >= config.block_source_conflict_score:
        reason_codes.add("source_conflict_block")
    elif observation.source_conflict_score >= config.watch_source_conflict_score:
        reason_codes.add("source_conflict_watch")
    else:
        reason_codes.add("source_conflict_clear")
    if observation.revision_pressure_score >= config.block_revision_pressure_score:
        reason_codes.add("source_revision_pressure_block")
    elif observation.revision_pressure_score >= config.watch_revision_pressure_score:
        reason_codes.add("source_revision_pressure_watch")
    else:
        reason_codes.add("source_revision_pressure_clear")
    if dependency_gap_score >= config.block_dependency_gap_score:
        reason_codes.add("dependency_gap_block")
    elif dependency_gap_score >= config.watch_dependency_gap_score:
        reason_codes.add("dependency_gap_watch")
    else:
        reason_codes.add("dependency_gap_clear")
    if deadline_pressure_score >= config.block_deadline_pressure_score:
        reason_codes.add("resolution_deadline_pressure_block")
    elif deadline_pressure_score >= config.watch_deadline_pressure_score:
        reason_codes.add("resolution_deadline_pressure_watch")
    else:
        reason_codes.add("resolution_deadline_pressure_clear")
    for reason_code in observation.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_observations(
    values: Iterable[object],
) -> tuple[ResearchSourceClaimResolutionRecheckPriorityObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceClaimResolutionRecheckPriorityObservation] = []
    seen: set[tuple[str, str]] = set()
    for observation in observations:
        _require_exact_type(
            "observation",
            observation,
            ResearchSourceClaimResolutionRecheckPriorityObservation,
        )
        _require_hard_flags("observation", observation)
        key = (observation.claim_bucket, observation.authority_bucket)
        if key in seen:
            raise ValueError("duplicate claim_bucket and authority_bucket pair")
        seen.add(key)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.claim_bucket, item.authority_bucket),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceClaimResolutionRecheckPriorityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchSourceClaimResolutionRecheckPriorityRow] = []
    seen: set[tuple[str, str]] = set()
    for row in value:
        _require_exact_type("row", row, ResearchSourceClaimResolutionRecheckPriorityRow)
        _require_hard_flags("row", row)
        _validate_row_digest(row)
        key = (row.claim_bucket, row.authority_bucket)
        if key in seen:
            raise ValueError("duplicate row claim_bucket and authority_bucket pair")
        seen.add(key)
        rows.append(row)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceClaimResolutionRecheckPriorityRow,
) -> tuple[Decimal, int, str, str]:
    return (
        -row.resolution_recheck_priority_score,
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.claim_bucket,
        row.authority_bucket,
    )


def _report_status(
    rows: tuple[ResearchSourceClaimResolutionRecheckPriorityRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_status_count(
    rows: tuple[ResearchSourceClaimResolutionRecheckPriorityRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _count(sum(1 for row in rows if row.status == status))


def _row_reason_code_count(
    rows: tuple[ResearchSourceClaimResolutionRecheckPriorityRow, ...],
    *reason_codes: str,
) -> Decimal:
    reason_code_set = set(reason_codes)
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code in reason_code_set for reason_code in row.reason_codes)
        ),
    )


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimResolutionRecheckPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_recheck_priority_empty",)
    reason_codes: set[str] = {f"resolution_recheck_priority_{_report_status(rows)}"}
    for row in rows:
        reason_codes.update(row.reason_codes)
    return tuple(sorted(reason_codes))


def _validate_row_consistency(
    row: ResearchSourceClaimResolutionRecheckPriorityRow,
) -> None:
    if row.authority_mismatch_score != _cap_probability(ONE - row.authority_match_score):
        raise ValueError("authority_mismatch_score must match authority_match_score")
    if row.evidence_gap_score != _cap_probability(
        ONE - row.resolution_evidence_strength,
    ):
        raise ValueError(
            "evidence_gap_score must match resolution_evidence_strength",
        )
    if row.dependency_gap_score != _ratio(
        row.unresolved_dependency_count,
        row.required_dependency_count,
    ):
        raise ValueError("dependency_gap_score must match dependency counts")
    expected_priority = _resolution_recheck_priority_score(
        authority_staleness_score=row.authority_staleness_score,
        authority_mismatch_score=row.authority_mismatch_score,
        evidence_gap_score=row.evidence_gap_score,
        source_conflict_score=row.source_conflict_score,
        revision_pressure_score=row.revision_pressure_score,
        dependency_gap_score=row.dependency_gap_score,
        deadline_pressure_score=row.deadline_pressure_score,
    )
    if row.resolution_recheck_priority_score != expected_priority:
        raise ValueError("resolution_recheck_priority_score must match components")
    if row.status == "pass" and f"resolution_recheck_priority_{row.status}" not in row.reason_codes:
        raise ValueError("pass rows must include pass reason code")


def _validate_report_consistency(
    report: ResearchSourceClaimResolutionRecheckPriorityReport,
) -> None:
    rows = report.rows
    expected_counts = {
        "observation_count": _count(len(rows)),
        "pass_count": _row_status_count(rows, "pass"),
        "watch_count": _row_status_count(rows, "watch"),
        "block_count": _row_status_count(rows, "block"),
        "authority_stale_count": _row_reason_code_count(
            rows,
            "authority_staleness_watch",
            "authority_staleness_block",
        ),
        "authority_mismatch_count": _row_reason_code_count(
            rows,
            "authority_mismatch_watch",
            "authority_mismatch_block",
        ),
        "evidence_gap_count": _row_reason_code_count(
            rows,
            "evidence_gap_watch",
            "evidence_gap_block",
        ),
        "conflict_count": _row_reason_code_count(
            rows,
            "source_conflict_watch",
            "source_conflict_block",
        ),
        "revision_pressure_count": _row_reason_code_count(
            rows,
            "source_revision_pressure_watch",
            "source_revision_pressure_block",
        ),
        "dependency_gap_count": _row_reason_code_count(
            rows,
            "dependency_gap_watch",
            "dependency_gap_block",
        ),
        "deadline_pressure_count": _row_reason_code_count(
            rows,
            "resolution_deadline_pressure_watch",
            "resolution_deadline_pressure_block",
        ),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_resolution_recheck_priority_score != _average(
        tuple(row.resolution_recheck_priority_score for row in rows),
    ):
        raise ValueError("average_resolution_recheck_priority_score must match rows")
    if report.max_resolution_recheck_priority_score != _max_decimal(
        tuple(row.resolution_recheck_priority_score for row in rows),
    ):
        raise ValueError("max_resolution_recheck_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")


def _row_values_without_digest(
    row: ResearchSourceClaimResolutionRecheckPriorityRow,
) -> dict[str, object]:
    values = asdict(row)
    values.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    return values


def _report_values_without_digest(
    report: ResearchSourceClaimResolutionRecheckPriorityReport,
) -> dict[str, object]:
    values = _report_values(report)
    values.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    return values


def _report_values(
    report: ResearchSourceClaimResolutionRecheckPriorityReport,
) -> dict[str, object]:
    return asdict(report)


def _row_digest_from_values(values: dict[str, object]) -> str:
    return _digest_from_values(values)


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _digest_from_values(values)


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_row_digest(row: ResearchSourceClaimResolutionRecheckPriorityRow) -> None:
    expected = _row_digest_from_values(_row_values_without_digest(row))
    if row.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match row payload")


def _validate_report_digest(
    report: ResearchSourceClaimResolutionRecheckPriorityReport,
) -> None:
    expected = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_REPORT_FIELDS, "report")
    _require_public_label("config_version", payload["config_version"])
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_status("status", payload["status"])
    for field_name in (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "authority_stale_count",
        "authority_mismatch_count",
        "evidence_gap_count",
        "conflict_count",
        "revision_pressure_count",
        "dependency_gap_count",
        "deadline_pressure_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "average_resolution_recheck_priority_score",
        "max_resolution_recheck_priority_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _normalize_payload_reason_codes("reason_codes", payload["reason_codes"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain row payload dictionaries")
        _reject_unsafe_public_payload("row payload", row_payload)
        _validate_public_row_payload(row_payload)
    _require_hard_flags("payload", _DictFlags(payload))
    digest = _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    unsigned_payload = dict(payload)
    unsigned_payload.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    if digest != _report_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match report payload")
    _validate_public_report_payload_consistency(payload)


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_payload_fields(payload, PUBLIC_ROW_FIELDS, "row")
    for field_name in ("claim_bucket", "authority_bucket"):
        _require_public_label(field_name, payload[field_name])
    for field_name in (
        "observed_age_seconds",
        "authority_age_seconds",
        "unresolved_dependency_count",
        "required_dependency_count",
    ):
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            whole=field_name
            in {"unresolved_dependency_count", "required_dependency_count"},
        )
    for field_name in (
        "authority_staleness_score",
        "authority_match_score",
        "authority_mismatch_score",
        "resolution_evidence_strength",
        "evidence_gap_score",
        "source_conflict_score",
        "revision_pressure_score",
        "dependency_gap_score",
        "deadline_pressure_score",
        "resolution_recheck_priority_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], probability=True)
    _require_status("status", payload["status"])
    _normalize_payload_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    digest = _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    unsigned_payload = dict(payload)
    unsigned_payload.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    if digest != _row_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match row payload")


def _validate_public_report_payload_consistency(payload: dict[str, object]) -> None:
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    expected_status = _payload_report_status(rows)
    expected_counts = {
        "observation_count": _count(len(rows)),
        "pass_count": _payload_status_count(rows, "pass"),
        "watch_count": _payload_status_count(rows, "watch"),
        "block_count": _payload_status_count(rows, "block"),
        "authority_stale_count": _payload_reason_code_count(
            rows,
            "authority_staleness_watch",
            "authority_staleness_block",
        ),
        "authority_mismatch_count": _payload_reason_code_count(
            rows,
            "authority_mismatch_watch",
            "authority_mismatch_block",
        ),
        "evidence_gap_count": _payload_reason_code_count(
            rows,
            "evidence_gap_watch",
            "evidence_gap_block",
        ),
        "conflict_count": _payload_reason_code_count(
            rows,
            "source_conflict_watch",
            "source_conflict_block",
        ),
        "revision_pressure_count": _payload_reason_code_count(
            rows,
            "source_revision_pressure_watch",
            "source_revision_pressure_block",
        ),
        "dependency_gap_count": _payload_reason_code_count(
            rows,
            "dependency_gap_watch",
            "dependency_gap_block",
        ),
        "deadline_pressure_count": _payload_reason_code_count(
            rows,
            "resolution_deadline_pressure_watch",
            "resolution_deadline_pressure_block",
        ),
    }
    for field_name, expected_value in expected_counts.items():
        actual_value = _require_decimal_payload_string(
            field_name,
            payload[field_name],
            whole=True,
        )
        if actual_value != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if payload["status"] != expected_status:
        raise ValueError("status must match rows")
    row_scores = tuple(
        _require_decimal_payload_string(
            "resolution_recheck_priority_score",
            row["resolution_recheck_priority_score"],
            probability=True,
        )
        for row in rows
        if type(row) is dict
    )
    if _require_decimal_payload_string(
        "average_resolution_recheck_priority_score",
        payload["average_resolution_recheck_priority_score"],
        probability=True,
    ) != _average(row_scores):
        raise ValueError("average_resolution_recheck_priority_score must match rows")
    if _require_decimal_payload_string(
        "max_resolution_recheck_priority_score",
        payload["max_resolution_recheck_priority_score"],
        probability=True,
    ) != _max_decimal(row_scores):
        raise ValueError("max_resolution_recheck_priority_score must match rows")
    if _normalize_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
    ) != _payload_report_reason_codes(rows, expected_status):
        raise ValueError("reason_codes must match rows")
    if rows != sorted(rows, key=_payload_row_sort_key):
        raise ValueError("rows must be sorted deterministically")


def _payload_status_count(rows: list[object], status: str) -> Decimal:
    _require_status("status", status)
    return _count(
        sum(1 for row in rows if type(row) is dict and row["status"] == status),
    )


def _payload_reason_code_count(rows: list[object], *reason_codes: str) -> Decimal:
    reason_code_set = set(reason_codes)
    return _count(
        sum(
            1
            for row in rows
            if type(row) is dict
            and any(
                reason_code in reason_code_set
                for reason_code in row["reason_codes"]
                if type(reason_code) is str
            )
        ),
    )


def _payload_report_status(rows: list[object]) -> str:
    if any(type(row) is dict and row["status"] == "block" for row in rows):
        return "block"
    if any(type(row) is dict and row["status"] == "watch" for row in rows):
        return "watch"
    return "pass"


def _payload_report_reason_codes(
    rows: list[object],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_recheck_priority_empty",)
    reason_codes: set[str] = {f"resolution_recheck_priority_{status}"}
    for row in rows:
        if type(row) is dict:
            reason_codes.update(
                reason_code
                for reason_code in row["reason_codes"]
                if type(reason_code) is str
            )
    return tuple(sorted(reason_codes))


def _payload_row_sort_key(row: object) -> tuple[Decimal, int, str, str]:
    if type(row) is not dict:
        raise ValueError("rows must contain row payload dictionaries")
    return (
        -_require_decimal_payload_string(
            "resolution_recheck_priority_score",
            row["resolution_recheck_priority_score"],
            probability=True,
        ),
        {"block": 0, "watch": 1, "pass": 2}[_require_status("status", row["status"])],
        str(row["claim_bucket"]),
        str(row["authority_bucket"]),
    )


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


def _json_ready(value: Any) -> Any:
    if type(value) is bool or value is None:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal subclasses are not supported")
        return _quantize_decimal(value).to_eng_string()
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
    raise ValueError(f"unsupported JSON payload value {type(value).__name__}")


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


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECOND_DIVISOR
    return _quantize_decimal(seconds + microseconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_input_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or not REASON_CODE_RE.fullmatch(reason_code):
            raise ValueError(f"{field_name} must be reason codes")
        _reject_unsafe_public_string(field_name, reason_code)
        seen.add(reason_code)
    return tuple(sorted(seen))


def _normalize_public_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_reason_code(field_name, reason_code)
        seen.add(reason_code)
    return tuple(sorted(seen))


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    codes: list[str] = []
    for reason_code in value:
        codes.append(_require_public_reason_code(field_name, reason_code))
    if len(codes) != len(set(codes)):
        raise ValueError(f"{field_name} must be unique")
    return tuple(codes)


def _require_public_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be reason codes")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_private_text(field_name: str, value: object) -> str:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{field_name} must be nonempty text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in RESOLUTION_RECHECK_PRIORITY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    whole: bool = False,
    probability: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal payload string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal payload string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if probability and normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime payload string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime payload string") from exc
    return _as_utc(field_name, parsed)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name.startswith("private_"):
                continue
            _reject_unsafe_public_string(label, field.name, is_key=True)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(label, key, is_key=True)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(
    field_name: str,
    value: str,
    *,
    is_key: bool = False,
) -> None:
    lowered = value.lower()
    fragments = UNSAFE_KEY_FRAGMENTS if is_key else UNSAFE_VALUE_FRAGMENTS
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"unsafe public value in {field_name}")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]
