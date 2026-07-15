"""Deterministic learning report for domain-level source disagreements."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_REPORT_CONFIG_VERSION = (
    "research-team-domain-source-disagreement-learning-report-v1"
)
RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES = (
    "pass",
    "watch",
    "block",
)
RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_PRIORITIES = (
    "high",
    "medium",
    "low",
)
RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES = (
    "authority_conflict",
    "factual_conflict",
    "coverage_gap",
    "timing_conflict",
    "interpretation_conflict",
)

_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_THREE = Decimal("3.000000")
_FOUR = Decimal("4.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_HEX_CHARS = frozenset("0123456789abcdef")
_PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
_REPORT_MODE_BY_STATUS = {
    "pass": "paper_source_disagreement_learning_monitor",
    "watch": "paper_source_disagreement_learning_watch",
    "block": "paper_source_disagreement_learning_block",
}
_TYPE_PRIORITY_WEIGHT = {
    "authority_conflict": Decimal("0.900000"),
    "factual_conflict": Decimal("1.000000"),
    "coverage_gap": Decimal("0.800000"),
    "timing_conflict": Decimal("0.700000"),
    "interpretation_conflict": Decimal("0.500000"),
}
_REASON_SEQUENCE = (
    "review_quality_block",
    "repeat_disagreement_block",
    "open_follow_up_block",
    "review_quality_watch",
    "repeat_disagreement_watch",
    "open_follow_up_watch",
    "source_disagreement_learning_pass",
    "learning_priority_high",
    "learning_priority_medium",
    "learning_priority_low",
)
_EMPTY_REASON = (
    "research_team_domain_source_disagreement_learning_report_empty"
)
_UNSAFE_PUBLIC_LABEL_FRAGMENTS = (
    "candidate",
    "market",
    "question",
    "reviewer",
    "person",
    "url",
    "://",
    "token",
    "secret",
    "credential",
    "private",
    "wallet",
    "order",
    "trade",
    "position",
    "recommendation",
)

_REPORT_PAYLOAD_KEY_ORDER = (
    "generated_at",
    "config_version",
    "min_pass_review_quality_score",
    "min_watch_review_quality_score",
    "max_pass_repeat_disagreement_ratio",
    "max_watch_repeat_disagreement_ratio",
    "max_pass_open_follow_up_count",
    "max_watch_open_follow_up_count",
    "high_learning_priority_threshold",
    "medium_learning_priority_threshold",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "high_priority_count",
    "medium_priority_count",
    "low_priority_count",
    "disagreement_type_count",
    "watch_block_ratio",
    "average_review_quality_score",
    "max_learning_priority_score",
    "status",
    "report_mode",
    "reason_codes",
    "disagreement_type_counts",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = frozenset(_REPORT_PAYLOAD_KEY_ORDER)
_ROW_PAYLOAD_KEY_ORDER = (
    "learning_rank",
    "disagreement_fingerprint",
    "team_label",
    "domain_label",
    "disagreement_type",
    "status",
    "learning_priority",
    "review_count",
    "correct_review_count",
    "independent_review_count",
    "learning_capture_count",
    "repeated_disagreement_count",
    "open_follow_up_count",
    "resolution_accuracy_ratio",
    "independent_review_ratio",
    "learning_capture_ratio",
    "repeat_disagreement_ratio",
    "open_follow_up_ratio",
    "review_quality_score",
    "learning_priority_score",
    "observed_at",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = frozenset(_ROW_PAYLOAD_KEY_ORDER)
_TYPE_COUNT_PAYLOAD_KEY_ORDER = (
    "disagreement_type",
    "count",
    "row_ratio",
    "average_review_quality_score",
    "average_learning_priority_score",
    "paper_only",
    "report_only",
    "readonly",
)
TYPE_COUNT_PAYLOAD_KEYS = frozenset(_TYPE_COUNT_PAYLOAD_KEY_ORDER)
_REASON_COUNT_PAYLOAD_KEY_ORDER = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_COUNT_PAYLOAD_KEYS = frozenset(_REASON_COUNT_PAYLOAD_KEY_ORDER)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_PRIORITIES",
    "RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES",
    "RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES",
    "REPORT_PAYLOAD_KEYS",
    "ROW_PAYLOAD_KEYS",
    "TYPE_COUNT_PAYLOAD_KEYS",
    "REASON_COUNT_PAYLOAD_KEYS",
    "ResearchTeamDomainSourceDisagreementLearningConfig",
    "ResearchTeamDomainSourceDisagreementLearningInput",
    "ResearchTeamDomainSourceDisagreementLearningReasonCodeCount",
    "ResearchTeamDomainSourceDisagreementLearningReport",
    "ResearchTeamDomainSourceDisagreementLearningRow",
    "ResearchTeamDomainSourceDisagreementLearningTypeCount",
    "build_research_team_domain_source_disagreement_learning_report",
    "research_team_domain_source_disagreement_learning_report_digest",
    "research_team_domain_source_disagreement_learning_report_payload",
    "validate_research_team_domain_source_disagreement_learning_report_digest",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainSourceDisagreementLearningConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_REPORT_CONFIG_VERSION
    )
    min_pass_review_quality_score: Decimal = Decimal("0.800000")
    min_watch_review_quality_score: Decimal = Decimal("0.600000")
    max_pass_repeat_disagreement_ratio: Decimal = Decimal("0.100000")
    max_watch_repeat_disagreement_ratio: Decimal = Decimal("0.300000")
    max_pass_open_follow_up_count: Decimal = Decimal("0")
    max_watch_open_follow_up_count: Decimal = Decimal("2")
    high_learning_priority_threshold: Decimal = Decimal("0.600000")
    medium_learning_priority_threshold: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceDisagreementLearningConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "min_pass_review_quality_score",
            "min_watch_review_quality_score",
            "max_pass_repeat_disagreement_ratio",
            "max_watch_repeat_disagreement_ratio",
            "high_learning_priority_threshold",
            "medium_learning_priority_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_open_follow_up_count",
            "max_watch_open_follow_up_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.min_pass_review_quality_score < self.min_watch_review_quality_score:
            raise ValueError(
                "min_watch_review_quality_score must not exceed "
                "min_pass_review_quality_score",
            )
        if (
            self.max_pass_repeat_disagreement_ratio
            > self.max_watch_repeat_disagreement_ratio
        ):
            raise ValueError(
                "max_pass_repeat_disagreement_ratio must not exceed "
                "max_watch_repeat_disagreement_ratio",
            )
        if self.max_pass_open_follow_up_count > self.max_watch_open_follow_up_count:
            raise ValueError(
                "max_pass_open_follow_up_count must not exceed "
                "max_watch_open_follow_up_count",
            )
        if (
            self.high_learning_priority_threshold
            < self.medium_learning_priority_threshold
        ):
            raise ValueError(
                "medium_learning_priority_threshold must not exceed "
                "high_learning_priority_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceDisagreementLearningInput(_FinalDataclass):
    disagreement_key: str
    team_label: str
    domain_label: str
    disagreement_type: str
    reviewer_reference: str
    primary_source_reference: str
    conflicting_source_reference: str
    review_count: Decimal
    correct_review_count: Decimal
    independent_review_count: Decimal
    learning_capture_count: Decimal
    repeated_disagreement_count: Decimal
    open_follow_up_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceDisagreementLearningInput, "input")
        _require_private_reference("disagreement_key", self.disagreement_key)
        _require_public_label("team_label", self.team_label)
        _require_public_label("domain_label", self.domain_label)
        _require_member(
            "disagreement_type",
            self.disagreement_type,
            RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES,
        )
        for field_name in (
            "reviewer_reference",
            "primary_source_reference",
            "conflicting_source_reference",
        ):
            _require_private_reference(field_name, getattr(self, field_name))
        if self.primary_source_reference == self.conflicting_source_reference:
            raise ValueError(
                "primary_source_reference and conflicting_source_reference "
                "must be distinct",
            )
        object.__setattr__(
            self,
            "review_count",
            _require_positive_count("review_count", self.review_count),
        )
        for field_name in (
            "correct_review_count",
            "independent_review_count",
            "learning_capture_count",
            "repeated_disagreement_count",
            "open_follow_up_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_count_not_above(
            "correct_review_count",
            self.correct_review_count,
            self.review_count,
        )
        _require_count_not_above(
            "independent_review_count",
            self.independent_review_count,
            self.review_count,
        )
        _require_count_not_above(
            "learning_capture_count",
            self.learning_capture_count,
            self.review_count,
        )
        _require_count_not_above(
            "repeated_disagreement_count",
            self.repeated_disagreement_count,
            self.review_count,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceDisagreementLearningRow(_FinalDataclass):
    learning_rank: Decimal
    disagreement_fingerprint: str
    team_label: str
    domain_label: str
    disagreement_type: str
    status: str
    learning_priority: str
    review_count: Decimal
    correct_review_count: Decimal
    independent_review_count: Decimal
    learning_capture_count: Decimal
    repeated_disagreement_count: Decimal
    open_follow_up_count: Decimal
    resolution_accuracy_ratio: Decimal
    independent_review_ratio: Decimal
    learning_capture_ratio: Decimal
    repeat_disagreement_ratio: Decimal
    open_follow_up_ratio: Decimal
    review_quality_score: Decimal
    learning_priority_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceDisagreementLearningRow, "row")
        object.__setattr__(
            self,
            "learning_rank",
            _require_nonnegative_count("learning_rank", self.learning_rank),
        )
        _require_digest("disagreement_fingerprint", self.disagreement_fingerprint)
        _require_public_label("team_label", self.team_label)
        _require_public_label("domain_label", self.domain_label)
        _require_member(
            "disagreement_type",
            self.disagreement_type,
            RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES,
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES,
        )
        _require_member(
            "learning_priority",
            self.learning_priority,
            RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_PRIORITIES,
        )
        object.__setattr__(
            self,
            "review_count",
            _require_positive_count("review_count", self.review_count),
        )
        for field_name in (
            "correct_review_count",
            "independent_review_count",
            "learning_capture_count",
            "repeated_disagreement_count",
            "open_follow_up_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_count_not_above(
            "correct_review_count",
            self.correct_review_count,
            self.review_count,
        )
        _require_count_not_above(
            "independent_review_count",
            self.independent_review_count,
            self.review_count,
        )
        _require_count_not_above(
            "learning_capture_count",
            self.learning_capture_count,
            self.review_count,
        )
        _require_count_not_above(
            "repeated_disagreement_count",
            self.repeated_disagreement_count,
            self.review_count,
        )
        for field_name in (
            "resolution_accuracy_ratio",
            "independent_review_ratio",
            "learning_capture_ratio",
            "repeat_disagreement_ratio",
            "open_follow_up_ratio",
            "review_quality_score",
            "learning_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_math(self)
        _validate_priority_reason(self)
        _validate_status_reasons(self)
        _apply_or_verify_digest(self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceDisagreementLearningTypeCount(_FinalDataclass):
    disagreement_type: str
    count: Decimal
    row_ratio: Decimal
    average_review_quality_score: Decimal
    average_learning_priority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSourceDisagreementLearningTypeCount,
            "type_count",
        )
        _require_member(
            "disagreement_type",
            self.disagreement_type,
            RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES,
        )
        object.__setattr__(self, "count", _require_positive_count("count", self.count))
        for field_name in (
            "row_ratio",
            "average_review_quality_score",
            "average_learning_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("type_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceDisagreementLearningReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSourceDisagreementLearningReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, _REASON_SEQUENCE)
        object.__setattr__(self, "count", _require_positive_count("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSourceDisagreementLearningReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    min_pass_review_quality_score: Decimal
    min_watch_review_quality_score: Decimal
    max_pass_repeat_disagreement_ratio: Decimal
    max_watch_repeat_disagreement_ratio: Decimal
    max_pass_open_follow_up_count: Decimal
    max_watch_open_follow_up_count: Decimal
    high_learning_priority_threshold: Decimal
    medium_learning_priority_threshold: Decimal
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    disagreement_type_count: Decimal
    watch_block_ratio: Decimal
    average_review_quality_score: Decimal
    max_learning_priority_score: Decimal
    status: str
    report_mode: str
    reason_codes: tuple[str, ...]
    disagreement_type_counts: tuple[
        ResearchTeamDomainSourceDisagreementLearningTypeCount,
        ...,
    ]
    reason_code_counts: tuple[
        ResearchTeamDomainSourceDisagreementLearningReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSourceDisagreementLearningReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "min_pass_review_quality_score",
            "min_watch_review_quality_score",
            "max_pass_repeat_disagreement_ratio",
            "max_watch_repeat_disagreement_ratio",
            "high_learning_priority_threshold",
            "medium_learning_priority_threshold",
            "watch_block_ratio",
            "average_review_quality_score",
            "max_learning_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_open_follow_up_count",
            "max_watch_open_follow_up_count",
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "disagreement_type_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES,
        )
        _require_public_string("report_mode", self.report_mode)
        if self.report_mode != _REPORT_MODE_BY_STATUS[self.status]:
            raise ValueError("report_mode must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "disagreement_type_counts",
            _require_type_counts(self.disagreement_type_counts),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _apply_or_verify_digest(self)


def build_research_team_domain_source_disagreement_learning_report(
    inputs: Iterable[ResearchTeamDomainSourceDisagreementLearningInput],
    *,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSourceDisagreementLearningReport:
    normalized_config = _revalidate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    base_rows = tuple(
        _row_from_input(item, normalized_config)
        for item in normalized_inputs
    )
    rows = _rank_rows(base_rows)
    return _report_from_rows(
        rows,
        config=normalized_config,
        generated_at=generated_at_utc,
    )


def research_team_domain_source_disagreement_learning_report_payload(
    report: ResearchTeamDomainSourceDisagreementLearningReport
    | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSourceDisagreementLearningReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        for row in report.rows:
            _validate_row_math(row)
            _verify_digest(row)
        _verify_digest(report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        _reject_mapping_numeric_types(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a "
            "ResearchTeamDomainSourceDisagreementLearningReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload_shape(payload)
    _verify_public_payload_digests(payload)
    _validate_public_payload_derived_fields(payload)
    return payload


def research_team_domain_source_disagreement_learning_report_digest(
    report: ResearchTeamDomainSourceDisagreementLearningReport
    | Mapping[str, object],
) -> str:
    payload = research_team_domain_source_disagreement_learning_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_team_domain_source_disagreement_learning_report_digest(
    report: ResearchTeamDomainSourceDisagreementLearningReport
    | Mapping[str, object],
) -> bool:
    payload = research_team_domain_source_disagreement_learning_report_payload(report)
    return payload["derived_validation_digest"] == _digest_from_payload(payload)


def _row_from_input(
    item: ResearchTeamDomainSourceDisagreementLearningInput,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> ResearchTeamDomainSourceDisagreementLearningRow:
    return _row_from_public_values(
        learning_rank=_ZERO,
        disagreement_fingerprint=_fingerprint(item.disagreement_key),
        team_label=item.team_label,
        domain_label=item.domain_label,
        disagreement_type=item.disagreement_type,
        review_count=item.review_count,
        correct_review_count=item.correct_review_count,
        independent_review_count=item.independent_review_count,
        learning_capture_count=item.learning_capture_count,
        repeated_disagreement_count=item.repeated_disagreement_count,
        open_follow_up_count=item.open_follow_up_count,
        observed_at=item.observed_at,
        config=config,
    )


def _row_from_public_values(
    *,
    learning_rank: Decimal,
    disagreement_fingerprint: str,
    team_label: str,
    domain_label: str,
    disagreement_type: str,
    review_count: Decimal,
    correct_review_count: Decimal,
    independent_review_count: Decimal,
    learning_capture_count: Decimal,
    repeated_disagreement_count: Decimal,
    open_follow_up_count: Decimal,
    observed_at: datetime,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> ResearchTeamDomainSourceDisagreementLearningRow:
    resolution_accuracy_ratio = _ratio(correct_review_count, review_count)
    independent_review_ratio = _ratio(independent_review_count, review_count)
    learning_capture_ratio = _ratio(learning_capture_count, review_count)
    repeat_disagreement_ratio = _ratio(repeated_disagreement_count, review_count)
    open_follow_up_ratio = _bounded_ratio(open_follow_up_count, review_count)
    review_quality_score = _mean(
        (
            resolution_accuracy_ratio,
            independent_review_ratio,
            learning_capture_ratio,
        ),
    )
    learning_priority_score = _mean(
        (
            _difference(_ONE, review_quality_score),
            repeat_disagreement_ratio,
            open_follow_up_ratio,
            _TYPE_PRIORITY_WEIGHT[disagreement_type],
        ),
    )
    status = _status_for(
        review_quality_score=review_quality_score,
        repeat_disagreement_ratio=repeat_disagreement_ratio,
        open_follow_up_count=open_follow_up_count,
        config=config,
    )
    learning_priority = _learning_priority_for(
        learning_priority_score,
        config=config,
    )
    return ResearchTeamDomainSourceDisagreementLearningRow(
        learning_rank=learning_rank,
        disagreement_fingerprint=disagreement_fingerprint,
        team_label=team_label,
        domain_label=domain_label,
        disagreement_type=disagreement_type,
        status=status,
        learning_priority=learning_priority,
        review_count=review_count,
        correct_review_count=correct_review_count,
        independent_review_count=independent_review_count,
        learning_capture_count=learning_capture_count,
        repeated_disagreement_count=repeated_disagreement_count,
        open_follow_up_count=open_follow_up_count,
        resolution_accuracy_ratio=resolution_accuracy_ratio,
        independent_review_ratio=independent_review_ratio,
        learning_capture_ratio=learning_capture_ratio,
        repeat_disagreement_ratio=repeat_disagreement_ratio,
        open_follow_up_ratio=open_follow_up_ratio,
        review_quality_score=review_quality_score,
        learning_priority_score=learning_priority_score,
        observed_at=observed_at,
        reason_codes=_reason_codes_for(
            review_quality_score=review_quality_score,
            repeat_disagreement_ratio=repeat_disagreement_ratio,
            open_follow_up_count=open_follow_up_count,
            status=status,
            learning_priority=learning_priority,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
) -> tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...]:
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return tuple(
        _copy_row_with_rank(row, _count(index))
        for index, row in enumerate(sorted_rows, start=1)
    )


def _copy_row_with_rank(
    row: ResearchTeamDomainSourceDisagreementLearningRow,
    learning_rank: Decimal,
) -> ResearchTeamDomainSourceDisagreementLearningRow:
    return ResearchTeamDomainSourceDisagreementLearningRow(
        learning_rank=learning_rank,
        disagreement_fingerprint=row.disagreement_fingerprint,
        team_label=row.team_label,
        domain_label=row.domain_label,
        disagreement_type=row.disagreement_type,
        status=row.status,
        learning_priority=row.learning_priority,
        review_count=row.review_count,
        correct_review_count=row.correct_review_count,
        independent_review_count=row.independent_review_count,
        learning_capture_count=row.learning_capture_count,
        repeated_disagreement_count=row.repeated_disagreement_count,
        open_follow_up_count=row.open_follow_up_count,
        resolution_accuracy_ratio=row.resolution_accuracy_ratio,
        independent_review_ratio=row.independent_review_ratio,
        learning_capture_ratio=row.learning_capture_ratio,
        repeat_disagreement_ratio=row.repeat_disagreement_ratio,
        open_follow_up_ratio=row.open_follow_up_ratio,
        review_quality_score=row.review_quality_score,
        learning_priority_score=row.learning_priority_score,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _report_from_rows(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
    *,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSourceDisagreementLearningReport:
    status = _report_status(rows)
    row_count = _count(len(rows))
    watch_block_count = _count(
        sum(1 for row in rows if row.status in ("watch", "block")),
    )
    return ResearchTeamDomainSourceDisagreementLearningReport(
        generated_at=generated_at,
        config_version=config.config_version,
        min_pass_review_quality_score=config.min_pass_review_quality_score,
        min_watch_review_quality_score=config.min_watch_review_quality_score,
        max_pass_repeat_disagreement_ratio=(
            config.max_pass_repeat_disagreement_ratio
        ),
        max_watch_repeat_disagreement_ratio=(
            config.max_watch_repeat_disagreement_ratio
        ),
        max_pass_open_follow_up_count=config.max_pass_open_follow_up_count,
        max_watch_open_follow_up_count=config.max_watch_open_follow_up_count,
        high_learning_priority_threshold=config.high_learning_priority_threshold,
        medium_learning_priority_threshold=config.medium_learning_priority_threshold,
        input_count=row_count,
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        high_priority_count=_priority_count(rows, "high"),
        medium_priority_count=_priority_count(rows, "medium"),
        low_priority_count=_priority_count(rows, "low"),
        disagreement_type_count=_count(len({row.disagreement_type for row in rows})),
        watch_block_ratio=_ratio(watch_block_count, row_count),
        average_review_quality_score=_mean(
            tuple(row.review_quality_score for row in rows),
        ),
        max_learning_priority_score=_max_decimal(
            tuple(row.learning_priority_score for row in rows),
        ),
        status=status,
        report_mode=_REPORT_MODE_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        disagreement_type_counts=_type_counts(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def _status_for(
    *,
    review_quality_score: Decimal,
    repeat_disagreement_ratio: Decimal,
    open_follow_up_count: Decimal,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> str:
    if (
        review_quality_score < config.min_watch_review_quality_score
        or repeat_disagreement_ratio > config.max_watch_repeat_disagreement_ratio
        or open_follow_up_count > config.max_watch_open_follow_up_count
    ):
        return "block"
    if (
        review_quality_score < config.min_pass_review_quality_score
        or repeat_disagreement_ratio > config.max_pass_repeat_disagreement_ratio
        or open_follow_up_count > config.max_pass_open_follow_up_count
    ):
        return "watch"
    return "pass"


def _learning_priority_for(
    score: Decimal,
    *,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> str:
    if score >= config.high_learning_priority_threshold:
        return "high"
    if score >= config.medium_learning_priority_threshold:
        return "medium"
    return "low"


def _reason_codes_for(
    *,
    review_quality_score: Decimal,
    repeat_disagreement_ratio: Decimal,
    open_follow_up_count: Decimal,
    status: str,
    learning_priority: str,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if review_quality_score < config.min_watch_review_quality_score:
        reasons.append("review_quality_block")
    elif review_quality_score < config.min_pass_review_quality_score:
        reasons.append("review_quality_watch")
    if repeat_disagreement_ratio > config.max_watch_repeat_disagreement_ratio:
        reasons.append("repeat_disagreement_block")
    elif repeat_disagreement_ratio > config.max_pass_repeat_disagreement_ratio:
        reasons.append("repeat_disagreement_watch")
    if open_follow_up_count > config.max_watch_open_follow_up_count:
        reasons.append("open_follow_up_block")
    elif open_follow_up_count > config.max_pass_open_follow_up_count:
        reasons.append("open_follow_up_watch")
    if not reasons and status == "pass":
        reasons.append("source_disagreement_learning_pass")
    reasons.append(f"learning_priority_{learning_priority}")
    canonical_reasons = tuple(
        reason for reason in _REASON_SEQUENCE if reason in reasons
    )
    return _require_reason_codes(canonical_reasons, allow_empty=False)


def _row_sort_key(
    row: ResearchTeamDomainSourceDisagreementLearningRow,
) -> tuple[int, int, Decimal, Decimal, datetime, str, str, str, str]:
    return (
        _STATUS_RANK[row.status],
        _PRIORITY_RANK[row.learning_priority],
        row.learning_priority_score.copy_negate(),
        row.review_quality_score,
        row.observed_at,
        row.domain_label,
        row.team_label,
        row.disagreement_type,
        row.disagreement_fingerprint,
    )


def _report_status(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in _REASON_SEQUENCE if reason in present)


def _type_counts(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
) -> tuple[ResearchTeamDomainSourceDisagreementLearningTypeCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    output: list[ResearchTeamDomainSourceDisagreementLearningTypeCount] = []
    for disagreement_type in RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES:
        matching = tuple(
            row for row in rows if row.disagreement_type == disagreement_type
        )
        if not matching:
            continue
        count = _count(len(matching))
        output.append(
            ResearchTeamDomainSourceDisagreementLearningTypeCount(
                disagreement_type=disagreement_type,
                count=count,
                row_ratio=_ratio(count, row_count),
                average_review_quality_score=_mean(
                    tuple(row.review_quality_score for row in matching),
                ),
                average_learning_priority_score=_mean(
                    tuple(row.learning_priority_score for row in matching),
                ),
            ),
        )
    return tuple(output)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
) -> tuple[ResearchTeamDomainSourceDisagreementLearningReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamDomainSourceDisagreementLearningReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            row_ratio=_ratio(_count(counts[reason_code]), row_count),
        )
        for reason_code in _REASON_SEQUENCE
        if reason_code in counts
    )


def _status_count(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _priority_count(
    rows: tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...],
    priority: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.learning_priority == priority))


def _normalize_inputs(
    inputs: Iterable[ResearchTeamDomainSourceDisagreementLearningInput],
) -> tuple[ResearchTeamDomainSourceDisagreementLearningInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    revalidated: list[ResearchTeamDomainSourceDisagreementLearningInput] = []
    for item in normalized:
        revalidated_item = _revalidate_input(item)
        if revalidated_item.disagreement_key in seen_keys:
            raise ValueError("disagreement_key values must be unique")
        seen_keys.add(revalidated_item.disagreement_key)
        revalidated.append(revalidated_item)
    return tuple(revalidated)


def _validate_row_math(
    row: ResearchTeamDomainSourceDisagreementLearningRow,
) -> None:
    expected_values = {
        "resolution_accuracy_ratio": _ratio(
            row.correct_review_count,
            row.review_count,
        ),
        "independent_review_ratio": _ratio(
            row.independent_review_count,
            row.review_count,
        ),
        "learning_capture_ratio": _ratio(
            row.learning_capture_count,
            row.review_count,
        ),
        "repeat_disagreement_ratio": _ratio(
            row.repeated_disagreement_count,
            row.review_count,
        ),
        "open_follow_up_ratio": _bounded_ratio(
            row.open_follow_up_count,
            row.review_count,
        ),
    }
    for field_name, expected in expected_values.items():
        if getattr(row, field_name) != expected:
            raise ValueError(f"{field_name} must match source counts")
    expected_quality = _mean(
        (
            expected_values["resolution_accuracy_ratio"],
            expected_values["independent_review_ratio"],
            expected_values["learning_capture_ratio"],
        ),
    )
    if row.review_quality_score != expected_quality:
        raise ValueError("review_quality_score must match derived fields")
    expected_priority = _mean(
        (
            _difference(_ONE, expected_quality),
            expected_values["repeat_disagreement_ratio"],
            expected_values["open_follow_up_ratio"],
            _TYPE_PRIORITY_WEIGHT[row.disagreement_type],
        ),
    )
    if row.learning_priority_score != expected_priority:
        raise ValueError("learning_priority_score must match derived fields")


def _validate_priority_reason(
    row: ResearchTeamDomainSourceDisagreementLearningRow,
) -> None:
    expected = f"learning_priority_{row.learning_priority}"
    priority_reasons = tuple(
        reason for reason in row.reason_codes if reason.startswith("learning_priority_")
    )
    if priority_reasons != (expected,):
        raise ValueError("reason_codes must match learning_priority")


def _validate_status_reasons(
    row: ResearchTeamDomainSourceDisagreementLearningRow,
) -> None:
    block_reasons = {
        "review_quality_block",
        "repeat_disagreement_block",
        "open_follow_up_block",
    }
    watch_reasons = {
        "review_quality_watch",
        "repeat_disagreement_watch",
        "open_follow_up_watch",
    }
    has_block = any(reason in block_reasons for reason in row.reason_codes)
    has_watch = any(reason in watch_reasons for reason in row.reason_codes)
    has_pass = "source_disagreement_learning_pass" in row.reason_codes
    reason_set = set(row.reason_codes)
    has_metric_conflict = any(
        {f"{metric}_block", f"{metric}_watch"} <= reason_set
        for metric in (
            "review_quality",
            "repeat_disagreement",
            "open_follow_up",
        )
    )
    if has_metric_conflict:
        raise ValueError("reason_codes must match status")
    valid = (
        (row.status == "block" and has_block and not has_pass)
        or (
            row.status == "watch"
            and has_watch
            and not has_block
            and not has_pass
        )
        or (
            row.status == "pass"
            and has_pass
            and not has_block
            and not has_watch
        )
    )
    if not valid:
        raise ValueError("reason_codes must match status")


def _validate_row_against_config(
    row: ResearchTeamDomainSourceDisagreementLearningRow,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> None:
    _validate_row_math(row)
    expected_status = _status_for(
        review_quality_score=row.review_quality_score,
        repeat_disagreement_ratio=row.repeat_disagreement_ratio,
        open_follow_up_count=row.open_follow_up_count,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match derived fields")
    expected_priority = _learning_priority_for(
        row.learning_priority_score,
        config=config,
    )
    if row.learning_priority != expected_priority:
        raise ValueError("learning_priority must match derived fields")
    expected_reasons = _reason_codes_for(
        review_quality_score=row.review_quality_score,
        repeat_disagreement_ratio=row.repeat_disagreement_ratio,
        open_follow_up_count=row.open_follow_up_count,
        status=row.status,
        learning_priority=row.learning_priority,
        config=config,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match derived fields")


def _validate_report(
    report: ResearchTeamDomainSourceDisagreementLearningReport,
) -> None:
    config = _config_from_report(report)
    rows = report.rows
    expected_order = tuple(sorted(rows, key=_row_sort_key))
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if rows != expected_order or tuple(row.learning_rank for row in rows) != expected_ranks:
        raise ValueError("rows must be sorted deterministically")
    seen_fingerprints: set[str] = set()
    for row in rows:
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if row.disagreement_fingerprint in seen_fingerprints:
            raise ValueError("disagreement_fingerprint values must be unique")
        seen_fingerprints.add(row.disagreement_fingerprint)
        _validate_row_against_config(row, config)
        _verify_digest(row)
    expected_counts = {
        "input_count": _count(len(rows)),
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "high_priority_count": _priority_count(rows, "high"),
        "medium_priority_count": _priority_count(rows, "medium"),
        "low_priority_count": _priority_count(rows, "low"),
        "disagreement_type_count": _count(
            len({row.disagreement_type for row in rows}),
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    watch_block_count = _count(
        sum(1 for row in rows if row.status in ("watch", "block")),
    )
    if report.watch_block_ratio != _ratio(watch_block_count, _count(len(rows))):
        raise ValueError("watch_block_ratio must match rows")
    if report.average_review_quality_score != _mean(
        tuple(row.review_quality_score for row in rows),
    ):
        raise ValueError("average_review_quality_score must match rows")
    if report.max_learning_priority_score != _max_decimal(
        tuple(row.learning_priority_score for row in rows),
    ):
        raise ValueError("max_learning_priority_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.report_mode != _REPORT_MODE_BY_STATUS[report.status]:
        raise ValueError("report_mode must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.disagreement_type_counts != _type_counts(rows):
        raise ValueError("disagreement_type_counts must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _config_from_report(
    report: ResearchTeamDomainSourceDisagreementLearningReport,
) -> ResearchTeamDomainSourceDisagreementLearningConfig:
    return ResearchTeamDomainSourceDisagreementLearningConfig(
        config_version=report.config_version,
        min_pass_review_quality_score=report.min_pass_review_quality_score,
        min_watch_review_quality_score=report.min_watch_review_quality_score,
        max_pass_repeat_disagreement_ratio=(
            report.max_pass_repeat_disagreement_ratio
        ),
        max_watch_repeat_disagreement_ratio=(
            report.max_watch_repeat_disagreement_ratio
        ),
        max_pass_open_follow_up_count=report.max_pass_open_follow_up_count,
        max_watch_open_follow_up_count=report.max_watch_open_follow_up_count,
        high_learning_priority_threshold=report.high_learning_priority_threshold,
        medium_learning_priority_threshold=report.medium_learning_priority_threshold,
    )


def _revalidate_config(
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> ResearchTeamDomainSourceDisagreementLearningConfig:
    _require_exact_type(
        config,
        ResearchTeamDomainSourceDisagreementLearningConfig,
        "config",
    )
    return ResearchTeamDomainSourceDisagreementLearningConfig(
        config_version=config.config_version,
        min_pass_review_quality_score=config.min_pass_review_quality_score,
        min_watch_review_quality_score=config.min_watch_review_quality_score,
        max_pass_repeat_disagreement_ratio=(
            config.max_pass_repeat_disagreement_ratio
        ),
        max_watch_repeat_disagreement_ratio=(
            config.max_watch_repeat_disagreement_ratio
        ),
        max_pass_open_follow_up_count=config.max_pass_open_follow_up_count,
        max_watch_open_follow_up_count=config.max_watch_open_follow_up_count,
        high_learning_priority_threshold=config.high_learning_priority_threshold,
        medium_learning_priority_threshold=config.medium_learning_priority_threshold,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def _revalidate_input(
    item: ResearchTeamDomainSourceDisagreementLearningInput,
) -> ResearchTeamDomainSourceDisagreementLearningInput:
    _require_exact_type(
        item,
        ResearchTeamDomainSourceDisagreementLearningInput,
        "input",
    )
    return ResearchTeamDomainSourceDisagreementLearningInput(
        disagreement_key=item.disagreement_key,
        team_label=item.team_label,
        domain_label=item.domain_label,
        disagreement_type=item.disagreement_type,
        reviewer_reference=item.reviewer_reference,
        primary_source_reference=item.primary_source_reference,
        conflicting_source_reference=item.conflicting_source_reference,
        review_count=item.review_count,
        correct_review_count=item.correct_review_count,
        independent_review_count=item.independent_review_count,
        learning_capture_count=item.learning_capture_count,
        repeated_disagreement_count=item.repeated_disagreement_count,
        open_follow_up_count=item.open_follow_up_count,
        observed_at=item.observed_at,
        paper_only=item.paper_only,
        report_only=item.report_only,
        readonly=item.readonly,
    )


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_config_version(value: object) -> None:
    _require_public_string("config_version", value)
    if (
        value
        != DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")


def _require_public_label(name: str, value: object) -> None:
    _require_public_string(name, value)
    assert type(value) is str
    if _PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a public aggregate label")
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
        raise ValueError(f"{name} must be a public aggregate label")


def _require_private_reference(name: str, value: object) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{name} must be a non-empty canonical string")
    if len(value) > 2048 or any(ord(character) < 32 for character in value):
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_member(name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be a supported value")


def _require_decimal(name: str, value: object, *, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    try:
        with localcontext(_DECIMAL_CONTEXT):
            normalized = value.quantize(quantum)
    except DecimalException as exc:
        raise ValueError(f"{name} exceeds the fixed Decimal context") from exc
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return normalized


def _require_nonnegative_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be an integer Decimal")
    normalized = _require_decimal(name, value, quantum=_COUNT_QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_count(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    normalized = _require_decimal(name, value, quantum=_QUANTUM)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_count_not_above(
    name: str,
    value: Decimal,
    upper_bound: Decimal,
) -> None:
    if value > upper_bound:
        raise ValueError(f"{name} must not exceed review_count")


def _count(value: int) -> Decimal:
    return _require_nonnegative_count("count", Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_count("numerator", numerator)
    denominator = _require_nonnegative_count("denominator", denominator)
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _require_ratio_decimal("ratio", numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_count("numerator", numerator)
    denominator = _require_positive_count("denominator", denominator)
    with localcontext(_DECIMAL_CONTEXT):
        value = numerator / denominator
    if value >= _ONE:
        return _ONE
    return _require_ratio_decimal("bounded_ratio", value)


def _difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _require_ratio_decimal("difference", left - right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in values:
            total += _require_ratio_decimal("mean_value", value)
        divisor = Decimal(len(values))
        return _require_ratio_decimal("mean", total / divisor)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in _HEX_CHARS for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _fingerprint(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    for reason in normalized:
        _require_member("reason_code", reason, _REASON_SEQUENCE)
    expected = tuple(reason for reason in _REASON_SEQUENCE if reason in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must use canonical order")
    return normalized


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)) and tuple(value) == (_EMPTY_REASON,):
        return (_EMPTY_REASON,)
    return _require_reason_codes(value, allow_empty=False)


def _require_type_counts(
    value: object,
) -> tuple[ResearchTeamDomainSourceDisagreementLearningTypeCount, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("disagreement_type_counts must be a list or tuple")
    normalized = tuple(value)
    seen: set[str] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchTeamDomainSourceDisagreementLearningTypeCount,
            "type_count",
        )
        if item.disagreement_type in seen:
            raise ValueError("disagreement_type_counts must be unique")
        seen.add(item.disagreement_type)
    return normalized


def _require_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainSourceDisagreementLearningReasonCodeCount, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(value)
    seen: set[str] = set()
    for item in normalized:
        _require_exact_type(
            item,
            ResearchTeamDomainSourceDisagreementLearningReasonCodeCount,
            "reason_code_count",
        )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    return normalized


def _require_rows(
    value: object,
) -> tuple[ResearchTeamDomainSourceDisagreementLearningRow, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(value)
    for row in normalized:
        _require_exact_type(
            row,
            ResearchTeamDomainSourceDisagreementLearningRow,
            "row",
        )
    return normalized


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _apply_or_verify_digest(value: object) -> None:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    expected = _digest_from_payload(payload)
    current = payload.get("derived_validation_digest")
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    if current != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _verify_digest(value: object) -> None:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    if payload.get("derived_validation_digest") != _digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match payload")


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("JSON Decimal value must not use signed zero")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON numeric values must use Decimal-derived strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_mapping_numeric_types(value: object) -> None:
    if type(value) is bool or type(value) is str or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(
            "public payload numeric values must use Decimal-derived strings",
        )
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_mapping_numeric_types(item)
        return
    if type(value) is list:
        for item in value:
            _reject_mapping_numeric_types(item)
        return
    raise ValueError("public payload contains an unsupported value")


def _validate_public_payload_shape(payload: dict[str, object]) -> None:
    _require_exact_schema(payload, _REPORT_PAYLOAD_KEY_ORDER, "report")
    _require_payload_hard_flags(payload, "report payload")
    _require_config_version(payload["config_version"])
    _parse_datetime_string("generated_at", payload["generated_at"])
    for field_name in (
        "min_pass_review_quality_score",
        "min_watch_review_quality_score",
        "max_pass_repeat_disagreement_ratio",
        "max_watch_repeat_disagreement_ratio",
        "high_learning_priority_threshold",
        "medium_learning_priority_threshold",
        "watch_block_ratio",
        "average_review_quality_score",
        "max_learning_priority_score",
    ):
        _parse_ratio_string(field_name, payload[field_name])
    for field_name in (
        "max_pass_open_follow_up_count",
        "max_watch_open_follow_up_count",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "disagreement_type_count",
    ):
        _parse_count_string(field_name, payload[field_name], positive=False)
    _require_member(
        "status",
        payload["status"],
        RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES,
    )
    _require_public_string("report_mode", payload["report_mode"])
    _require_public_digest(payload["derived_validation_digest"])
    _validate_payload_reason_codes(payload["reason_codes"], report_level=True)
    for item in _require_payload_list(
        "disagreement_type_counts",
        payload["disagreement_type_counts"],
    ):
        _validate_public_type_count(item)
    for item in _require_payload_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    ):
        _validate_public_reason_count(item)
    for row in _require_payload_list("rows", payload["rows"]):
        _validate_public_row(row)


def _validate_public_row(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_exact_schema(value, _ROW_PAYLOAD_KEY_ORDER, "row")
    _require_payload_hard_flags(value, "row payload")
    _parse_count_string("learning_rank", value["learning_rank"], positive=False)
    _require_public_digest(value["disagreement_fingerprint"])
    _require_public_label("team_label", value["team_label"])
    _require_public_label("domain_label", value["domain_label"])
    _require_member(
        "disagreement_type",
        value["disagreement_type"],
        RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES,
    )
    _require_member(
        "status",
        value["status"],
        RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES,
    )
    _require_member(
        "learning_priority",
        value["learning_priority"],
        RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_PRIORITIES,
    )
    _parse_count_string("review_count", value["review_count"], positive=True)
    for field_name in (
        "correct_review_count",
        "independent_review_count",
        "learning_capture_count",
        "repeated_disagreement_count",
        "open_follow_up_count",
    ):
        _parse_count_string(field_name, value[field_name], positive=False)
    for field_name in (
        "resolution_accuracy_ratio",
        "independent_review_ratio",
        "learning_capture_ratio",
        "repeat_disagreement_ratio",
        "open_follow_up_ratio",
        "review_quality_score",
        "learning_priority_score",
    ):
        _parse_ratio_string(field_name, value[field_name])
    _parse_datetime_string("observed_at", value["observed_at"])
    _validate_payload_reason_codes(value["reason_codes"], report_level=False)
    _require_public_digest(value["derived_validation_digest"])


def _validate_public_type_count(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("disagreement_type_counts must contain JSON objects")
    _require_exact_schema(value, _TYPE_COUNT_PAYLOAD_KEY_ORDER, "type_count")
    _require_payload_hard_flags(value, "type_count payload")
    _require_member(
        "disagreement_type",
        value["disagreement_type"],
        RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES,
    )
    _parse_count_string("count", value["count"], positive=True)
    for field_name in (
        "row_ratio",
        "average_review_quality_score",
        "average_learning_priority_score",
    ):
        _parse_ratio_string(field_name, value[field_name])


def _validate_public_reason_count(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_exact_schema(value, _REASON_COUNT_PAYLOAD_KEY_ORDER, "reason_code_count")
    _require_payload_hard_flags(value, "reason_code_count payload")
    _require_member("reason_code", value["reason_code"], _REASON_SEQUENCE)
    _parse_count_string("count", value["count"], positive=True)
    _parse_ratio_string("row_ratio", value["row_ratio"])


def _require_exact_schema(
    payload: Mapping[str, object],
    expected_key_order: tuple[str, ...],
    label: str,
) -> None:
    if tuple(payload) != expected_key_order:
        raise ValueError(f"{label} public payload must use exact schema")


def _require_payload_hard_flags(
    payload: Mapping[str, object],
    label: str,
) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_list(name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return value


def _parse_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} numeric values must use Decimal-derived strings")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(
            f"{name} numeric values must use Decimal-derived strings",
        ) from exc
    return parsed


def _parse_count_string(
    name: str,
    value: object,
    *,
    positive: bool,
) -> Decimal:
    parsed = _parse_decimal_string(name, value)
    if positive:
        return _require_positive_count(name, parsed)
    return _require_nonnegative_count(name, parsed)


def _parse_ratio_string(name: str, value: object) -> Decimal:
    return _require_ratio_decimal(name, _parse_decimal_string(name, value))


def _parse_datetime_string(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return parsed.astimezone(UTC)


def _require_public_digest(value: object) -> None:
    _require_digest("derived_validation_digest", value)


def _validate_payload_reason_codes(
    value: object,
    *,
    report_level: bool,
) -> None:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    if report_level and tuple(value) == (_EMPTY_REASON,):
        return
    _require_reason_codes(value, allow_empty=False)


def _verify_public_payload_digests(payload: dict[str, object]) -> None:
    rows = _require_payload_list("rows", payload["rows"])
    for row in rows:
        assert type(row) is dict
        if row["derived_validation_digest"] != _digest_from_payload(row):
            raise ValueError(
                "derived_validation_digest does not match row payload",
            )
    if payload["derived_validation_digest"] != _digest_from_payload(payload):
        raise ValueError(
            "derived_validation_digest does not match report payload",
        )


def _validate_public_payload_derived_fields(
    payload: dict[str, object],
) -> None:
    config = ResearchTeamDomainSourceDisagreementLearningConfig(
        config_version=str(payload["config_version"]),
        min_pass_review_quality_score=_parse_ratio_string(
            "min_pass_review_quality_score",
            payload["min_pass_review_quality_score"],
        ),
        min_watch_review_quality_score=_parse_ratio_string(
            "min_watch_review_quality_score",
            payload["min_watch_review_quality_score"],
        ),
        max_pass_repeat_disagreement_ratio=_parse_ratio_string(
            "max_pass_repeat_disagreement_ratio",
            payload["max_pass_repeat_disagreement_ratio"],
        ),
        max_watch_repeat_disagreement_ratio=_parse_ratio_string(
            "max_watch_repeat_disagreement_ratio",
            payload["max_watch_repeat_disagreement_ratio"],
        ),
        max_pass_open_follow_up_count=_parse_count_string(
            "max_pass_open_follow_up_count",
            payload["max_pass_open_follow_up_count"],
            positive=False,
        ),
        max_watch_open_follow_up_count=_parse_count_string(
            "max_watch_open_follow_up_count",
            payload["max_watch_open_follow_up_count"],
            positive=False,
        ),
        high_learning_priority_threshold=_parse_ratio_string(
            "high_learning_priority_threshold",
            payload["high_learning_priority_threshold"],
        ),
        medium_learning_priority_threshold=_parse_ratio_string(
            "medium_learning_priority_threshold",
            payload["medium_learning_priority_threshold"],
        ),
    )
    base_rows = tuple(
        _row_from_public_payload(row, config=config)
        for row in _require_payload_list("rows", payload["rows"])
    )
    rebuilt = _report_from_rows(
        _rank_rows(base_rows),
        config=config,
        generated_at=_parse_datetime_string("generated_at", payload["generated_at"]),
    )
    expected = _json_ready(asdict(rebuilt))
    if type(expected) is not dict:
        raise ValueError("canonical report payload must be a JSON object")
    mismatch = _first_mismatch_path(payload, expected)
    if mismatch is not None:
        raise ValueError(f"{mismatch} derived fields do not match canonical report")


def _row_from_public_payload(
    value: object,
    *,
    config: ResearchTeamDomainSourceDisagreementLearningConfig,
) -> ResearchTeamDomainSourceDisagreementLearningRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    return _row_from_public_values(
        learning_rank=_ZERO,
        disagreement_fingerprint=str(value["disagreement_fingerprint"]),
        team_label=str(value["team_label"]),
        domain_label=str(value["domain_label"]),
        disagreement_type=str(value["disagreement_type"]),
        review_count=_parse_count_string(
            "review_count",
            value["review_count"],
            positive=True,
        ),
        correct_review_count=_parse_count_string(
            "correct_review_count",
            value["correct_review_count"],
            positive=False,
        ),
        independent_review_count=_parse_count_string(
            "independent_review_count",
            value["independent_review_count"],
            positive=False,
        ),
        learning_capture_count=_parse_count_string(
            "learning_capture_count",
            value["learning_capture_count"],
            positive=False,
        ),
        repeated_disagreement_count=_parse_count_string(
            "repeated_disagreement_count",
            value["repeated_disagreement_count"],
            positive=False,
        ),
        open_follow_up_count=_parse_count_string(
            "open_follow_up_count",
            value["open_follow_up_count"],
            positive=False,
        ),
        observed_at=_parse_datetime_string("observed_at", value["observed_at"]),
        config=config,
    )


def _first_mismatch_path(
    actual: object,
    expected: object,
    path: str = "payload",
) -> str | None:
    if type(actual) is not type(expected):
        return path
    if isinstance(actual, dict) and isinstance(expected, dict):
        for key in expected:
            mismatch = _first_mismatch_path(
                actual.get(key),
                expected[key],
                f"{path}.{key}",
            )
            if mismatch is not None:
                return mismatch
        return None
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return path
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            mismatch = _first_mismatch_path(
                actual_item,
                expected_item,
                f"{path}[{index}]",
            )
            if mismatch is not None:
                return mismatch
        return None
    if actual != expected:
        return path
    return None
