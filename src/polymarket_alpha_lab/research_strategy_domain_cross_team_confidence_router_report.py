"""Report-only reducer for domain cross-team confidence routing."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_STATUSES",
    "ResearchStrategyDomainCrossTeamConfidenceRouterConfig",
    "ResearchStrategyDomainCrossTeamConfidenceRouterInput",
    "ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount",
    "ResearchStrategyDomainCrossTeamConfidenceRouterReport",
    "ResearchStrategyDomainCrossTeamConfidenceRouterRow",
    "build_research_strategy_domain_cross_team_confidence_router_report",
    "research_strategy_domain_cross_team_confidence_router_report_payload",
    "validate_research_strategy_domain_cross_team_confidence_router_public_payload",
)


DEFAULT_RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-cross-team-confidence-router-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}
HEX_CHARS = frozenset("0123456789abcdef")
HUMAN_REVIEW_ROUTES = (
    "no_review",
    "standard_review",
    "priority_review",
)
PRIVATE_IDENTIFIER_TOKENS = frozenset(
    {
        "confidential",
        "internal",
        "private",
        "proprietary",
        "source",
    },
)
CONFIG_DECIMAL_FIELDS = (
    "local_confidence_weight",
    "cross_team_agreement_weight",
    "evidence_support_weight",
    "handoff_completeness_weight",
    "conflict_reserve_weight",
    "pass_threshold",
    "watch_threshold",
    "min_pass_local_confidence_score",
    "min_watch_local_confidence_score",
    "min_pass_cross_team_agreement_score",
    "min_watch_cross_team_agreement_score",
    "min_pass_evidence_support_score",
    "min_watch_evidence_support_score",
    "min_pass_handoff_completeness_score",
    "min_watch_handoff_completeness_score",
    "max_pass_conflict_pressure_score",
    "max_watch_conflict_pressure_score",
)
ROW_PAYLOAD_FIELDS = (
    "rank",
    "domain_key",
    "team_key",
    "assessment_digest",
    "status",
    "human_review_required",
    "human_review_route",
    "observed_at",
    "assessment_age_seconds",
    "local_confidence_score",
    "cross_team_agreement_score",
    "evidence_support_score",
    "handoff_completeness_score",
    "conflict_pressure_score",
    "router_confidence_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    *CONFIG_DECIMAL_FIELDS,
    "signal_count",
    "domain_count",
    "team_count",
    "pass_count",
    "watch_count",
    "block_count",
    "human_review_required_count",
    "priority_review_count",
    "standard_review_count",
    "average_router_confidence_score",
    "average_conflict_pressure_score",
    "highest_conflict_pressure_score",
    "oldest_assessment_age_seconds",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "public_payload_sha256",
    "paper_only",
    "report_only",
    "readonly",
)

EMPTY_REPORT_REASON_CODE = "empty_domain_cross_team_confidence_router_inputs"
REPORT_PASS_REASON_CODE = "domain_cross_team_confidence_router_report_pass"
REPORT_WATCH_REASON_CODE = "domain_cross_team_confidence_router_report_watch"
REPORT_BLOCK_REASON_CODE = "domain_cross_team_confidence_router_report_block"
ROW_PASS_REASON_CODE = "router_confidence_score_pass"
ROW_REASON_CODES = (
    "router_confidence_score_block",
    "router_confidence_score_watch",
    ROW_PASS_REASON_CODE,
    "local_confidence_score_block",
    "local_confidence_score_watch",
    "cross_team_agreement_score_block",
    "cross_team_agreement_score_watch",
    "evidence_support_score_block",
    "evidence_support_score_watch",
    "handoff_completeness_score_block",
    "handoff_completeness_score_watch",
    "conflict_pressure_score_block",
    "conflict_pressure_score_watch",
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
    *ROW_REASON_CODES,
    EMPTY_REPORT_REASON_CODE,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


RESTRICTED_KEY_FRAGMENTS = (
    _join_parts("raw", "_candidate", "_id"),
    _join_parts("candidate", "_id"),
    _join_parts("candidate", "_sl", "ug"),
    _join_parts("market", "_id"),
    _join_parts("market", "_sl", "ug"),
    _join_parts("market", "_ques", "tion"),
    _join_parts("source", "_u", "rl"),
    _join_parts("source", "_te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("table", "_name"),
    _join_parts("private", "_tok", "en"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("li", "ve"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("exec", "ute"),
    _join_parts("exec", "ution"),
    _join_parts("pos", "ition", "_size"),
    _join_parts("si", "zing"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
    _join_parts("reco", "mmend"),
    _join_parts("re", "quests"),
    _join_parts("ht", "tp"),
    _join_parts("so", "cket"),
    _join_parts("sub", "process"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
)
RESTRICTED_VALUE_FRAGMENTS = (
    *RESTRICTED_KEY_FRAGMENTS,
    "://",
    _join_parts("d", "sn", "="),
    _join_parts("tok", "en", "="),
)


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCrossTeamConfidenceRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_REPORT_CONFIG_VERSION
    )
    local_confidence_weight: Decimal = Decimal("0.250000")
    cross_team_agreement_weight: Decimal = Decimal("0.300000")
    evidence_support_weight: Decimal = Decimal("0.200000")
    handoff_completeness_weight: Decimal = Decimal("0.150000")
    conflict_reserve_weight: Decimal = Decimal("0.100000")
    pass_threshold: Decimal = Decimal("0.750000")
    watch_threshold: Decimal = Decimal("0.550000")
    min_pass_local_confidence_score: Decimal = Decimal("0.750000")
    min_watch_local_confidence_score: Decimal = Decimal("0.500000")
    min_pass_cross_team_agreement_score: Decimal = Decimal("0.750000")
    min_watch_cross_team_agreement_score: Decimal = Decimal("0.500000")
    min_pass_evidence_support_score: Decimal = Decimal("0.700000")
    min_watch_evidence_support_score: Decimal = Decimal("0.500000")
    min_pass_handoff_completeness_score: Decimal = Decimal("0.750000")
    min_watch_handoff_completeness_score: Decimal = Decimal("0.500000")
    max_pass_conflict_pressure_score: Decimal = Decimal("0.250000")
    max_watch_conflict_pressure_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "local_confidence_weight",
            "cross_team_agreement_weight",
            "evidence_support_weight",
            "handoff_completeness_weight",
            "conflict_reserve_weight",
            "pass_threshold",
            "watch_threshold",
            "min_pass_local_confidence_score",
            "min_watch_local_confidence_score",
            "min_pass_cross_team_agreement_score",
            "min_watch_cross_team_agreement_score",
            "min_pass_evidence_support_score",
            "min_watch_evidence_support_score",
            "min_pass_handoff_completeness_score",
            "min_watch_handoff_completeness_score",
            "max_pass_conflict_pressure_score",
            "max_watch_conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than("watch_threshold", self.watch_threshold, self.pass_threshold)
        _require_less_than(
            "min_watch_local_confidence_score",
            self.min_watch_local_confidence_score,
            self.min_pass_local_confidence_score,
        )
        _require_less_than(
            "min_watch_cross_team_agreement_score",
            self.min_watch_cross_team_agreement_score,
            self.min_pass_cross_team_agreement_score,
        )
        _require_less_than(
            "min_watch_evidence_support_score",
            self.min_watch_evidence_support_score,
            self.min_pass_evidence_support_score,
        )
        _require_less_than(
            "min_watch_handoff_completeness_score",
            self.min_watch_handoff_completeness_score,
            self.min_pass_handoff_completeness_score,
        )
        _require_less_than(
            "max_pass_conflict_pressure_score",
            self.max_pass_conflict_pressure_score,
            self.max_watch_conflict_pressure_score,
        )
        _require_weight_total(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCrossTeamConfidenceRouterInput(_FinalPublicDataclass):
    domain_key: str
    team_key: str
    assessment_label: str
    observed_at: datetime
    local_confidence_score: Decimal
    cross_team_agreement_score: Decimal
    evidence_support_score: Decimal
    handoff_completeness_score: Decimal
    conflict_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCrossTeamConfidenceRouterInput,
            "input",
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_label("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_safe_label("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "assessment_label",
            _require_assessment_label("assessment_label", self.assessment_label),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "local_confidence_score",
            "cross_team_agreement_score",
            "evidence_support_score",
            "handoff_completeness_score",
            "conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCrossTeamConfidenceRouterRow(_FinalPublicDataclass):
    rank: Decimal
    domain_key: str
    team_key: str
    assessment_digest: str
    status: str
    human_review_required: bool
    human_review_route: str
    observed_at: datetime
    assessment_age_seconds: Decimal
    local_confidence_score: Decimal
    cross_team_agreement_score: Decimal
    evidence_support_score: Decimal
    handoff_completeness_score: Decimal
    conflict_pressure_score: Decimal
    router_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCrossTeamConfidenceRouterRow,
            "row",
        )
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_label("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_safe_label("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "assessment_digest",
            _normalize_sha256("assessment_digest", self.assessment_digest),
        )
        _require_status("status", self.status)
        _require_bool("human_review_required", self.human_review_required)
        _require_member(
            "human_review_route",
            self.human_review_route,
            HUMAN_REVIEW_ROUTES,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "assessment_age_seconds",
            _normalize_nonnegative_decimal(
                "assessment_age_seconds",
                self.assessment_age_seconds,
            ),
        )
        for field_name in (
            "local_confidence_score",
            "cross_team_agreement_score",
            "evidence_support_score",
            "handoff_completeness_score",
            "conflict_pressure_score",
            "router_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainCrossTeamConfidenceRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    local_confidence_weight: Decimal
    cross_team_agreement_weight: Decimal
    evidence_support_weight: Decimal
    handoff_completeness_weight: Decimal
    conflict_reserve_weight: Decimal
    pass_threshold: Decimal
    watch_threshold: Decimal
    min_pass_local_confidence_score: Decimal
    min_watch_local_confidence_score: Decimal
    min_pass_cross_team_agreement_score: Decimal
    min_watch_cross_team_agreement_score: Decimal
    min_pass_evidence_support_score: Decimal
    min_watch_evidence_support_score: Decimal
    min_pass_handoff_completeness_score: Decimal
    min_watch_handoff_completeness_score: Decimal
    max_pass_conflict_pressure_score: Decimal
    max_watch_conflict_pressure_score: Decimal
    signal_count: Decimal
    domain_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    human_review_required_count: Decimal
    priority_review_count: Decimal
    standard_review_count: Decimal
    average_router_confidence_score: Decimal
    average_conflict_pressure_score: Decimal
    highest_conflict_pressure_score: Decimal
    oldest_assessment_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...]
    public_payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainCrossTeamConfidenceRouterReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in CONFIG_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_count",
            "domain_count",
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "human_review_required_count",
            "priority_review_count",
            "standard_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_router_confidence_score",
            "average_conflict_pressure_score",
            "highest_conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_assessment_age_seconds",
            _normalize_nonnegative_decimal(
                "oldest_assessment_age_seconds",
                self.oldest_assessment_age_seconds,
            ),
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
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_sha256 = _report_public_payload_sha256(self)
        if self.public_payload_sha256:
            object.__setattr__(
                self,
                "public_payload_sha256",
                _normalize_sha256("public_payload_sha256", self.public_payload_sha256),
            )
            if self.public_payload_sha256 != expected_sha256:
                raise ValueError("public_payload_sha256 must match report fields")
        else:
            object.__setattr__(self, "public_payload_sha256", expected_sha256)


@dataclass(frozen=True, slots=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


@dataclass(frozen=True, slots=True)
class _RowValues:
    domain_key: str
    team_key: str
    assessment_digest: str
    status: str
    human_review_required: bool
    human_review_route: str
    observed_at: datetime
    assessment_age_seconds: Decimal
    local_confidence_score: Decimal
    cross_team_agreement_score: Decimal
    evidence_support_score: Decimal
    handoff_completeness_score: Decimal
    conflict_pressure_score: Decimal
    router_confidence_score: Decimal
    reason_codes: tuple[str, ...]


def build_research_strategy_domain_cross_team_confidence_router_report(
    signals: Iterable[ResearchStrategyDomainCrossTeamConfidenceRouterInput],
    *,
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterReport:
    if type(config) is not ResearchStrategyDomainCrossTeamConfidenceRouterConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainCrossTeamConfidenceRouterConfig",
        )
    config = _revalidate_config(config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(signals, generated_at=generated_at_utc)
    row_values = sorted(
        (
            _row_values_for_input(
                value,
                config=config,
                generated_at=generated_at_utc,
            )
            for value in inputs
        ),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    return ResearchStrategyDomainCrossTeamConfidenceRouterReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        local_confidence_weight=config.local_confidence_weight,
        cross_team_agreement_weight=config.cross_team_agreement_weight,
        evidence_support_weight=config.evidence_support_weight,
        handoff_completeness_weight=config.handoff_completeness_weight,
        conflict_reserve_weight=config.conflict_reserve_weight,
        pass_threshold=config.pass_threshold,
        watch_threshold=config.watch_threshold,
        min_pass_local_confidence_score=config.min_pass_local_confidence_score,
        min_watch_local_confidence_score=config.min_watch_local_confidence_score,
        min_pass_cross_team_agreement_score=(
            config.min_pass_cross_team_agreement_score
        ),
        min_watch_cross_team_agreement_score=(
            config.min_watch_cross_team_agreement_score
        ),
        min_pass_evidence_support_score=config.min_pass_evidence_support_score,
        min_watch_evidence_support_score=config.min_watch_evidence_support_score,
        min_pass_handoff_completeness_score=(
            config.min_pass_handoff_completeness_score
        ),
        min_watch_handoff_completeness_score=(
            config.min_watch_handoff_completeness_score
        ),
        max_pass_conflict_pressure_score=config.max_pass_conflict_pressure_score,
        max_watch_conflict_pressure_score=config.max_watch_conflict_pressure_score,
        signal_count=_count(len(rows)),
        domain_count=_count(len({row.domain_key for row in rows})),
        team_count=_count(len({row.team_key for row in rows})),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        human_review_required_count=_count(
            sum(1 for row in rows if row.human_review_required),
        ),
        priority_review_count=_count(
            sum(1 for row in rows if row.human_review_route == "priority_review"),
        ),
        standard_review_count=_count(
            sum(1 for row in rows if row.human_review_route == "standard_review"),
        ),
        average_router_confidence_score=_average_field(
            rows,
            "router_confidence_score",
        ),
        average_conflict_pressure_score=_average_field(
            rows,
            "conflict_pressure_score",
        ),
        highest_conflict_pressure_score=_max_ratio_field(
            rows,
            "conflict_pressure_score",
        ),
        oldest_assessment_age_seconds=_max_measure_field(
            rows,
            "assessment_age_seconds",
        ),
        status=_status_rollup(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_domain_cross_team_confidence_router_report_payload(
    report: ResearchStrategyDomainCrossTeamConfidenceRouterReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyDomainCrossTeamConfidenceRouterReport:
        raise ValueError(
            "report must be a ResearchStrategyDomainCrossTeamConfidenceRouterReport",
        )
    _require_hard_flags("report", report)
    _revalidate_report_for_payload(report)
    _validate_report_public_payload_sha256(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("payload", payload)
    validate_research_strategy_domain_cross_team_confidence_router_public_payload(
        payload,
    )
    return payload


def validate_research_strategy_domain_cross_team_confidence_router_public_payload(
    payload: object,
) -> bool:
    rebuilt_report = _report_from_public_payload(payload)
    rebuilt_payload = _json_ready(rebuilt_report)
    if rebuilt_payload != payload:
        raise ValueError("public payload must match fully derived report fields")
    return True


def _row_values_for_input(
    value: ResearchStrategyDomainCrossTeamConfidenceRouterInput,
    *,
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
    generated_at: datetime,
) -> _RowValues:
    assessment_age_seconds = _age_seconds(value.observed_at, generated_at)
    router_confidence_score = _router_confidence_score(value, config=config)
    reason_codes = _row_reason_codes(
        local_confidence_score=value.local_confidence_score,
        cross_team_agreement_score=value.cross_team_agreement_score,
        evidence_support_score=value.evidence_support_score,
        handoff_completeness_score=value.handoff_completeness_score,
        conflict_pressure_score=value.conflict_pressure_score,
        router_confidence_score=router_confidence_score,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return _RowValues(
        domain_key=value.domain_key,
        team_key=value.team_key,
        assessment_digest=_public_hash(value.assessment_label),
        status=status,
        human_review_required=status != PASS_STATUS,
        human_review_route=_human_review_route(status),
        observed_at=value.observed_at,
        assessment_age_seconds=assessment_age_seconds,
        local_confidence_score=value.local_confidence_score,
        cross_team_agreement_score=value.cross_team_agreement_score,
        evidence_support_score=value.evidence_support_score,
        handoff_completeness_score=value.handoff_completeness_score,
        conflict_pressure_score=value.conflict_pressure_score,
        router_confidence_score=router_confidence_score,
        reason_codes=reason_codes,
    )


def _row_from_values(
    rank: Decimal,
    values: _RowValues,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterRow:
    return ResearchStrategyDomainCrossTeamConfidenceRouterRow(
        rank=rank,
        domain_key=values.domain_key,
        team_key=values.team_key,
        assessment_digest=values.assessment_digest,
        status=values.status,
        human_review_required=values.human_review_required,
        human_review_route=values.human_review_route,
        observed_at=values.observed_at,
        assessment_age_seconds=values.assessment_age_seconds,
        local_confidence_score=values.local_confidence_score,
        cross_team_agreement_score=values.cross_team_agreement_score,
        evidence_support_score=values.evidence_support_score,
        handoff_completeness_score=values.handoff_completeness_score,
        conflict_pressure_score=values.conflict_pressure_score,
        router_confidence_score=values.router_confidence_score,
        reason_codes=values.reason_codes,
    )


def _router_confidence_score(
    value: ResearchStrategyDomainCrossTeamConfidenceRouterInput,
    *,
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
) -> Decimal:
    return _router_confidence_score_from_values(
        local_confidence_score=value.local_confidence_score,
        cross_team_agreement_score=value.cross_team_agreement_score,
        evidence_support_score=value.evidence_support_score,
        handoff_completeness_score=value.handoff_completeness_score,
        conflict_pressure_score=value.conflict_pressure_score,
        config=config,
    )


def _router_confidence_score_from_values(
    *,
    local_confidence_score: Decimal,
    cross_team_agreement_score: Decimal,
    evidence_support_score: Decimal,
    handoff_completeness_score: Decimal,
    conflict_pressure_score: Decimal,
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        conflict_reserve_score = ONE - conflict_pressure_score
        score = (
            (local_confidence_score * config.local_confidence_weight)
            + (cross_team_agreement_score * config.cross_team_agreement_weight)
            + (evidence_support_score * config.evidence_support_weight)
            + (handoff_completeness_score * config.handoff_completeness_weight)
            + (conflict_reserve_score * config.conflict_reserve_weight)
        )
    return _quantize_ratio(score)


def _row_reason_codes(
    *,
    local_confidence_score: Decimal,
    cross_team_agreement_score: Decimal,
    evidence_support_score: Decimal,
    handoff_completeness_score: Decimal,
    conflict_pressure_score: Decimal,
    router_confidence_score: Decimal,
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
) -> tuple[str, ...]:
    block_codes: list[str] = []
    watch_codes: list[str] = []
    if router_confidence_score < config.watch_threshold:
        block_codes.append("router_confidence_score_block")
    elif router_confidence_score < config.pass_threshold:
        watch_codes.append("router_confidence_score_watch")
    if local_confidence_score < config.min_watch_local_confidence_score:
        block_codes.append("local_confidence_score_block")
    elif local_confidence_score < config.min_pass_local_confidence_score:
        watch_codes.append("local_confidence_score_watch")
    if cross_team_agreement_score < config.min_watch_cross_team_agreement_score:
        block_codes.append("cross_team_agreement_score_block")
    elif cross_team_agreement_score < config.min_pass_cross_team_agreement_score:
        watch_codes.append("cross_team_agreement_score_watch")
    if evidence_support_score < config.min_watch_evidence_support_score:
        block_codes.append("evidence_support_score_block")
    elif evidence_support_score < config.min_pass_evidence_support_score:
        watch_codes.append("evidence_support_score_watch")
    if handoff_completeness_score < config.min_watch_handoff_completeness_score:
        block_codes.append("handoff_completeness_score_block")
    elif handoff_completeness_score < config.min_pass_handoff_completeness_score:
        watch_codes.append("handoff_completeness_score_watch")
    if conflict_pressure_score >= config.max_watch_conflict_pressure_score:
        block_codes.append("conflict_pressure_score_block")
    elif conflict_pressure_score >= config.max_pass_conflict_pressure_score:
        watch_codes.append("conflict_pressure_score_watch")
    if block_codes:
        return _normalize_reason_codes("reason_codes", tuple(block_codes), ROW_REASON_CODES)
    if watch_codes:
        return _normalize_reason_codes("reason_codes", tuple(watch_codes), ROW_REASON_CODES)
    return (ROW_PASS_REASON_CODE,)


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status_code = {
        PASS_STATUS: REPORT_PASS_REASON_CODE,
        WATCH_STATUS: REPORT_WATCH_REASON_CODE,
        BLOCK_STATUS: REPORT_BLOCK_REASON_CODE,
    }[_status_rollup(rows)]
    seen = {status_code}
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    return (
        status_code,
        *(
            reason_code
            for reason_code in ROW_REASON_CODES
            if reason_code in row_codes
            and reason_code not in seen
            and (reason_code != ROW_PASS_REASON_CODE or status_code == REPORT_PASS_REASON_CODE)
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
) -> tuple[ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON_CODE,
                count=COUNT_QUANTUM,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if counts[reason_code]
    )


def _normalize_inputs(
    values: Iterable[ResearchStrategyDomainCrossTeamConfidenceRouterInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyDomainCrossTeamConfidenceRouterInput, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("signals must be an iterable of router inputs")
    normalized = tuple(values)
    revalidated: list[ResearchStrategyDomainCrossTeamConfidenceRouterInput] = []
    for value in normalized:
        if type(value) is not ResearchStrategyDomainCrossTeamConfidenceRouterInput:
            raise ValueError(
                "signals must contain ResearchStrategyDomainCrossTeamConfidenceRouterInput",
            )
        value = _revalidate_input(value)
        _require_hard_flags("input", value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        revalidated.append(value)
    return tuple(revalidated)


def _revalidate_config(
    value: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterConfig:
    return ResearchStrategyDomainCrossTeamConfidenceRouterConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_input(
    value: ResearchStrategyDomainCrossTeamConfidenceRouterInput,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterInput:
    return ResearchStrategyDomainCrossTeamConfidenceRouterInput(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _normalize_rows(
    values: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
) -> tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    for value in values:
        if type(value) is not ResearchStrategyDomainCrossTeamConfidenceRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainCrossTeamConfidenceRouterRow",
            )
    expected_ranks = tuple(_count(index) for index in range(1, len(values) + 1))
    if tuple(value.rank for value in values) != expected_ranks:
        raise ValueError("rows must use deterministic rank sequence")
    if tuple(sorted(values, key=_row_sort_key)) != values:
        raise ValueError("rows must use deterministic sequence")
    return values


def _normalize_reason_code_counts(
    values: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount, ...],
) -> tuple[ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount",
            )
    if tuple(sorted(values, key=lambda value: REPORT_REASON_CODES.index(value.reason_code))) != values:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return values


def _validate_row(row: ResearchStrategyDomainCrossTeamConfidenceRouterRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    expected_review_required = row.status != PASS_STATUS
    if row.human_review_required is not expected_review_required:
        raise ValueError("human_review_required must match status")
    if row.human_review_route != _human_review_route(row.status):
        raise ValueError("human_review_route must match status")


def _validate_report(report: ResearchStrategyDomainCrossTeamConfidenceRouterReport) -> None:
    rows = report.rows
    config = _config_from_report(report)
    for row in rows:
        _validate_row_derivations(
            row,
            generated_at=report.generated_at,
            config=config,
        )
    expected_values = {
        "signal_count": _count(len(rows)),
        "domain_count": _count(len({row.domain_key for row in rows})),
        "team_count": _count(len({row.team_key for row in rows})),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "human_review_required_count": _count(
            sum(1 for row in rows if row.human_review_required),
        ),
        "priority_review_count": _count(
            sum(1 for row in rows if row.human_review_route == "priority_review"),
        ),
        "standard_review_count": _count(
            sum(1 for row in rows if row.human_review_route == "standard_review"),
        ),
        "average_router_confidence_score": _average_field(
            rows,
            "router_confidence_score",
        ),
        "average_conflict_pressure_score": _average_field(
            rows,
            "conflict_pressure_score",
        ),
        "highest_conflict_pressure_score": _max_ratio_field(
            rows,
            "conflict_pressure_score",
        ),
        "oldest_assessment_age_seconds": _max_measure_field(
            rows,
            "assessment_age_seconds",
        ),
        "status": _status_rollup(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match report rows")


def _revalidate_report_for_payload(
    report: ResearchStrategyDomainCrossTeamConfidenceRouterReport,
) -> None:
    for row in report.rows:
        ResearchStrategyDomainCrossTeamConfidenceRouterRow(
            rank=row.rank,
            domain_key=row.domain_key,
            team_key=row.team_key,
            assessment_digest=row.assessment_digest,
            status=row.status,
            human_review_required=row.human_review_required,
            human_review_route=row.human_review_route,
            observed_at=row.observed_at,
            assessment_age_seconds=row.assessment_age_seconds,
            local_confidence_score=row.local_confidence_score,
            cross_team_agreement_score=row.cross_team_agreement_score,
            evidence_support_score=row.evidence_support_score,
            handoff_completeness_score=row.handoff_completeness_score,
            conflict_pressure_score=row.conflict_pressure_score,
            router_confidence_score=row.router_confidence_score,
            reason_codes=row.reason_codes,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        )
    for reason_code_count in report.reason_code_counts:
        ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount(
            reason_code=reason_code_count.reason_code,
            count=reason_code_count.count,
            paper_only=reason_code_count.paper_only,
            report_only=reason_code_count.report_only,
            readonly=reason_code_count.readonly,
        )
    _validate_report(report)


def _validate_row_derivations(
    row: ResearchStrategyDomainCrossTeamConfidenceRouterRow,
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
) -> None:
    expected_age_seconds = _age_seconds(row.observed_at, generated_at)
    if row.assessment_age_seconds != expected_age_seconds:
        raise ValueError("assessment_age_seconds must match report timestamps")
    expected_router_confidence_score = _router_confidence_score_from_values(
        local_confidence_score=row.local_confidence_score,
        cross_team_agreement_score=row.cross_team_agreement_score,
        evidence_support_score=row.evidence_support_score,
        handoff_completeness_score=row.handoff_completeness_score,
        conflict_pressure_score=row.conflict_pressure_score,
        config=config,
    )
    if row.router_confidence_score != expected_router_confidence_score:
        raise ValueError("router_confidence_score must match component scores")
    expected_reason_codes = _row_reason_codes(
        local_confidence_score=row.local_confidence_score,
        cross_team_agreement_score=row.cross_team_agreement_score,
        evidence_support_score=row.evidence_support_score,
        handoff_completeness_score=row.handoff_completeness_score,
        conflict_pressure_score=row.conflict_pressure_score,
        router_confidence_score=expected_router_confidence_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match component scores")
    expected_status = _status_from_reason_codes(expected_reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match component scores")
    if row.human_review_required is not (expected_status != PASS_STATUS):
        raise ValueError("human_review_required must match component scores")
    if row.human_review_route != _human_review_route(expected_status):
        raise ValueError("human_review_route must match component scores")


def _config_from_report(
    report: ResearchStrategyDomainCrossTeamConfidenceRouterReport,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterConfig:
    return ResearchStrategyDomainCrossTeamConfidenceRouterConfig(
        config_version=report.config_version,
        local_confidence_weight=report.local_confidence_weight,
        cross_team_agreement_weight=report.cross_team_agreement_weight,
        evidence_support_weight=report.evidence_support_weight,
        handoff_completeness_weight=report.handoff_completeness_weight,
        conflict_reserve_weight=report.conflict_reserve_weight,
        pass_threshold=report.pass_threshold,
        watch_threshold=report.watch_threshold,
        min_pass_local_confidence_score=report.min_pass_local_confidence_score,
        min_watch_local_confidence_score=report.min_watch_local_confidence_score,
        min_pass_cross_team_agreement_score=(
            report.min_pass_cross_team_agreement_score
        ),
        min_watch_cross_team_agreement_score=(
            report.min_watch_cross_team_agreement_score
        ),
        min_pass_evidence_support_score=report.min_pass_evidence_support_score,
        min_watch_evidence_support_score=report.min_watch_evidence_support_score,
        min_pass_handoff_completeness_score=(
            report.min_pass_handoff_completeness_score
        ),
        min_watch_handoff_completeness_score=(
            report.min_watch_handoff_completeness_score
        ),
        max_pass_conflict_pressure_score=report.max_pass_conflict_pressure_score,
        max_watch_conflict_pressure_score=report.max_watch_conflict_pressure_score,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _status_rollup(
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
) -> str:
    if not rows or any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return BLOCK_STATUS
    if any(code.endswith("_watch") for code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _human_review_route(status: str) -> str:
    return {
        PASS_STATUS: "no_review",
        WATCH_STATUS: "standard_review",
        BLOCK_STATUS: "priority_review",
    }[status]


def _row_values_sort_key(value: _RowValues) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_WEIGHT[value.status],
        value.router_confidence_score,
        _fixed_subtract(ONE, value.conflict_pressure_score),
        _fixed_subtract(ZERO, value.assessment_age_seconds),
        value.domain_key,
        value.team_key,
        value.assessment_digest,
    )


def _row_sort_key(
    row: ResearchStrategyDomainCrossTeamConfidenceRouterRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_WEIGHT[row.status],
        row.router_confidence_score,
        _fixed_subtract(ONE, row.conflict_pressure_score),
        _fixed_subtract(ZERO, row.assessment_age_seconds),
        row.domain_key,
        row.team_key,
        row.assessment_digest,
    )


def _average_field(
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        total = sum((getattr(row, field_name) for row in rows), ZERO)
        average = total / Decimal(len(rows))
    return _quantize_ratio(average)


def _max_ratio_field(
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _max_measure_field(
    rows: tuple[ResearchStrategyDomainCrossTeamConfidenceRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            (Decimal(delta.days) * SECONDS_PER_DAY)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize_measure(seconds)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _fixed_subtract(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return left - right


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    try:
        return _quantize_ratio(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} exceeds the fixed context") from exc


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        return _quantize_measure(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} exceeds the fixed context") from exc


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        integral_value = normalized.to_integral_value()
        if normalized != integral_value:
            raise ValueError(f"{field_name} must be a whole count")
        return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("decimal value exceeds the fixed context") from exc


def _quantize_measure(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("decimal value exceeds the fixed context") from exc


def _require_weight_total(
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = (
            config.local_confidence_weight
            + config.cross_team_agreement_weight
            + config.evidence_support_weight
            + config.handoff_completeness_weight
            + config.conflict_reserve_weight
        )
    if _quantize_ratio(total) != ONE:
        raise ValueError("confidence weights must total one")


def _require_less_than(field_name: str, lower_value: Decimal, upper_value: Decimal) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{field_name} must be less than the paired threshold")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_status(field_name: str, value: object) -> None:
    _require_member(
        field_name,
        value,
        RESEARCH_STRATEGY_DOMAIN_CROSS_TEAM_CONFIDENCE_ROUTER_STATUSES,
    )


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_safe_label(field_name: str, value: object) -> str:
    label = _require_public_string(field_name, value)
    if len(label) > 64:
        raise ValueError(f"{field_name} must be at most 64 characters")
    lowered = label.lower()
    if lowered != label:
        raise ValueError(f"{field_name} must be lower-case")
    if _has_restricted_fragment(lowered, RESTRICTED_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains restricted references")
    identifier_tokens = {
        token
        for token in lowered.replace("-", "_").split("_")
        if token
    }
    if identifier_tokens & PRIVATE_IDENTIFIER_TOKENS:
        raise ValueError(f"{field_name} contains restricted public identifier")
    for character in label:
        if not (
            "a" <= character <= "z"
            or "0" <= character <= "9"
            or character in {"-", "_"}
        ):
            raise ValueError(f"{field_name} must use public label characters")
    return label


def _require_assessment_label(field_name: str, value: object) -> str:
    label = _require_public_string(field_name, value)
    if len(label) > 256:
        raise ValueError(f"{field_name} must be at most 256 characters")
    lowered = label.lower()
    restricted = tuple(
        fragment
        for fragment in RESTRICTED_VALUE_FRAGMENTS
        if not fragment.startswith(_join_parts("candidate", "_"))
    )
    if _has_restricted_fragment(lowered, restricted):
        raise ValueError(f"{field_name} contains restricted references")
    return label


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if reason_code not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed if reason_code in seen)
    if value != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _report_from_public_payload(
    value: object,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterReport:
    payload = _require_payload_object(
        "report payload",
        value,
        REPORT_PAYLOAD_FIELDS,
    )
    generated_at = _payload_datetime("generated_at", payload["generated_at"])
    config_values = {
        field_name: _payload_probability_decimal(field_name, payload[field_name])
        for field_name in CONFIG_DECIMAL_FIELDS
    }
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a canonical JSON array")
    rows = tuple(
        _row_from_public_payload(
            row_value,
            generated_at=generated_at,
            config=ResearchStrategyDomainCrossTeamConfidenceRouterConfig(
                config_version=payload["config_version"],
                **config_values,
            ),
        )
        for row_value in rows_value
    )
    reason_code_counts_value = payload["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError("reason_code_counts must be a canonical JSON array")
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(count_value)
        for count_value in reason_code_counts_value
    )
    return ResearchStrategyDomainCrossTeamConfidenceRouterReport(
        generated_at=generated_at,
        config_version=payload["config_version"],
        **config_values,
        signal_count=_payload_nonnegative_count(
            "signal_count",
            payload["signal_count"],
        ),
        domain_count=_payload_nonnegative_count(
            "domain_count",
            payload["domain_count"],
        ),
        team_count=_payload_nonnegative_count("team_count", payload["team_count"]),
        pass_count=_payload_nonnegative_count("pass_count", payload["pass_count"]),
        watch_count=_payload_nonnegative_count("watch_count", payload["watch_count"]),
        block_count=_payload_nonnegative_count("block_count", payload["block_count"]),
        human_review_required_count=_payload_nonnegative_count(
            "human_review_required_count",
            payload["human_review_required_count"],
        ),
        priority_review_count=_payload_nonnegative_count(
            "priority_review_count",
            payload["priority_review_count"],
        ),
        standard_review_count=_payload_nonnegative_count(
            "standard_review_count",
            payload["standard_review_count"],
        ),
        average_router_confidence_score=_payload_probability_decimal(
            "average_router_confidence_score",
            payload["average_router_confidence_score"],
        ),
        average_conflict_pressure_score=_payload_probability_decimal(
            "average_conflict_pressure_score",
            payload["average_conflict_pressure_score"],
        ),
        highest_conflict_pressure_score=_payload_probability_decimal(
            "highest_conflict_pressure_score",
            payload["highest_conflict_pressure_score"],
        ),
        oldest_assessment_age_seconds=_payload_nonnegative_decimal(
            "oldest_assessment_age_seconds",
            payload["oldest_assessment_age_seconds"],
        ),
        status=payload["status"],
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        reason_code_counts=reason_code_counts,
        rows=rows,
        public_payload_sha256=payload["public_payload_sha256"],
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainCrossTeamConfidenceRouterConfig,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterRow:
    payload = _require_payload_object("row payload", value, ROW_PAYLOAD_FIELDS)
    row = ResearchStrategyDomainCrossTeamConfidenceRouterRow(
        rank=_payload_positive_count("rank", payload["rank"]),
        domain_key=payload["domain_key"],
        team_key=payload["team_key"],
        assessment_digest=payload["assessment_digest"],
        status=payload["status"],
        human_review_required=_payload_bool(
            "human_review_required",
            payload["human_review_required"],
        ),
        human_review_route=payload["human_review_route"],
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        assessment_age_seconds=_payload_nonnegative_decimal(
            "assessment_age_seconds",
            payload["assessment_age_seconds"],
        ),
        local_confidence_score=_payload_probability_decimal(
            "local_confidence_score",
            payload["local_confidence_score"],
        ),
        cross_team_agreement_score=_payload_probability_decimal(
            "cross_team_agreement_score",
            payload["cross_team_agreement_score"],
        ),
        evidence_support_score=_payload_probability_decimal(
            "evidence_support_score",
            payload["evidence_support_score"],
        ),
        handoff_completeness_score=_payload_probability_decimal(
            "handoff_completeness_score",
            payload["handoff_completeness_score"],
        ),
        conflict_pressure_score=_payload_probability_decimal(
            "conflict_pressure_score",
            payload["conflict_pressure_score"],
        ),
        router_confidence_score=_payload_probability_decimal(
            "router_confidence_score",
            payload["router_confidence_score"],
        ),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )
    _validate_row_derivations(
        row,
        generated_at=generated_at,
        config=config,
    )
    return row


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount:
    payload = _require_payload_object(
        "reason_code_count payload",
        value,
        REASON_CODE_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchStrategyDomainCrossTeamConfidenceRouterReasonCodeCount(
        reason_code=payload["reason_code"],
        count=_payload_positive_count("count", payload["count"]),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _require_payload_object(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a canonical JSON object")
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} must use exact canonical schema")
    actual_fields = tuple(value)
    if actual_fields != expected_fields:
        if len(actual_fields) == len(expected_fields) and set(actual_fields) == set(
            expected_fields,
        ):
            raise ValueError(f"{label} must use canonical field sequence")
        raise ValueError(f"{label} must use exact canonical schema")
    return value


def _payload_decimal(
    field_name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a canonical decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    return normalized


def _payload_probability_decimal(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_probability_decimal)


def _payload_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_decimal)


def _payload_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_count)


def _payload_positive_count(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_positive_count)


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must be a canonical string array")
    return tuple(value)


def _payload_bool(field_name: str, value: object) -> bool:
    _require_bool(field_name, value)
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _unsigned_report_payload(
    report: ResearchStrategyDomainCrossTeamConfidenceRouterReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("public_payload_sha256", None)
    return payload


def _report_public_payload_sha256(
    report: ResearchStrategyDomainCrossTeamConfidenceRouterReport,
) -> str:
    payload = _unsigned_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_report_public_payload_sha256(
    report: ResearchStrategyDomainCrossTeamConfidenceRouterReport,
) -> None:
    expected_sha256 = _report_public_payload_sha256(report)
    if report.public_payload_sha256 != expected_sha256:
        raise ValueError("public_payload_sha256 must match report fields")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _json_ready(value))
        return
    if type(value) is str:
        lowered = value.lower()
        if _has_restricted_fragment(lowered, RESTRICTED_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered_key = key.lower()
            if _has_restricted_fragment(lowered_key, RESTRICTED_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_restricted_fragment(value: str, fragments: tuple[str, ...]) -> bool:
    return any(fragment in value for fragment in fragments)
