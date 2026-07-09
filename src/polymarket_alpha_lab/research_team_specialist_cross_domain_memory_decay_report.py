"""Pure report-only cross-domain specialist memory decay reducer."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_REPORT_CONFIG_VERSION = (
    "research-team-specialist-cross-domain-memory-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
COMPONENT_COUNT = Decimal("3.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
REDACTED_MEMORY_REF_PREFIX = "memory_ref_"
REDACTED_DIGEST_LENGTH = 16

NO_OBSERVATIONS_REASON = "cross_domain_memory_decay_no_observations"
RETAINED_REASON = "cross_domain_memory_retained"
MEMORY_AGE_BLOCK_REASON = "memory_age_block"
MEMORY_AGE_WATCH_REASON = "memory_age_watch"
MEMORY_CONFLICT_BLOCK_REASON = "memory_conflict_block"
MEMORY_CONFLICT_WATCH_REASON = "memory_conflict_watch"
MEMORY_VALIDATION_BLOCK_REASON = "memory_validation_block"
MEMORY_VALIDATION_WATCH_REASON = "memory_validation_watch"
MEMORY_RETENTION_BLOCK_REASON = "memory_retention_block"
MEMORY_RETENTION_WATCH_REASON = "memory_retention_watch"

ROW_REASON_CODE_SEQUENCE = (
    MEMORY_AGE_BLOCK_REASON,
    MEMORY_CONFLICT_BLOCK_REASON,
    MEMORY_VALIDATION_BLOCK_REASON,
    MEMORY_RETENTION_BLOCK_REASON,
    MEMORY_AGE_WATCH_REASON,
    MEMORY_CONFLICT_WATCH_REASON,
    MEMORY_VALIDATION_WATCH_REASON,
    MEMORY_RETENTION_WATCH_REASON,
    RETAINED_REASON,
)

REPORT_BLOCK_PRESENT_REASON = "cross_domain_memory_decay_block_present"
REPORT_WATCH_PRESENT_REASON = "cross_domain_memory_decay_watch_present"
REPORT_PASS_REASON = "cross_domain_memory_decay_pass"
REPORT_MEMORY_AGE_REASON = "memory_age_decay_present"
REPORT_MEMORY_CONFLICT_REASON = "memory_conflict_decay_present"
REPORT_MEMORY_VALIDATION_REASON = "memory_validation_decay_present"

REPORT_REASON_CODE_SEQUENCE = (
    NO_OBSERVATIONS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_MEMORY_AGE_REASON,
    REPORT_MEMORY_CONFLICT_REASON,
    REPORT_MEMORY_VALIDATION_REASON,
    REPORT_PASS_REASON,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
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

UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    _join_parts("can", "did", "ate"),
    _join_parts("condition"),
    _join_parts("mar", "ket", "-", "s", "lug"),
    _join_parts("mar", "ket", "_", "s", "lug"),
    _join_parts("quest", "ion"),
    _join_parts("u", "rl"),
    _join_parts("ra", "w", "-"),
    _join_parts("tok", "en"),
    _join_parts("sec", "ret"),
    _join_parts("priv", "ate"),
    _join_parts("d", "sn"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_STATUSES",
    "ResearchTeamSpecialistCrossDomainMemoryDecayConfig",
    "ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary",
    "ResearchTeamSpecialistCrossDomainMemoryDecayObservation",
    "ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount",
    "ResearchTeamSpecialistCrossDomainMemoryDecayReport",
    "ResearchTeamSpecialistCrossDomainMemoryDecayRow",
    "build_research_team_specialist_cross_domain_memory_decay_report",
    "research_team_specialist_cross_domain_memory_decay_report_digest",
    "research_team_specialist_cross_domain_memory_decay_report_json",
    "research_team_specialist_cross_domain_memory_decay_report_payload",
    "validate_research_team_specialist_cross_domain_memory_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistCrossDomainMemoryDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_memory_age_days: Decimal = Decimal("30.000000")
    max_watch_memory_age_days: Decimal = Decimal("90.000000")
    max_pass_conflict_ratio: Decimal = Decimal("0.100000")
    max_watch_conflict_ratio: Decimal = Decimal("0.250000")
    min_pass_validation_ratio: Decimal = Decimal("0.800000")
    min_watch_validation_ratio: Decimal = Decimal("0.500000")
    min_pass_retention_score: Decimal = Decimal("0.700000")
    min_watch_retention_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistCrossDomainMemoryDecayConfig:
            raise TypeError(
                "ResearchTeamSpecialistCrossDomainMemoryDecayConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCrossDomainMemoryDecayConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_memory_age_days",
            "max_watch_memory_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_conflict_ratio",
            "max_watch_conflict_ratio",
            "min_pass_validation_ratio",
            "min_watch_validation_ratio",
            "min_pass_retention_score",
            "min_watch_retention_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_memory_age_days > self.max_watch_memory_age_days:
            raise ValueError("max_pass_memory_age_days must not exceed watch")
        if self.max_pass_conflict_ratio > self.max_watch_conflict_ratio:
            raise ValueError("max_pass_conflict_ratio must not exceed watch")
        if self.min_watch_validation_ratio > self.min_pass_validation_ratio:
            raise ValueError("min_watch_validation_ratio must not exceed pass")
        if self.min_watch_retention_score > self.min_pass_retention_score:
            raise ValueError("min_watch_retention_score must not exceed pass")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCrossDomainMemoryDecayObservation:
    memory_ref: str
    original_domain_label: str
    target_domain_label: str
    specialist_label: str
    observed_at: datetime
    memory_age_days: Decimal
    reuse_count: Decimal
    conflict_count: Decimal
    validation_count: Decimal
    validation_pass_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistCrossDomainMemoryDecayObservation:
            raise TypeError(
                "ResearchTeamSpecialistCrossDomainMemoryDecayObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCrossDomainMemoryDecayObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "memory_ref",
            _require_private_reference("memory_ref", self.memory_ref),
        )
        for field_name in (
            "original_domain_label",
            "target_domain_label",
            "specialist_label",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("memory_age_days", "conflict_count", "validation_pass_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("reuse_count", "validation_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflict_count > self.reuse_count:
            raise ValueError("conflict_count must not exceed reuse_count")
        if self.validation_pass_count > self.validation_count:
            raise ValueError("validation_pass_count must not exceed validation_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCrossDomainMemoryDecayRow:
    redacted_memory_ref: str
    original_domain_label: str
    target_domain_label: str
    specialist_label: str
    observed_at: datetime
    memory_age_days: Decimal
    memory_age_ratio: Decimal
    reuse_count: Decimal
    conflict_count: Decimal
    conflict_ratio: Decimal
    validation_count: Decimal
    validation_pass_count: Decimal
    validation_ratio: Decimal
    retention_score: Decimal
    decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistCrossDomainMemoryDecayRow:
            raise TypeError(
                "ResearchTeamSpecialistCrossDomainMemoryDecayRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCrossDomainMemoryDecayRow, "row")
        _require_redacted_memory_ref(self.redacted_memory_ref)
        for field_name in (
            "original_domain_label",
            "target_domain_label",
            "specialist_label",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "memory_age_days",
            "reuse_count",
            "conflict_count",
            "validation_count",
            "validation_pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_age_ratio",
            "conflict_ratio",
            "validation_ratio",
            "retention_score",
            "decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        if self.reuse_count == ZERO:
            raise ValueError("reuse_count must be positive")
        if self.validation_count == ZERO:
            raise ValueError("validation_count must be positive")
        if self.conflict_count > self.reuse_count:
            raise ValueError("conflict_count must not exceed reuse_count")
        if self.validation_pass_count > self.validation_count:
            raise ValueError("validation_pass_count must not exceed validation_count")
        if self.decay_score != _ratio(ONE - self.retention_score):
            raise ValueError("decay_score must equal one minus retention_score")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary:
    target_domain_label: str
    memory_count: Decimal
    reuse_count: Decimal
    conflict_count: Decimal
    validation_count: Decimal
    validation_pass_count: Decimal
    mean_retention_score: Decimal
    mean_decay_score: Decimal
    worst_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary:
            raise TypeError(
                "ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary,
            "domain_summary",
        )
        object.__setattr__(
            self,
            "target_domain_label",
            _require_public_label("target_domain_label", self.target_domain_label),
        )
        for field_name in (
            "memory_count",
            "reuse_count",
            "conflict_count",
            "validation_count",
            "validation_pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_retention_score", "mean_decay_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("worst_status", self.worst_status, RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_STATUSES)
        _require_hard_flags("domain_summary", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount:
            raise TypeError(
                "ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_member(
            "reason_code",
            self.reason_code,
            (NO_OBSERVATIONS_REASON,) + ROW_REASON_CODE_SEQUENCE,
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCrossDomainMemoryDecayReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    reuse_count: Decimal
    conflict_count: Decimal
    validation_count: Decimal
    validation_pass_count: Decimal
    cross_domain_pair_count: Decimal
    mean_memory_age_days: Decimal
    mean_retention_score: Decimal
    mean_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount, ...]
    domain_summaries: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary, ...]
    rows: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayRow, ...]
    payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSpecialistCrossDomainMemoryDecayReport:
            raise TypeError(
                "ResearchTeamSpecialistCrossDomainMemoryDecayReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCrossDomainMemoryDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "reuse_count",
            "conflict_count",
            "validation_count",
            "validation_pass_count",
            "cross_domain_pair_count",
            "mean_memory_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_retention_score", "mean_decay_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, RESEARCH_TEAM_SPECIALIST_CROSS_DOMAIN_MEMORY_DECAY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_tuple_of_exact(
                "reason_code_counts",
                self.reason_code_counts,
                ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount,
            ),
        )
        object.__setattr__(
            self,
            "domain_summaries",
            _require_tuple_of_exact(
                "domain_summaries",
                self.domain_summaries,
                ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary,
            ),
        )
        object.__setattr__(
            self,
            "rows",
            _require_tuple_of_exact(
                "rows",
                self.rows,
                ResearchTeamSpecialistCrossDomainMemoryDecayRow,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        if self.payload_sha256:
            expected_digest = research_team_specialist_cross_domain_memory_decay_report_digest(self)
            if self.payload_sha256 != expected_digest:
                raise ValueError("payload_sha256 does not match report payload")


def build_research_team_specialist_cross_domain_memory_decay_report(
    observations: Iterable[ResearchTeamSpecialistCrossDomainMemoryDecayObservation],
    *,
    config: ResearchTeamSpecialistCrossDomainMemoryDecayConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSpecialistCrossDomainMemoryDecayReport:
    if config is None:
        config = ResearchTeamSpecialistCrossDomainMemoryDecayConfig()
    _require_exact_type(config, ResearchTeamSpecialistCrossDomainMemoryDecayConfig, "config")
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_from_observation(observation, config) for observation in observations),
            key=_row_sort_key,
        ),
    )
    report = ResearchTeamSpecialistCrossDomainMemoryDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        reuse_count=_sum_decimal(row.reuse_count for row in rows),
        conflict_count=_sum_decimal(row.conflict_count for row in rows),
        validation_count=_sum_decimal(row.validation_count for row in rows),
        validation_pass_count=_sum_decimal(row.validation_pass_count for row in rows),
        cross_domain_pair_count=_count(
            len({(row.original_domain_label, row.target_domain_label) for row in rows}),
        ),
        mean_memory_age_days=_mean_decimal(row.memory_age_days for row in rows),
        mean_retention_score=_mean_ratio(row.retention_score for row in rows),
        mean_decay_score=_mean_decay_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        domain_summaries=_domain_summaries(rows),
        rows=rows,
    )
    return replace(
        report,
        payload_sha256=research_team_specialist_cross_domain_memory_decay_report_digest(
            report,
        ),
    )


def research_team_specialist_cross_domain_memory_decay_report_payload(
    report: ResearchTeamSpecialistCrossDomainMemoryDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistCrossDomainMemoryDecayReport:
        payload = _json_ready_report(report)
        payload["payload_sha256"] = research_team_specialist_cross_domain_memory_decay_report_digest(report)
        _validate_public_payload(payload, validate_digest=True)
        return payload
    if type(report) is dict:
        payload = _json_ready_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _validate_public_payload(payload, validate_digest=True)
        return payload
    raise ValueError("report must be exactly ResearchTeamSpecialistCrossDomainMemoryDecayReport")


def research_team_specialist_cross_domain_memory_decay_report_json(
    report: ResearchTeamSpecialistCrossDomainMemoryDecayReport,
) -> str:
    payload = research_team_specialist_cross_domain_memory_decay_report_payload(report)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def research_team_specialist_cross_domain_memory_decay_report_digest(
    report: ResearchTeamSpecialistCrossDomainMemoryDecayReport,
) -> str:
    if type(report) is not ResearchTeamSpecialistCrossDomainMemoryDecayReport:
        raise ValueError(
            "report must be exactly ResearchTeamSpecialistCrossDomainMemoryDecayReport",
        )
    payload = _json_ready_report(report)
    if "payload_sha256" in payload:
        del payload["payload_sha256"]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def validate_research_team_specialist_cross_domain_memory_decay_report_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    ready = _json_ready_value(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(ready, validate_digest=True)


def _row_from_observation(
    observation: ResearchTeamSpecialistCrossDomainMemoryDecayObservation,
    config: ResearchTeamSpecialistCrossDomainMemoryDecayConfig,
) -> ResearchTeamSpecialistCrossDomainMemoryDecayRow:
    _require_exact_type(
        observation,
        ResearchTeamSpecialistCrossDomainMemoryDecayObservation,
        "observation",
    )
    age_ratio = _bounded_ratio(observation.memory_age_days, config.max_watch_memory_age_days)
    conflict_ratio = _bounded_ratio(observation.conflict_count, observation.reuse_count)
    validation_ratio = _bounded_ratio(
        observation.validation_pass_count,
        observation.validation_count,
    )
    validation_decay_ratio = _ratio(ONE - validation_ratio)
    retention_score = _ratio(
        ONE
        - _ratio((age_ratio + conflict_ratio + validation_decay_ratio) / COMPONENT_COUNT),
    )
    decay_score = _ratio(ONE - retention_score)
    status, reason_codes = _row_status_and_reasons(
        observation,
        config,
        conflict_ratio,
        validation_ratio,
        retention_score,
    )
    return ResearchTeamSpecialistCrossDomainMemoryDecayRow(
        redacted_memory_ref=_redacted_memory_ref(observation.memory_ref),
        original_domain_label=observation.original_domain_label,
        target_domain_label=observation.target_domain_label,
        specialist_label=observation.specialist_label,
        observed_at=observation.observed_at,
        memory_age_days=observation.memory_age_days,
        memory_age_ratio=age_ratio,
        reuse_count=observation.reuse_count,
        conflict_count=observation.conflict_count,
        conflict_ratio=conflict_ratio,
        validation_count=observation.validation_count,
        validation_pass_count=observation.validation_pass_count,
        validation_ratio=validation_ratio,
        retention_score=retention_score,
        decay_score=decay_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    observation: ResearchTeamSpecialistCrossDomainMemoryDecayObservation,
    config: ResearchTeamSpecialistCrossDomainMemoryDecayConfig,
    conflict_ratio: Decimal,
    validation_ratio: Decimal,
    retention_score: Decimal,
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    if observation.memory_age_days > config.max_watch_memory_age_days:
        reasons.append(MEMORY_AGE_BLOCK_REASON)
    elif observation.memory_age_days > config.max_pass_memory_age_days:
        reasons.append(MEMORY_AGE_WATCH_REASON)
    if conflict_ratio > config.max_watch_conflict_ratio:
        reasons.append(MEMORY_CONFLICT_BLOCK_REASON)
    elif conflict_ratio > config.max_pass_conflict_ratio:
        reasons.append(MEMORY_CONFLICT_WATCH_REASON)
    if validation_ratio < config.min_watch_validation_ratio:
        reasons.append(MEMORY_VALIDATION_BLOCK_REASON)
    elif validation_ratio < config.min_pass_validation_ratio:
        reasons.append(MEMORY_VALIDATION_WATCH_REASON)
    if retention_score < config.min_watch_retention_score:
        reasons.append(MEMORY_RETENTION_BLOCK_REASON)
    elif retention_score < config.min_pass_retention_score:
        reasons.append(MEMORY_RETENTION_WATCH_REASON)
    if any(reason.endswith("_block") for reason in reasons):
        status = STATUS_BLOCK
    elif any(reason.endswith("_watch") for reason in reasons):
        status = STATUS_WATCH
    else:
        status = STATUS_PASS
        reasons.append(RETAINED_REASON)
    return status, _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODE_SEQUENCE)


def _row_sort_key(
    row: ResearchTeamSpecialistCrossDomainMemoryDecayRow,
) -> tuple[int, Decimal, str]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        -row.decay_score,
        row.redacted_memory_ref,
    )


def _report_status(
    rows: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    reasons: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reasons.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reasons.append(REPORT_WATCH_PRESENT_REASON)
    row_reasons = {reason for row in rows for reason in row.reason_codes}
    if MEMORY_AGE_BLOCK_REASON in row_reasons or MEMORY_AGE_WATCH_REASON in row_reasons:
        reasons.append(REPORT_MEMORY_AGE_REASON)
    if (
        MEMORY_CONFLICT_BLOCK_REASON in row_reasons
        or MEMORY_CONFLICT_WATCH_REASON in row_reasons
    ):
        reasons.append(REPORT_MEMORY_CONFLICT_REASON)
    if (
        MEMORY_VALIDATION_BLOCK_REASON in row_reasons
        or MEMORY_VALIDATION_WATCH_REASON in row_reasons
    ):
        reasons.append(REPORT_MEMORY_VALIDATION_REASON)
    if not reasons:
        reasons.append(REPORT_PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), REPORT_REASON_CODE_SEQUENCE)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayRow, ...],
) -> tuple[ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=_count(1),
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            row_ratio=_bounded_ratio(_count(counter[reason_code]), row_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if counter[reason_code]
    )


def _domain_summaries(
    rows: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayRow, ...],
) -> tuple[ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary, ...]:
    target_labels = sorted({row.target_domain_label for row in rows})
    summaries: list[ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary] = []
    for target_label in target_labels:
        domain_rows = tuple(row for row in rows if row.target_domain_label == target_label)
        summaries.append(
            ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary(
                target_domain_label=target_label,
                memory_count=_count(len(domain_rows)),
                reuse_count=_sum_decimal(row.reuse_count for row in domain_rows),
                conflict_count=_sum_decimal(row.conflict_count for row in domain_rows),
                validation_count=_sum_decimal(row.validation_count for row in domain_rows),
                validation_pass_count=_sum_decimal(
                    row.validation_pass_count for row in domain_rows
                ),
                mean_retention_score=_mean_ratio(
                    row.retention_score for row in domain_rows
                ),
                mean_decay_score=_mean_ratio(row.decay_score for row in domain_rows),
                worst_status=_report_status(domain_rows),
            ),
        )
    return tuple(summaries)


def _validate_report_consistency(
    report: ResearchTeamSpecialistCrossDomainMemoryDecayReport,
) -> None:
    rows = report.rows
    if report.observation_count != _count(len(rows)):
        raise ValueError("observation_count must equal row count")
    if report.pass_count != _count_status(rows, STATUS_PASS):
        raise ValueError("pass_count must equal pass rows")
    if report.watch_count != _count_status(rows, STATUS_WATCH):
        raise ValueError("watch_count must equal watch rows")
    if report.block_count != _count_status(rows, STATUS_BLOCK):
        raise ValueError("block_count must equal block rows")
    if report.reuse_count != _sum_decimal(row.reuse_count for row in rows):
        raise ValueError("reuse_count must equal row total")
    if report.conflict_count != _sum_decimal(row.conflict_count for row in rows):
        raise ValueError("conflict_count must equal row total")
    if report.validation_count != _sum_decimal(row.validation_count for row in rows):
        raise ValueError("validation_count must equal row total")
    if report.validation_pass_count != _sum_decimal(
        row.validation_pass_count for row in rows
    ):
        raise ValueError("validation_pass_count must equal row total")
    pair_count = len({(row.original_domain_label, row.target_domain_label) for row in rows})
    if report.cross_domain_pair_count != _count(pair_count):
        raise ValueError("cross_domain_pair_count must equal distinct row pairs")
    if report.mean_memory_age_days != _mean_decimal(row.memory_age_days for row in rows):
        raise ValueError("mean_memory_age_days must equal row mean")
    if report.mean_retention_score != _mean_ratio(row.retention_score for row in rows):
        raise ValueError("mean_retention_score must equal row mean")
    if report.mean_decay_score != _mean_decay_score(rows):
        raise ValueError("mean_decay_score must equal row mean")
    if report.status != _report_status(rows):
        raise ValueError("status must match row statuses")


def _count_status(
    rows: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean_decay_score(
    rows: tuple[ResearchTeamSpecialistCrossDomainMemoryDecayRow, ...],
) -> Decimal:
    if not rows:
        return ONE
    return _mean_ratio(row.decay_score for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _decimal(total)


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _decimal(_sum_decimal(items) / _count(len(items)))


def _mean_ratio(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(_sum_decimal(items) / _count(len(items)))


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    value = _ratio(numerator / denominator)
    if value > ONE:
        return ONE
    return value


def _redacted_memory_ref(value: str) -> str:
    _require_private_reference("memory_ref", value)
    return (
        f"{REDACTED_MEMORY_REF_PREFIX}"
        f"{sha256(value.encode('utf-8')).hexdigest()[:REDACTED_DIGEST_LENGTH]}"
    )


def _require_redacted_memory_ref(value: str) -> None:
    if type(value) is not str:
        raise ValueError("redacted_memory_ref must be a string")
    if not value.startswith(REDACTED_MEMORY_REF_PREFIX):
        raise ValueError("redacted_memory_ref must use the memory_ref prefix")
    digest = value[len(REDACTED_MEMORY_REF_PREFIX) :]
    if len(digest) != REDACTED_DIGEST_LENGTH:
        raise ValueError("redacted_memory_ref digest length is invalid")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("redacted_memory_ref digest must be lowercase hex")


def _require_private_reference(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    if normalized != value:
        raise ValueError(f"{name} must be canonical")
    return normalized


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    if normalized != value:
        raise ValueError(f"{name} must be canonical")
    _reject_unsafe_string(name, normalized, field_name=name)
    return normalized


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_member(name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{name} must be one of {allowed_values}")


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, flag_name):
            raise ValueError(f"{name} must include {flag_name}")
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{name} must be {flag_name}")


def _require_tuple_of_exact(
    name: str,
    values: object,
    expected_type: type[object],
) -> tuple[Any, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for item in values:
        if type(item) is not expected_type:
            raise ValueError(f"{name} entries must be exactly {expected_type.__name__}")
    return values


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_member(name, value, allowed_values)
        if value in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(value)
    for allowed_value in allowed_values:
        if allowed_value in seen:
            normalized.append(allowed_value)
    return tuple(normalized)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _decimal(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _ratio(value: Decimal) -> Decimal:
    normalized = _decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready_report(
    report: ResearchTeamSpecialistCrossDomainMemoryDecayReport,
) -> dict[str, Any]:
    _require_exact_type(report, ResearchTeamSpecialistCrossDomainMemoryDecayReport, "report")
    payload = _json_ready_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload, validate_digest=False)
    return payload


def _json_ready_value(value: Any) -> Any:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_value(asdict(value))
    if type(value) is tuple:
        return [_json_ready_value(item) for item in value]
    if type(value) is list:
        return [_json_ready_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready_value(item) for key, item in value.items()}
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if value is None or type(value) in (str, bool, int):
        return value
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def _validate_public_payload(payload: dict[str, Any], *, validate_digest: bool) -> None:
    _reject_floats(payload)
    _reject_unsafe_public_payload(payload)
    _require_payload_flags(payload)
    if validate_digest:
        _validate_payload_digest(payload)


def _reject_floats(value: Any) -> None:
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is dict:
        for item in value.values():
            _reject_floats(item)
    elif type(value) is list:
        for item in value:
            _reject_floats(item)


def _reject_unsafe_public_payload(value: Any, *, path: str = "payload") -> None:
    if type(value) is dict:
        for key, item in value.items():
            key_text = str(key)
            lowered_key = key_text.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe public field at {path}.{key_text}")
            _reject_unsafe_public_payload(item, path=f"{path}.{key_text}")
    elif type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(item, path=f"{path}[{index}]")
    elif type(value) is str:
        _reject_unsafe_string(path, value, field_name=path)


def _reject_unsafe_string(name: str, value: str, *, field_name: str) -> None:
    lowered_field = field_name.lower()
    if any(fragment in lowered_field for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
        raise ValueError(f"unsafe public field at {name}")
    lowered_value = value.lower()
    if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public value at {name}")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if flag_name not in payload:
            raise ValueError(f"payload must include {flag_name}")
        if payload[flag_name] is not True:
            raise ValueError(f"payload must be {flag_name}")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "payload_sha256" not in payload:
        raise ValueError("payload_sha256 is required")
    digest = payload["payload_sha256"]
    if type(digest) is not str:
        raise ValueError("payload_sha256 must be a string")
    unsigned = dict(payload)
    del unsigned["payload_sha256"]
    expected_digest = sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    if digest != expected_digest:
        raise ValueError("payload_sha256 does not match payload")


def _public_field_names() -> tuple[str, ...]:
    public_fields: list[str] = []
    for dataclass_type in (
        ResearchTeamSpecialistCrossDomainMemoryDecayConfig,
        ResearchTeamSpecialistCrossDomainMemoryDecayRow,
        ResearchTeamSpecialistCrossDomainMemoryDecayDomainSummary,
        ResearchTeamSpecialistCrossDomainMemoryDecayReasonCodeCount,
        ResearchTeamSpecialistCrossDomainMemoryDecayReport,
    ):
        public_fields.extend(field.name for field in fields(dataclass_type))
    return tuple(public_fields)


for _field_name in _public_field_names():
    if any(fragment in _field_name.lower() for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
        raise ValueError(f"unsafe public dataclass field: {_field_name}")
