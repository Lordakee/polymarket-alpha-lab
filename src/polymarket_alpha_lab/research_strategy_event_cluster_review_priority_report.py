"""Report-only event-cluster review priority surface for strategy research."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_REVIEW_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-strategy-event-cluster-review-priority-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
REPORT_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_EMPTY_INPUT = "empty_input"
REASON_REVIEW_PRIORITY_PASS = "event_cluster_review_priority_pass"
REASON_SIGNAL_DIVERGENCE_WATCH = "signal_divergence_watch"
REASON_SIGNAL_DIVERGENCE_BLOCK = "signal_divergence_block"
REASON_EVIDENCE_FRESHNESS_WATCH = "evidence_freshness_watch"
REASON_EVIDENCE_FRESHNESS_BLOCK = "evidence_freshness_block"
REASON_SOURCE_CONSENSUS_WATCH = "source_consensus_watch"
REASON_SOURCE_CONSENSUS_BLOCK = "source_consensus_block"
REASON_COST_PRESSURE_WATCH = "cost_pressure_watch"
REASON_COST_PRESSURE_BLOCK = "cost_pressure_block"
REASON_RESOLUTION_AMBIGUITY_WATCH = "resolution_ambiguity_watch"
REASON_RESOLUTION_AMBIGUITY_BLOCK = "resolution_ambiguity_block"
REASON_TEAM_CAPACITY_WATCH = "team_capacity_watch"
REASON_TEAM_CAPACITY_BLOCK = "team_capacity_block"
REASON_REVIEW_PRIORITY_SCORE_WATCH = "review_priority_score_watch"
REASON_REVIEW_PRIORITY_SCORE_BLOCK = "review_priority_score_block"

ROW_REASON_CODE_SEQUENCE = (
    REASON_SIGNAL_DIVERGENCE_BLOCK,
    REASON_EVIDENCE_FRESHNESS_BLOCK,
    REASON_SOURCE_CONSENSUS_BLOCK,
    REASON_COST_PRESSURE_BLOCK,
    REASON_RESOLUTION_AMBIGUITY_BLOCK,
    REASON_TEAM_CAPACITY_BLOCK,
    REASON_REVIEW_PRIORITY_SCORE_BLOCK,
    REASON_SIGNAL_DIVERGENCE_WATCH,
    REASON_EVIDENCE_FRESHNESS_WATCH,
    REASON_SOURCE_CONSENSUS_WATCH,
    REASON_COST_PRESSURE_WATCH,
    REASON_RESOLUTION_AMBIGUITY_WATCH,
    REASON_TEAM_CAPACITY_WATCH,
    REASON_REVIEW_PRIORITY_SCORE_WATCH,
    REASON_REVIEW_PRIORITY_PASS,
)
REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *ROW_REASON_CODE_SEQUENCE)
BLOCK_REASON_CODES = frozenset(
    (
        REASON_SIGNAL_DIVERGENCE_BLOCK,
        REASON_EVIDENCE_FRESHNESS_BLOCK,
        REASON_SOURCE_CONSENSUS_BLOCK,
        REASON_COST_PRESSURE_BLOCK,
        REASON_RESOLUTION_AMBIGUITY_BLOCK,
        REASON_TEAM_CAPACITY_BLOCK,
        REASON_REVIEW_PRIORITY_SCORE_BLOCK,
    ),
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
TOP_LEVEL_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_review_priority_score",
        "max_review_priority_score",
        "max_evidence_age_seconds",
        "min_source_consensus_score",
        "max_cost_pressure_score",
        "max_resolution_ambiguity_score",
        "min_team_capacity_score",
        "rows",
        "reason_code_counts",
        "reason_codes",
        DIGEST_FIELD,
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "cluster_row_number",
        "cluster_digest",
        "signal_divergence_score",
        "evidence_age_seconds",
        "evidence_freshness_pressure_score",
        "source_consensus_score",
        "source_consensus_gap_score",
        "cost_pressure_score",
        "resolution_ambiguity_score",
        "team_capacity_score",
        "team_capacity_pressure_score",
        "review_priority_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "raw_market",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "database",
    "table",
    "tok" + "en",
    "wal" + "let",
    "au" + "th",
    "ord" + "er",
    "tr" + "ade",
    "position",
    "siz" + "ing",
    "buy",
    "sell",
    "recommend",
    "http://",
    "https://",
    "://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyEventClusterReviewPriorityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_REVIEW_PRIORITY_REPORT_CONFIG_VERSION
    )
    signal_divergence_watch_threshold: Decimal = Decimal("0.200000")
    signal_divergence_block_threshold: Decimal = Decimal("0.350000")
    evidence_freshness_watch_age_seconds: Decimal = Decimal("7200.000000")
    evidence_freshness_block_age_seconds: Decimal = Decimal("21600.000000")
    source_consensus_watch_min_score: Decimal = Decimal("0.700000")
    source_consensus_block_min_score: Decimal = Decimal("0.500000")
    cost_pressure_watch_threshold: Decimal = Decimal("0.300000")
    cost_pressure_block_threshold: Decimal = Decimal("0.650000")
    resolution_ambiguity_watch_threshold: Decimal = Decimal("0.300000")
    resolution_ambiguity_block_threshold: Decimal = Decimal("0.600000")
    team_capacity_watch_min_score: Decimal = Decimal("0.500000")
    team_capacity_block_min_score: Decimal = Decimal("0.250000")
    review_priority_watch_threshold: Decimal = Decimal("0.500000")
    review_priority_block_threshold: Decimal = Decimal("0.750000")
    signal_divergence_weight: Decimal = Decimal("0.200000")
    evidence_freshness_weight: Decimal = Decimal("0.150000")
    source_consensus_gap_weight: Decimal = Decimal("0.200000")
    cost_pressure_weight: Decimal = Decimal("0.150000")
    resolution_ambiguity_weight: Decimal = Decimal("0.200000")
    team_capacity_pressure_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEventClusterReviewPriorityConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_REVIEW_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "signal_divergence_watch_threshold",
            "signal_divergence_block_threshold",
            "source_consensus_watch_min_score",
            "source_consensus_block_min_score",
            "cost_pressure_watch_threshold",
            "cost_pressure_block_threshold",
            "resolution_ambiguity_watch_threshold",
            "resolution_ambiguity_block_threshold",
            "team_capacity_watch_min_score",
            "team_capacity_block_min_score",
            "review_priority_watch_threshold",
            "review_priority_block_threshold",
            "signal_divergence_weight",
            "evidence_freshness_weight",
            "source_consensus_gap_weight",
            "cost_pressure_weight",
            "resolution_ambiguity_weight",
            "team_capacity_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_freshness_watch_age_seconds",
            "evidence_freshness_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.signal_divergence_watch_threshold
            > self.signal_divergence_block_threshold
        ):
            raise ValueError("signal divergence thresholds must be nondecreasing")
        if (
            self.evidence_freshness_watch_age_seconds
            > self.evidence_freshness_block_age_seconds
        ):
            raise ValueError("evidence freshness thresholds must be nondecreasing")
        if (
            self.source_consensus_block_min_score
            > self.source_consensus_watch_min_score
        ):
            raise ValueError("source consensus minimums must be nondecreasing")
        if self.cost_pressure_watch_threshold > self.cost_pressure_block_threshold:
            raise ValueError("cost pressure thresholds must be nondecreasing")
        if (
            self.resolution_ambiguity_watch_threshold
            > self.resolution_ambiguity_block_threshold
        ):
            raise ValueError("resolution ambiguity thresholds must be nondecreasing")
        if self.team_capacity_block_min_score > self.team_capacity_watch_min_score:
            raise ValueError("team capacity minimums must be nondecreasing")
        if self.review_priority_watch_threshold > self.review_priority_block_threshold:
            raise ValueError("review priority thresholds must be nondecreasing")
        weight_sum = _quantize(
            self.signal_divergence_weight
            + self.evidence_freshness_weight
            + self.source_consensus_gap_weight
            + self.cost_pressure_weight
            + self.resolution_ambiguity_weight
            + self.team_capacity_pressure_weight,
        )
        if weight_sum != ONE:
            raise ValueError("review priority weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterReviewPriorityInputRow(_FinalPublicDataclass):
    cluster_ref: str
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_market_question: str
    raw_source_url: str
    raw_source_text: str
    signal_divergence_score: Decimal
    evidence_observed_at: datetime
    source_consensus_score: Decimal
    cost_pressure_score: Decimal
    resolution_ambiguity_score: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventClusterReviewPriorityInputRow,
            "input row",
        )
        for field_name in (
            "cluster_ref",
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_market_question",
            "raw_source_url",
            "raw_source_text",
        ):
            _require_private_text(field_name, getattr(self, field_name))
        for field_name in (
            "signal_divergence_score",
            "source_consensus_score",
            "cost_pressure_score",
            "resolution_ambiguity_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterReviewPriorityReportRow(_FinalPublicDataclass):
    cluster_row_number: Decimal
    cluster_digest: str
    signal_divergence_score: Decimal
    evidence_age_seconds: Decimal
    evidence_freshness_pressure_score: Decimal
    source_consensus_score: Decimal
    source_consensus_gap_score: Decimal
    cost_pressure_score: Decimal
    resolution_ambiguity_score: Decimal
    team_capacity_score: Decimal
    team_capacity_pressure_score: Decimal
    review_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventClusterReviewPriorityReportRow,
            "report row",
        )
        object.__setattr__(
            self,
            "cluster_row_number",
            _require_positive_decimal("cluster_row_number", self.cluster_row_number),
        )
        object.__setattr__(
            self,
            "cluster_digest",
            _require_private_digest("cluster_digest", self.cluster_digest),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal("evidence_age_seconds", self.evidence_age_seconds),
        )
        for field_name in (
            "signal_divergence_score",
            "evidence_freshness_pressure_score",
            "source_consensus_score",
            "source_consensus_gap_score",
            "cost_pressure_score",
            "resolution_ambiguity_score",
            "team_capacity_score",
            "team_capacity_pressure_score",
            "review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("report row", self)
        _reject_unsafe_public_payload("report row", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterReviewPriorityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEventClusterReviewPriorityReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
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
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterReviewPriorityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_review_priority_score: Decimal
    max_review_priority_score: Decimal
    max_evidence_age_seconds: Decimal
    min_source_consensus_score: Decimal
    max_cost_pressure_score: Decimal
    max_resolution_ambiguity_score: Decimal
    min_team_capacity_score: Decimal
    rows: tuple[ResearchStrategyEventClusterReviewPriorityReportRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyEventClusterReviewPriorityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEventClusterReviewPriorityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_REVIEW_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_review_priority_score",
            "max_review_priority_score",
            "min_source_consensus_score",
            "max_cost_pressure_score",
            "max_resolution_ambiguity_score",
            "min_team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _require_nonnegative_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_event_cluster_review_priority_report_payload(self)


def build_research_strategy_event_cluster_review_priority_report(
    input_rows: Sequence[ResearchStrategyEventClusterReviewPriorityInputRow],
    *,
    generated_at: datetime,
    config: ResearchStrategyEventClusterReviewPriorityConfig | None = None,
) -> ResearchStrategyEventClusterReviewPriorityReport:
    cfg = config or ResearchStrategyEventClusterReviewPriorityConfig()
    if type(cfg) is not ResearchStrategyEventClusterReviewPriorityConfig:
        raise ValueError("config must be a ResearchStrategyEventClusterReviewPriorityConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(input_rows)
    for row in normalized_inputs:
        if row.evidence_observed_at > report_time:
            raise ValueError("evidence_observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg, report_time) for row in normalized_inputs),
            key=_row_sort_key_without_number,
        ),
    )
    numbered_rows = tuple(
        _with_row_number(row, index) for index, row in enumerate(rows, start=1)
    )
    reason_code_counts = _reason_code_counts(numbered_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not numbered_rows:
        reason_code_counts = (
            ResearchStrategyEventClusterReviewPriorityReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(numbered_rows),
        "row_count": _decimal_count(len(numbered_rows)),
        "pass_count": _decimal_count(_status_count(numbered_rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(numbered_rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(numbered_rows, STATUS_BLOCK)),
        "average_review_priority_score": _average_ratio(
            tuple(row.review_priority_score for row in numbered_rows),
        ),
        "max_review_priority_score": max(
            (row.review_priority_score for row in numbered_rows),
            default=ZERO,
        ),
        "max_evidence_age_seconds": max(
            (row.evidence_age_seconds for row in numbered_rows),
            default=ZERO,
        ),
        "min_source_consensus_score": min(
            (row.source_consensus_score for row in numbered_rows),
            default=ZERO,
        ),
        "max_cost_pressure_score": max(
            (row.cost_pressure_score for row in numbered_rows),
            default=ZERO,
        ),
        "max_resolution_ambiguity_score": max(
            (row.resolution_ambiguity_score for row in numbered_rows),
            default=ZERO,
        ),
        "min_team_capacity_score": min(
            (row.team_capacity_score for row in numbered_rows),
            default=ZERO,
        ),
        "rows": numbered_rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEventClusterReviewPriorityReport(**values)


def research_strategy_event_cluster_review_priority_report_payload(
    value: ResearchStrategyEventClusterReviewPriorityReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyEventClusterReviewPriorityReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyEventClusterReviewPriorityReport or dict",
        )
    _validate_payload_statuses(payload)
    _validate_payload_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_shape(payload)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchStrategyEventClusterReviewPriorityInputRow,
    config: ResearchStrategyEventClusterReviewPriorityConfig,
    generated_at: datetime,
) -> ResearchStrategyEventClusterReviewPriorityReportRow:
    evidence_age = _age_seconds(generated_at, row.evidence_observed_at)
    evidence_pressure = min(
        ONE,
        _bounded_ratio(evidence_age, config.evidence_freshness_block_age_seconds),
    )
    source_gap = _inverse_ratio(row.source_consensus_score)
    capacity_pressure = _inverse_ratio(row.team_capacity_score)
    priority_score = _review_priority_score(
        signal_divergence_score=row.signal_divergence_score,
        evidence_freshness_pressure_score=evidence_pressure,
        source_consensus_gap_score=source_gap,
        cost_pressure_score=row.cost_pressure_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        team_capacity_pressure_score=capacity_pressure,
        config=config,
    )
    reason_codes = _row_reason_codes(
        signal_divergence_score=row.signal_divergence_score,
        evidence_age_seconds=evidence_age,
        source_consensus_score=row.source_consensus_score,
        cost_pressure_score=row.cost_pressure_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        team_capacity_score=row.team_capacity_score,
        review_priority_score=priority_score,
        config=config,
    )
    return ResearchStrategyEventClusterReviewPriorityReportRow(
        cluster_row_number=ONE,
        cluster_digest=_private_ref_digest(row.cluster_ref),
        signal_divergence_score=row.signal_divergence_score,
        evidence_age_seconds=evidence_age,
        evidence_freshness_pressure_score=evidence_pressure,
        source_consensus_score=row.source_consensus_score,
        source_consensus_gap_score=source_gap,
        cost_pressure_score=row.cost_pressure_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        team_capacity_score=row.team_capacity_score,
        team_capacity_pressure_score=capacity_pressure,
        review_priority_score=priority_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _with_row_number(
    row: ResearchStrategyEventClusterReviewPriorityReportRow,
    index: int,
) -> ResearchStrategyEventClusterReviewPriorityReportRow:
    return ResearchStrategyEventClusterReviewPriorityReportRow(
        cluster_row_number=_decimal_count(index),
        cluster_digest=row.cluster_digest,
        signal_divergence_score=row.signal_divergence_score,
        evidence_age_seconds=row.evidence_age_seconds,
        evidence_freshness_pressure_score=row.evidence_freshness_pressure_score,
        source_consensus_score=row.source_consensus_score,
        source_consensus_gap_score=row.source_consensus_gap_score,
        cost_pressure_score=row.cost_pressure_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        team_capacity_score=row.team_capacity_score,
        team_capacity_pressure_score=row.team_capacity_pressure_score,
        review_priority_score=row.review_priority_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    signal_divergence_score: Decimal,
    evidence_age_seconds: Decimal,
    source_consensus_score: Decimal,
    cost_pressure_score: Decimal,
    resolution_ambiguity_score: Decimal,
    team_capacity_score: Decimal,
    review_priority_score: Decimal,
    config: ResearchStrategyEventClusterReviewPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_high_threshold_reason(
        reason_codes,
        metric=signal_divergence_score,
        watch_threshold=config.signal_divergence_watch_threshold,
        block_threshold=config.signal_divergence_block_threshold,
        watch_reason=REASON_SIGNAL_DIVERGENCE_WATCH,
        block_reason=REASON_SIGNAL_DIVERGENCE_BLOCK,
    )
    _append_high_threshold_reason(
        reason_codes,
        metric=evidence_age_seconds,
        watch_threshold=config.evidence_freshness_watch_age_seconds,
        block_threshold=config.evidence_freshness_block_age_seconds,
        watch_reason=REASON_EVIDENCE_FRESHNESS_WATCH,
        block_reason=REASON_EVIDENCE_FRESHNESS_BLOCK,
    )
    _append_low_threshold_reason(
        reason_codes,
        metric=source_consensus_score,
        watch_min_score=config.source_consensus_watch_min_score,
        block_min_score=config.source_consensus_block_min_score,
        watch_reason=REASON_SOURCE_CONSENSUS_WATCH,
        block_reason=REASON_SOURCE_CONSENSUS_BLOCK,
    )
    _append_high_threshold_reason(
        reason_codes,
        metric=cost_pressure_score,
        watch_threshold=config.cost_pressure_watch_threshold,
        block_threshold=config.cost_pressure_block_threshold,
        watch_reason=REASON_COST_PRESSURE_WATCH,
        block_reason=REASON_COST_PRESSURE_BLOCK,
    )
    _append_high_threshold_reason(
        reason_codes,
        metric=resolution_ambiguity_score,
        watch_threshold=config.resolution_ambiguity_watch_threshold,
        block_threshold=config.resolution_ambiguity_block_threshold,
        watch_reason=REASON_RESOLUTION_AMBIGUITY_WATCH,
        block_reason=REASON_RESOLUTION_AMBIGUITY_BLOCK,
    )
    _append_low_threshold_reason(
        reason_codes,
        metric=team_capacity_score,
        watch_min_score=config.team_capacity_watch_min_score,
        block_min_score=config.team_capacity_block_min_score,
        watch_reason=REASON_TEAM_CAPACITY_WATCH,
        block_reason=REASON_TEAM_CAPACITY_BLOCK,
    )
    _append_high_threshold_reason(
        reason_codes,
        metric=review_priority_score,
        watch_threshold=config.review_priority_watch_threshold,
        block_threshold=config.review_priority_block_threshold,
        watch_reason=REASON_REVIEW_PRIORITY_SCORE_WATCH,
        block_reason=REASON_REVIEW_PRIORITY_SCORE_BLOCK,
    )
    if not reason_codes:
        reason_codes.append(REASON_REVIEW_PRIORITY_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _append_high_threshold_reason(
    reason_codes: list[str],
    *,
    metric: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if metric >= block_threshold:
        reason_codes.append(block_reason)
    elif metric >= watch_threshold:
        reason_codes.append(watch_reason)


def _append_low_threshold_reason(
    reason_codes: list[str],
    *,
    metric: Decimal,
    watch_min_score: Decimal,
    block_min_score: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if metric < block_min_score:
        reason_codes.append(block_reason)
    elif metric < watch_min_score:
        reason_codes.append(watch_reason)


def _review_priority_score(
    *,
    signal_divergence_score: Decimal,
    evidence_freshness_pressure_score: Decimal,
    source_consensus_gap_score: Decimal,
    cost_pressure_score: Decimal,
    resolution_ambiguity_score: Decimal,
    team_capacity_pressure_score: Decimal,
    config: ResearchStrategyEventClusterReviewPriorityConfig,
) -> Decimal:
    score = (
        signal_divergence_score * config.signal_divergence_weight
        + evidence_freshness_pressure_score * config.evidence_freshness_weight
        + source_consensus_gap_score * config.source_consensus_gap_weight
        + cost_pressure_score * config.cost_pressure_weight
        + resolution_ambiguity_score * config.resolution_ambiguity_weight
        + team_capacity_pressure_score * config.team_capacity_pressure_weight
    )
    return _require_ratio_decimal("review_priority_score", score)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (REASON_REVIEW_PRIORITY_PASS,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyEventClusterReviewPriorityReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyEventClusterReviewPriorityReportRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key_without_number(
    row: ResearchStrategyEventClusterReviewPriorityReportRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.review_priority_score,
        -row.resolution_ambiguity_score,
        -row.signal_divergence_score,
        -row.cost_pressure_score,
        row.cluster_digest,
    )


def _row_sort_key(
    row: ResearchStrategyEventClusterReviewPriorityReportRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return _row_sort_key_without_number(row)


def _reason_code_counts(
    rows: tuple[ResearchStrategyEventClusterReviewPriorityReportRow, ...],
) -> tuple[ResearchStrategyEventClusterReviewPriorityReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchStrategyEventClusterReviewPriorityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_ratio(_decimal_count(counts[reason_code]), total),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(row: ResearchStrategyEventClusterReviewPriorityReportRow) -> None:
    if row.source_consensus_gap_score != _inverse_ratio(row.source_consensus_score):
        raise ValueError("source_consensus_gap_score must match source_consensus_score")
    if row.team_capacity_pressure_score != _inverse_ratio(row.team_capacity_score):
        raise ValueError("team_capacity_pressure_score must match team_capacity_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_REVIEW_PRIORITY_PASS in row.reason_codes
        and row.reason_codes != (REASON_REVIEW_PRIORITY_PASS,)
    ):
        raise ValueError("pass reason cannot be mixed with watch or block reasons")


def _validate_report(report: ResearchStrategyEventClusterReviewPriorityReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_review_priority_score != _average_ratio(
        tuple(row.review_priority_score for row in report.rows),
    ):
        raise ValueError("average_review_priority_score must match rows")
    if report.max_review_priority_score != max(
        (row.review_priority_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_review_priority_score must match rows")
    if report.max_evidence_age_seconds != max(
        (row.evidence_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.min_source_consensus_score != min(
        (row.source_consensus_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_source_consensus_score must match rows")
    if report.max_cost_pressure_score != max(
        (row.cost_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_cost_pressure_score must match rows")
    if report.max_resolution_ambiguity_score != max(
        (row.resolution_ambiguity_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_resolution_ambiguity_score must match rows")
    if report.min_team_capacity_score != min(
        (row.team_capacity_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_team_capacity_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyEventClusterReviewPriorityReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_inputs(
    input_rows: Sequence[ResearchStrategyEventClusterReviewPriorityInputRow],
) -> tuple[ResearchStrategyEventClusterReviewPriorityInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    normalized = tuple(input_rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEventClusterReviewPriorityInputRow:
            raise ValueError(
                "input_rows must contain ResearchStrategyEventClusterReviewPriorityInputRow",
            )
        _require_hard_flags("input row", row)
        digest = _private_ref_digest(row.cluster_ref)
        if digest in seen:
            raise ValueError("input_rows must be unique by cluster digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyEventClusterReviewPriorityReportRow, ...],
) -> tuple[ResearchStrategyEventClusterReviewPriorityReportRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    expected_row_number = ONE
    for row in normalized:
        if type(row) is not ResearchStrategyEventClusterReviewPriorityReportRow:
            raise ValueError(
                "rows must contain ResearchStrategyEventClusterReviewPriorityReportRow",
            )
        _require_hard_flags("report row", row)
        if row.cluster_digest in seen:
            raise ValueError("rows must be unique by cluster digest")
        seen.add(row.cluster_digest)
        if row.cluster_row_number != expected_row_number:
            raise ValueError("cluster_row_number must be contiguous")
        expected_row_number = _quantize(expected_row_number + ONE)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyEventClusterReviewPriorityReasonCodeCount, ...],
) -> tuple[ResearchStrategyEventClusterReviewPriorityReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyEventClusterReviewPriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEventClusterReviewPriorityReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    sequence = {reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)}
    if normalized != tuple(sorted(normalized, key=lambda row: sequence[row.reason_code])):
        raise ValueError("reason_code_counts must use deterministic sort")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must be unique")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
        if reason_code == REASON_EMPTY_INPUT:
            raise ValueError("empty_input is report-only")
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_REVIEW_PRIORITY_PASS in value and value != (REASON_REVIEW_PRIORITY_PASS,):
        raise ValueError("reason_codes cannot mix pass with watch or block reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _report_payload(
    report: ResearchStrategyEventClusterReviewPriorityReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_review_priority_score=report.average_review_priority_score,
        max_review_priority_score=report.max_review_priority_score,
        max_evidence_age_seconds=report.max_evidence_age_seconds,
        min_source_consensus_score=report.min_source_consensus_score,
        max_cost_pressure_score=report.max_cost_pressure_score,
        max_resolution_ambiguity_score=report.max_resolution_ambiguity_score,
        min_team_capacity_score=report.min_team_capacity_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(**values: object) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(report: ResearchStrategyEventClusterReviewPriorityReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_review_priority_score": report.average_review_priority_score,
            "max_review_priority_score": report.max_review_priority_score,
            "max_evidence_age_seconds": report.max_evidence_age_seconds,
            "min_source_consensus_score": report.min_source_consensus_score,
            "max_cost_pressure_score": report.max_cost_pressure_score,
            "max_resolution_ambiguity_score": report.max_resolution_ambiguity_score,
            "min_team_capacity_score": report.min_team_capacity_score,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(DIGEST_FIELD)
    _require_digest(DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(DIGEST_FIELD, None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status" and item not in REPORT_STATUSES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _validate_payload_flags(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _validate_payload_flags(item)
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True")
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_flags(item)


def _validate_payload_shape(payload: dict[str, object]) -> None:
    _require_payload_keys("payload", payload, TOP_LEVEL_PAYLOAD_KEYS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_keys("payload.rows", row, ROW_PAYLOAD_KEYS)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for reason_code_count in reason_code_counts:
        if type(reason_code_count) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_payload_keys(
            "payload.reason_code_counts",
            reason_code_count,
            REASON_CODE_COUNT_PAYLOAD_KEYS,
        )
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list or any(type(item) is not str for item in reason_codes):
        raise ValueError("reason_codes must be a list of strings")


def _require_payload_keys(
    label: str,
    payload: Mapping[str, object],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload.keys())
    extra_keys = actual_keys - expected_keys
    if extra_keys:
        raise ValueError(
            f"unexpected public payload key {sorted(extra_keys)[0]} in {label}",
        )
    missing_keys = expected_keys - actual_keys
    if missing_keys:
        raise ValueError(
            f"missing public payload key {sorted(missing_keys)[0]} in {label}",
        )


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload contains unsupported JSON value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            ready[field.name] = _json_ready(getattr(value, field.name))
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            _json_ready(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(f"{label}.{key}", key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{label} must be a public dataclass or JSON object")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload value in {label}")


def _private_ref_digest(value: str) -> str:
    _require_private_text("cluster_ref", value)
    return "sha256:" + sha256(
        ("research_strategy_event_cluster_review_priority:" + value).encode("utf-8"),
    ).hexdigest()


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return _quantize(age_seconds)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _decimal_count(len(values)))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _require_ratio_decimal("ratio", numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    decimal_value = _require_nonnegative_decimal("ratio", numerator / denominator)
    return min(ONE, decimal_value)


def _inverse_ratio(value: Decimal) -> Decimal:
    return _require_ratio_decimal("inverse_ratio", ONE - value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = _quantize(value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a concrete UTC offset")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be known")


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 private digest")
    digest = value.removeprefix("sha256:")
    _require_digest(field_name, digest)
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    _require_private_text(field_name, value)
    text = str(value)
    if len(text) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    if any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-" for character in text):
        raise ValueError(f"{field_name} must be a public identifier")
    return text


def _require_private_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_REVIEW_PRIORITY_REPORT_CONFIG_VERSION",
    "REPORT_STATUSES",
    "ResearchStrategyEventClusterReviewPriorityConfig",
    "ResearchStrategyEventClusterReviewPriorityInputRow",
    "ResearchStrategyEventClusterReviewPriorityReportRow",
    "ResearchStrategyEventClusterReviewPriorityReasonCodeCount",
    "ResearchStrategyEventClusterReviewPriorityReport",
    "build_research_strategy_event_cluster_review_priority_report",
    "research_strategy_event_cluster_review_priority_report_payload",
)
