"""Report-only decision queue latency summaries for research strategy teams."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION = (
    "research-strategy-team-decision-queue-latency-report-v0"
)
RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_STATUSES = (
    "pass",
    "watch",
    "block",
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT_PREC = 64
_PUBLIC_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_ROW_PAYLOAD_FIELDS = (
    "queue_item_hash",
    "team_key",
    "decision_lane_key",
    "status",
    "queue_age_seconds",
    "assignment_lag_seconds",
    "required_reviewer_count",
    "available_reviewer_count",
    "reviewer_gap_ratio",
    "open_decision_count",
    "decision_capacity_count",
    "queue_load_ratio",
    "queue_load_pressure",
    "sla_breached_count",
    "sla_breach_ratio",
    "sla_breach_pressure",
    "rework_count",
    "rework_pressure",
    "escalation_pressure",
    "queue_age_pressure",
    "assignment_lag_pressure",
    "reviewer_gap_pressure",
    "latency_score",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_CODE_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "queue_item_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "queue_item_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_open_decisions",
    "average_queue_age_seconds",
    "average_assignment_lag_seconds",
    "average_reviewer_gap_ratio",
    "average_queue_load_ratio",
    "average_latency_score",
    "max_latency_score",
    "rows",
    "reason_codes",
    "reason_code_counts",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

_QUEUE_AGE_WEIGHT = Decimal("0.220000")
_ASSIGNMENT_LAG_WEIGHT = Decimal("0.180000")
_REVIEWER_GAP_WEIGHT = Decimal("0.170000")
_SLA_BREACH_WEIGHT = Decimal("0.160000")
_QUEUE_LOAD_WEIGHT = Decimal("0.140000")
_REWORK_WEIGHT = Decimal("0.080000")
_ESCALATION_WEIGHT = Decimal("0.050000")

_PASS_REASON_CODE = "decision_queue_latency_pass"
_EMPTY_REASON_CODE = "decision_queue_latency_no_inputs"
_REPORT_BLOCK_REASON_CODE = "decision_queue_latency_report_block_rows"
_REPORT_WATCH_REASON_CODE = "decision_queue_latency_report_watch_rows"
_REPORT_PASS_REASON_CODE = "decision_queue_latency_report_pass"
_ROW_REASON_CODE_SEQUENCE = (
    _PASS_REASON_CODE,
    "queue_age_watch",
    "queue_age_block",
    "assignment_lag_watch",
    "assignment_lag_block",
    "reviewer_gap_watch",
    "reviewer_gap_block",
    "decision_sla_breach_watch",
    "decision_sla_breach_block",
    "queue_load_watch",
    "queue_load_block",
    "rework_pressure_watch",
    "rework_pressure_block",
    "escalation_pressure_watch",
    "escalation_pressure_block",
    "latency_score_watch",
    "latency_score_block",
)
_REPORT_REASON_CODE_SEQUENCE = (
    _REPORT_BLOCK_REASON_CODE,
    _REPORT_WATCH_REASON_CODE,
    _REPORT_PASS_REASON_CODE,
    _EMPTY_REASON_CODE,
)
_REASON_CODE_SEQUENCE = _ROW_REASON_CODE_SEQUENCE + _REPORT_REASON_CODE_SEQUENCE
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "cand" + "idate",
    "event",
    "mar" + "ket",
    "slug",
    "que" + "stion",
    "sour" + "ce",
    "url",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "secret",
    "credential",
    "password",
    "private" + "_key",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "database" + "_url",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "b" + "uy",
    "s" + "ell",
    "recom" + "mendation",
    "siz" + "ing",
    "pos" + "ition",
    "exe" + "cute",
    "exe" + "cution",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_STATUSES",
    "ResearchStrategyTeamDecisionQueueLatencyConfig",
    "ResearchStrategyTeamDecisionQueueLatencyInput",
    "ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount",
    "ResearchStrategyTeamDecisionQueueLatencyReport",
    "ResearchStrategyTeamDecisionQueueLatencyRow",
    "build_research_strategy_team_decision_queue_latency_report",
    "research_strategy_team_decision_queue_latency_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyTeamDecisionQueueLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION
    )
    watch_latency_score_threshold: Decimal = Decimal("0.350000")
    block_latency_score_threshold: Decimal = Decimal("0.700000")
    watch_queue_age_seconds: Decimal = Decimal("1800.000000")
    block_queue_age_seconds: Decimal = Decimal("7200.000000")
    watch_assignment_lag_seconds: Decimal = Decimal("900.000000")
    block_assignment_lag_seconds: Decimal = Decimal("3600.000000")
    watch_reviewer_gap_ratio: Decimal = Decimal("0.250000")
    block_reviewer_gap_ratio: Decimal = Decimal("0.500000")
    watch_decision_sla_breach_ratio: Decimal = Decimal("0.100000")
    block_decision_sla_breach_ratio: Decimal = Decimal("0.300000")
    watch_queue_load_ratio: Decimal = Decimal("0.750000")
    block_queue_load_ratio: Decimal = Decimal("1.250000")
    watch_rework_pressure: Decimal = Decimal("0.100000")
    block_rework_pressure: Decimal = Decimal("0.300000")
    watch_escalation_pressure: Decimal = Decimal("0.300000")
    block_escalation_pressure: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamDecisionQueueLatencyConfig:
            raise TypeError(
                "ResearchStrategyTeamDecisionQueueLatencyConfig subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDecisionQueueLatencyConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_key("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_latency_score_threshold",
            "block_latency_score_threshold",
            "watch_reviewer_gap_ratio",
            "block_reviewer_gap_ratio",
            "watch_decision_sla_breach_ratio",
            "block_decision_sla_breach_ratio",
            "watch_rework_pressure",
            "block_rework_pressure",
            "watch_escalation_pressure",
            "block_escalation_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_queue_age_seconds",
            "block_queue_age_seconds",
            "watch_assignment_lag_seconds",
            "block_assignment_lag_seconds",
            "watch_queue_load_ratio",
            "block_queue_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDecisionQueueLatencyInput:
    queue_item_ref: str
    team_key: str
    decision_lane_key: str
    queued_at: datetime
    first_review_started_at: datetime
    required_reviewer_count: Decimal
    available_reviewer_count: Decimal
    open_decision_count: Decimal
    decision_capacity_count: Decimal
    sla_breached_count: Decimal
    rework_count: Decimal
    escalation_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamDecisionQueueLatencyInput:
            raise TypeError(
                "ResearchStrategyTeamDecisionQueueLatencyInput subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDecisionQueueLatencyInput, "input")
        _require_private_ref("queue_item_ref", self.queue_item_ref)
        object.__setattr__(
            self,
            "team_key",
            _require_public_key("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "decision_lane_key",
            _require_public_key("decision_lane_key", self.decision_lane_key),
        )
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "first_review_started_at",
            _as_utc("first_review_started_at", self.first_review_started_at),
        )
        if self.first_review_started_at < self.queued_at:
            raise ValueError("first_review_started_at must be at or after queued_at")
        for field_name in (
            "required_reviewer_count",
            "available_reviewer_count",
            "open_decision_count",
            "decision_capacity_count",
            "sla_breached_count",
            "rework_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_reviewer_count <= _ZERO:
            raise ValueError("required_reviewer_count must be positive")
        if self.decision_capacity_count <= _ZERO:
            raise ValueError("decision_capacity_count must be positive")
        if self.available_reviewer_count > self.required_reviewer_count:
            raise ValueError(
                "available_reviewer_count must be at most required_reviewer_count",
            )
        if self.sla_breached_count > self.open_decision_count:
            raise ValueError("sla_breached_count must be at most open_decision_count")
        if self.rework_count > self.open_decision_count:
            raise ValueError("rework_count must be at most open_decision_count")
        object.__setattr__(
            self,
            "escalation_pressure",
            _require_ratio_decimal("escalation_pressure", self.escalation_pressure),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDecisionQueueLatencyRow:
    queue_item_hash: str
    team_key: str
    decision_lane_key: str
    status: str
    queue_age_seconds: Decimal
    assignment_lag_seconds: Decimal
    required_reviewer_count: Decimal
    available_reviewer_count: Decimal
    reviewer_gap_ratio: Decimal
    open_decision_count: Decimal
    decision_capacity_count: Decimal
    queue_load_ratio: Decimal
    queue_load_pressure: Decimal
    sla_breached_count: Decimal
    sla_breach_ratio: Decimal
    sla_breach_pressure: Decimal
    rework_count: Decimal
    rework_pressure: Decimal
    escalation_pressure: Decimal
    queue_age_pressure: Decimal
    assignment_lag_pressure: Decimal
    reviewer_gap_pressure: Decimal
    latency_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamDecisionQueueLatencyRow:
            raise TypeError(
                "ResearchStrategyTeamDecisionQueueLatencyRow subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDecisionQueueLatencyRow, "row")
        _require_public_digest("queue_item_hash", self.queue_item_hash)
        object.__setattr__(
            self,
            "team_key",
            _require_public_key("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "decision_lane_key",
            _require_public_key("decision_lane_key", self.decision_lane_key),
        )
        _require_status("status", self.status)
        for field_name in (
            "required_reviewer_count",
            "available_reviewer_count",
            "open_decision_count",
            "decision_capacity_count",
            "sla_breached_count",
            "rework_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("queue_age_seconds", "assignment_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reviewer_gap_ratio",
            "queue_load_pressure",
            "sla_breach_ratio",
            "sla_breach_pressure",
            "rework_pressure",
            "escalation_pressure",
            "queue_age_pressure",
            "assignment_lag_pressure",
            "reviewer_gap_pressure",
            "latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_load_ratio",
            _require_nonnegative_decimal("queue_load_ratio", self.queue_load_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _public_digest_for_dataclass(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_public_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row payload")
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount:
    reason_code: str
    count: Decimal
    queue_item_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount:
            raise TypeError(
                "ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount subclass "
                "is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount,
            "reason_code_count",
        )
        if type(self.reason_code) is not str or self.reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be a supported public reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "queue_item_ratio",
            _require_ratio_decimal("queue_item_ratio", self.queue_item_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDecisionQueueLatencyReport:
    generated_at: datetime
    config_version: str
    status: str
    queue_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_open_decisions: Decimal
    average_queue_age_seconds: Decimal
    average_assignment_lag_seconds: Decimal
    average_reviewer_gap_ratio: Decimal
    average_queue_load_ratio: Decimal
    average_latency_score: Decimal
    max_latency_score: Decimal
    rows: tuple[ResearchStrategyTeamDecisionQueueLatencyRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount,
        ...
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamDecisionQueueLatencyReport:
            raise TypeError(
                "ResearchStrategyTeamDecisionQueueLatencyReport subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDecisionQueueLatencyReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_key("config_version", self.config_version),
        )
        _require_status("status", self.status)
        for field_name in (
            "queue_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_open_decisions",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_queue_age_seconds",
            "average_assignment_lag_seconds",
            "average_reviewer_gap_ratio",
            "average_queue_load_ratio",
            "average_latency_score",
            "max_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reviewer_gap_ratio",
            "average_latency_score",
            "max_latency_score",
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_dataclass(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_public_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        _validate_report(self)


def build_research_strategy_team_decision_queue_latency_report(
    inputs: Sequence[ResearchStrategyTeamDecisionQueueLatencyInput],
    *,
    config: ResearchStrategyTeamDecisionQueueLatencyConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyTeamDecisionQueueLatencyReport:
    cfg = config or ResearchStrategyTeamDecisionQueueLatencyConfig()
    if type(cfg) is not ResearchStrategyTeamDecisionQueueLatencyConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamDecisionQueueLatencyConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.queued_at > report_time:
            raise ValueError("queued_at must be at or before generated_at")
        if item.first_review_started_at > report_time:
            raise ValueError("first_review_started_at must be at or before generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, cfg, report_time) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyTeamDecisionQueueLatencyReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_report_status(rows),
        queue_item_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        total_open_decisions=_sum_decimal(row.open_decision_count for row in rows),
        average_queue_age_seconds=_average_decimal(
            row.queue_age_seconds for row in rows
        ),
        average_assignment_lag_seconds=_average_decimal(
            row.assignment_lag_seconds for row in rows
        ),
        average_reviewer_gap_ratio=_average_decimal(
            row.reviewer_gap_ratio for row in rows
        ),
        average_queue_load_ratio=_average_decimal(
            row.queue_load_ratio for row in rows
        ),
        average_latency_score=_average_decimal(row.latency_score for row in rows),
        max_latency_score=max((row.latency_score for row in rows), default=_ZERO),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_strategy_team_decision_queue_latency_report_payload(
    report: ResearchStrategyTeamDecisionQueueLatencyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamDecisionQueueLatencyReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload(payload)
        return payload
    raise ValueError(
        "report must be a ResearchStrategyTeamDecisionQueueLatencyReport or payload",
    )


def _row_from_input(
    item: ResearchStrategyTeamDecisionQueueLatencyInput,
    config: ResearchStrategyTeamDecisionQueueLatencyConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamDecisionQueueLatencyRow:
    queue_age_seconds = _duration_seconds(item.queued_at, generated_at)
    assignment_lag_seconds = _duration_seconds(
        item.queued_at,
        item.first_review_started_at,
    )
    reviewer_gap_ratio = _ratio_or_zero(
        item.required_reviewer_count - item.available_reviewer_count,
        item.required_reviewer_count,
    )
    queue_load_ratio = _ratio_or_zero(
        item.open_decision_count,
        item.decision_capacity_count,
    )
    sla_breach_ratio = _ratio_or_zero(item.sla_breached_count, item.open_decision_count)
    rework_pressure = _ratio_or_zero(item.rework_count, item.open_decision_count)
    queue_age_pressure = _clamp_ratio(queue_age_seconds / config.block_queue_age_seconds)
    assignment_lag_pressure = _clamp_ratio(
        assignment_lag_seconds / config.block_assignment_lag_seconds,
    )
    reviewer_gap_pressure = _clamp_ratio(
        reviewer_gap_ratio / config.block_reviewer_gap_ratio,
    )
    queue_load_pressure = _clamp_ratio(
        queue_load_ratio / config.block_queue_load_ratio,
    )
    sla_breach_pressure = _clamp_ratio(
        sla_breach_ratio / config.block_decision_sla_breach_ratio,
    )
    escalation_pressure = item.escalation_pressure
    latency_score = _latency_score(
        queue_age_pressure=queue_age_pressure,
        assignment_lag_pressure=assignment_lag_pressure,
        reviewer_gap_pressure=reviewer_gap_pressure,
        sla_breach_pressure=sla_breach_pressure,
        queue_load_pressure=queue_load_pressure,
        rework_pressure=rework_pressure,
        escalation_pressure=escalation_pressure,
    )
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
        queue_age_seconds=queue_age_seconds,
        assignment_lag_seconds=assignment_lag_seconds,
        reviewer_gap_ratio=reviewer_gap_ratio,
        queue_load_ratio=queue_load_ratio,
        sla_breach_ratio=sla_breach_ratio,
        rework_pressure=rework_pressure,
        latency_score=latency_score,
    )
    return ResearchStrategyTeamDecisionQueueLatencyRow(
        queue_item_hash=_hash_private_ref(item.queue_item_ref),
        team_key=item.team_key,
        decision_lane_key=item.decision_lane_key,
        status=_status_from_reason_codes(reason_codes),
        queue_age_seconds=queue_age_seconds,
        assignment_lag_seconds=assignment_lag_seconds,
        required_reviewer_count=item.required_reviewer_count,
        available_reviewer_count=item.available_reviewer_count,
        reviewer_gap_ratio=reviewer_gap_ratio,
        open_decision_count=item.open_decision_count,
        decision_capacity_count=item.decision_capacity_count,
        queue_load_ratio=queue_load_ratio,
        queue_load_pressure=queue_load_pressure,
        sla_breached_count=item.sla_breached_count,
        sla_breach_ratio=sla_breach_ratio,
        sla_breach_pressure=sla_breach_pressure,
        rework_count=item.rework_count,
        rework_pressure=rework_pressure,
        escalation_pressure=escalation_pressure,
        queue_age_pressure=queue_age_pressure,
        assignment_lag_pressure=assignment_lag_pressure,
        reviewer_gap_pressure=reviewer_gap_pressure,
        latency_score=latency_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchStrategyTeamDecisionQueueLatencyInput,
    config: ResearchStrategyTeamDecisionQueueLatencyConfig,
    queue_age_seconds: Decimal,
    assignment_lag_seconds: Decimal,
    reviewer_gap_ratio: Decimal,
    queue_load_ratio: Decimal,
    sla_breach_ratio: Decimal,
    rework_pressure: Decimal,
    latency_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_metric_reason(
        codes,
        "queue_age",
        _metric_status_above(
            queue_age_seconds,
            config.watch_queue_age_seconds,
            config.block_queue_age_seconds,
        ),
    )
    _append_metric_reason(
        codes,
        "assignment_lag",
        _metric_status_above(
            assignment_lag_seconds,
            config.watch_assignment_lag_seconds,
            config.block_assignment_lag_seconds,
        ),
    )
    _append_metric_reason(
        codes,
        "reviewer_gap",
        _metric_status_above(
            reviewer_gap_ratio,
            config.watch_reviewer_gap_ratio,
            config.block_reviewer_gap_ratio,
        ),
    )
    _append_metric_reason(
        codes,
        "decision_sla_breach",
        _metric_status_above(
            sla_breach_ratio,
            config.watch_decision_sla_breach_ratio,
            config.block_decision_sla_breach_ratio,
        ),
    )
    _append_metric_reason(
        codes,
        "queue_load",
        _metric_status_above(
            queue_load_ratio,
            config.watch_queue_load_ratio,
            config.block_queue_load_ratio,
        ),
    )
    _append_metric_reason(
        codes,
        "rework_pressure",
        _metric_status_above(
            rework_pressure,
            config.watch_rework_pressure,
            config.block_rework_pressure,
        ),
    )
    _append_metric_reason(
        codes,
        "escalation_pressure",
        _metric_status_above(
            item.escalation_pressure,
            config.watch_escalation_pressure,
            config.block_escalation_pressure,
        ),
    )
    _append_metric_reason(
        codes,
        "latency_score",
        _metric_status_above(
            latency_score,
            config.watch_latency_score_threshold,
            config.block_latency_score_threshold,
        ),
    )
    if not codes:
        return (_PASS_REASON_CODE,)
    return _normalize_row_reason_codes(tuple(codes))


def _append_metric_reason(codes: list[str], prefix: str, status: str) -> None:
    if status != "pass":
        codes.append(f"{prefix}_{status}")


def _metric_status_above(
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return "block"
    if value > watch_threshold:
        return "watch"
    return "pass"


def _latency_score(
    *,
    queue_age_pressure: Decimal,
    assignment_lag_pressure: Decimal,
    reviewer_gap_pressure: Decimal,
    sla_breach_pressure: Decimal,
    queue_load_pressure: Decimal,
    rework_pressure: Decimal,
    escalation_pressure: Decimal,
) -> Decimal:
    return _clamp_ratio(
        queue_age_pressure * _QUEUE_AGE_WEIGHT
        + assignment_lag_pressure * _ASSIGNMENT_LAG_WEIGHT
        + reviewer_gap_pressure * _REVIEWER_GAP_WEIGHT
        + sla_breach_pressure * _SLA_BREACH_WEIGHT
        + queue_load_pressure * _QUEUE_LOAD_WEIGHT
        + rework_pressure * _REWORK_WEIGHT
        + escalation_pressure * _ESCALATION_WEIGHT,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyTeamDecisionQueueLatencyInput],
) -> tuple[ResearchStrategyTeamDecisionQueueLatencyInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyTeamDecisionQueueLatencyInput:
            raise ValueError(
                "inputs must contain ResearchStrategyTeamDecisionQueueLatencyInput",
            )
        if item.queue_item_ref in seen:
            raise ValueError("duplicate queue_item_ref")
        seen.add(item.queue_item_ref)
    return tuple(sorted(normalized, key=lambda item: _hash_private_ref(item.queue_item_ref)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyTeamDecisionQueueLatencyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchStrategyTeamDecisionQueueLatencyRow")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchStrategyTeamDecisionQueueLatencyRow",
        ) from exc
    for row in normalized:
        if type(row) is not ResearchStrategyTeamDecisionQueueLatencyRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamDecisionQueueLatencyRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount",
        )
    try:
        normalized = tuple(counts)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount",
        ) from exc
    for count in normalized:
        if type(count) is not ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount",
            )
    return tuple(
        sorted(normalized, key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code))
    )


def _row_sort_key(
    row: ResearchStrategyTeamDecisionQueueLatencyRow,
) -> tuple[Decimal, str, str]:
    return (-row.latency_score, row.team_key, row.decision_lane_key)


def _report_status(
    rows: tuple[ResearchStrategyTeamDecisionQueueLatencyRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchStrategyTeamDecisionQueueLatencyRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamDecisionQueueLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON_CODE,)
    codes: list[str] = []
    if _status_count(rows, "block") > 0:
        codes.append(_REPORT_BLOCK_REASON_CODE)
    if _status_count(rows, "watch") > 0:
        codes.append(_REPORT_WATCH_REASON_CODE)
    if not codes:
        codes.append(_REPORT_PASS_REASON_CODE)
    return _normalize_report_reason_codes(tuple(codes))


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamDecisionQueueLatencyRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    counter.update(report_reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            queue_item_ratio=_ratio_or_zero(_count(count), row_count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: _REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _validate_config(
    config: ResearchStrategyTeamDecisionQueueLatencyConfig,
) -> None:
    _require_threshold_pair(
        "watch_latency_score_threshold",
        config.watch_latency_score_threshold,
        "block_latency_score_threshold",
        config.block_latency_score_threshold,
    )
    _require_threshold_pair(
        "watch_queue_age_seconds",
        config.watch_queue_age_seconds,
        "block_queue_age_seconds",
        config.block_queue_age_seconds,
    )
    _require_threshold_pair(
        "watch_assignment_lag_seconds",
        config.watch_assignment_lag_seconds,
        "block_assignment_lag_seconds",
        config.block_assignment_lag_seconds,
    )
    _require_threshold_pair(
        "watch_reviewer_gap_ratio",
        config.watch_reviewer_gap_ratio,
        "block_reviewer_gap_ratio",
        config.block_reviewer_gap_ratio,
    )
    _require_threshold_pair(
        "watch_decision_sla_breach_ratio",
        config.watch_decision_sla_breach_ratio,
        "block_decision_sla_breach_ratio",
        config.block_decision_sla_breach_ratio,
    )
    _require_threshold_pair(
        "watch_queue_load_ratio",
        config.watch_queue_load_ratio,
        "block_queue_load_ratio",
        config.block_queue_load_ratio,
    )
    _require_threshold_pair(
        "watch_rework_pressure",
        config.watch_rework_pressure,
        "block_rework_pressure",
        config.block_rework_pressure,
    )
    _require_threshold_pair(
        "watch_escalation_pressure",
        config.watch_escalation_pressure,
        "block_escalation_pressure",
        config.block_escalation_pressure,
    )


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_name} must be at most {block_name}")


def _validate_row(row: ResearchStrategyTeamDecisionQueueLatencyRow) -> None:
    if row.available_reviewer_count > row.required_reviewer_count:
        raise ValueError(
            "available_reviewer_count must be at most required_reviewer_count",
        )
    if row.sla_breached_count > row.open_decision_count:
        raise ValueError("sla_breached_count must be at most open_decision_count")
    if row.rework_count > row.open_decision_count:
        raise ValueError("rework_count must be at most open_decision_count")
    if row.reviewer_gap_ratio != _ratio_or_zero(
        row.required_reviewer_count - row.available_reviewer_count,
        row.required_reviewer_count,
    ):
        raise ValueError("reviewer_gap_ratio must match reviewer counts")
    if row.queue_load_ratio != _ratio_or_zero(
        row.open_decision_count,
        row.decision_capacity_count,
    ):
        raise ValueError("queue_load_ratio must match queue counts")
    if row.sla_breach_ratio != _ratio_or_zero(
        row.sla_breached_count,
        row.open_decision_count,
    ):
        raise ValueError("sla_breach_ratio must match queue counts")
    if row.rework_pressure != _ratio_or_zero(row.rework_count, row.open_decision_count):
        raise ValueError("rework_pressure must match queue counts")
    if row.latency_score != _latency_score(
        queue_age_pressure=row.queue_age_pressure,
        assignment_lag_pressure=row.assignment_lag_pressure,
        reviewer_gap_pressure=row.reviewer_gap_pressure,
        sla_breach_pressure=row.sla_breach_pressure,
        queue_load_pressure=row.queue_load_pressure,
        rework_pressure=row.rework_pressure,
        escalation_pressure=row.escalation_pressure,
    ):
        raise ValueError("latency_score must match component pressures")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchStrategyTeamDecisionQueueLatencyReport) -> None:
    if report.queue_item_count != _count(len(report.rows)):
        raise ValueError("queue_item_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.total_open_decisions != _sum_decimal(
        row.open_decision_count for row in report.rows
    ):
        raise ValueError("total_open_decisions must match rows")
    if report.average_queue_age_seconds != _average_decimal(
        row.queue_age_seconds for row in report.rows
    ):
        raise ValueError("average_queue_age_seconds must match rows")
    if report.average_assignment_lag_seconds != _average_decimal(
        row.assignment_lag_seconds for row in report.rows
    ):
        raise ValueError("average_assignment_lag_seconds must match rows")
    if report.average_reviewer_gap_ratio != _average_decimal(
        row.reviewer_gap_ratio for row in report.rows
    ):
        raise ValueError("average_reviewer_gap_ratio must match rows")
    if report.average_queue_load_ratio != _average_decimal(
        row.queue_load_ratio for row in report.rows
    ):
        raise ValueError("average_queue_load_ratio must match rows")
    if report.average_latency_score != _average_decimal(
        row.latency_score for row in report.rows
    ):
        raise ValueError("average_latency_score must match rows")
    if report.max_latency_score != max(
        (row.latency_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_latency_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_public_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public key")
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_STATUSES:
        raise ValueError(
            f"{field_name} must be one of "
            "RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_STATUSES",
        )
    return value


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as ctx:
        ctx.prec = _DECIMAL_CONTEXT_PREC
        return value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in _FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    if finished_at < started_at:
        raise ValueError("finished_at must be at or after started_at")
    delta = finished_at - started_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        return _ZERO
    with localcontext() as ctx:
        ctx.prec = _DECIMAL_CONTEXT_PREC
        return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    return _quantize(min(max(value, _ZERO), _ONE))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = _ZERO
    for value in values:  # type: ignore[assignment]
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _average_decimal(values: object) -> Decimal:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return _ZERO
    return _quantize(_sum_decimal(items) / _count(len(items)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = _DECIMAL_CONTEXT_PREC
        return value.quantize(_QUANT, rounding=ROUND_HALF_EVEN)


def _hash_private_ref(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _normalize_row_reason_codes(reason_codes: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        reason_codes,
        allowed=_ROW_REASON_CODE_SEQUENCE,
        label="row reason_codes",
    )


def _normalize_report_reason_codes(reason_codes: object) -> tuple[str, ...]:
    return _normalize_reason_codes(
        reason_codes,
        allowed=_REPORT_REASON_CODE_SEQUENCE,
        label="report reason_codes",
    )


def _normalize_reason_codes(
    reason_codes: object,
    *,
    allowed: tuple[str, ...],
    label: str,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{label} must be a sequence")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{label} must be a sequence") from exc
    if not normalized:
        raise ValueError(f"{label} must be non-empty")
    for code in normalized:
        if type(code) is not str or code not in allowed:
            raise ValueError(f"{label} contains an unsupported reason code")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicates")
    return tuple(sorted(normalized, key=allowed.index))


def _validate_payload(payload: dict[str, Any]) -> None:
    _validate_payload_schema(payload)
    _validate_payload_flags(payload)
    rows = payload.get("rows", ())
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _validate_payload_flags(row)
    for item in payload.get("reason_code_counts", ()):
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _validate_payload_flags(item)
    for row in rows:
        _validate_payload_digest(row)
    _validate_payload_digest(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_report_projection(payload)


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_fields("payload", payload, _REPORT_PAYLOAD_FIELDS)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain JSON objects")
        _require_payload_fields("payload row", row, _ROW_PAYLOAD_FIELDS)
        reason_codes = row["reason_codes"]
        if type(reason_codes) is not list:
            raise ValueError("row reason_codes must be a list")
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count in reason_code_counts:
        if type(count) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_payload_fields(
            "payload reason_code_counts",
            count,
            _REASON_CODE_COUNT_PAYLOAD_FIELDS,
        )


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    if set(payload) != set(expected_fields):
        raise ValueError(f"{label} fields must match public payload")


def _validate_payload_report_projection(payload: dict[str, Any]) -> None:
    config_version = _require_public_key("config_version", payload["config_version"])
    if (
        config_version
        != DEFAULT_RESEARCH_STRATEGY_TEAM_DECISION_QUEUE_LATENCY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    ResearchStrategyTeamDecisionQueueLatencyReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=config_version,
        status=_require_status("status", payload["status"]),
        queue_item_count=_payload_count_decimal(
            "queue_item_count",
            payload["queue_item_count"],
        ),
        pass_count=_payload_count_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_count_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_count_decimal("block_count", payload["block_count"]),
        total_open_decisions=_payload_count_decimal(
            "total_open_decisions",
            payload["total_open_decisions"],
        ),
        average_queue_age_seconds=_payload_nonnegative_decimal(
            "average_queue_age_seconds",
            payload["average_queue_age_seconds"],
        ),
        average_assignment_lag_seconds=_payload_nonnegative_decimal(
            "average_assignment_lag_seconds",
            payload["average_assignment_lag_seconds"],
        ),
        average_reviewer_gap_ratio=_payload_ratio_decimal(
            "average_reviewer_gap_ratio",
            payload["average_reviewer_gap_ratio"],
        ),
        average_queue_load_ratio=_payload_nonnegative_decimal(
            "average_queue_load_ratio",
            payload["average_queue_load_ratio"],
        ),
        average_latency_score=_payload_ratio_decimal(
            "average_latency_score",
            payload["average_latency_score"],
        ),
        max_latency_score=_payload_ratio_decimal(
            "max_latency_score",
            payload["max_latency_score"],
        ),
        rows=tuple(_payload_row(row) for row in payload["rows"]),
        reason_codes=tuple(payload["reason_codes"]),
        reason_code_counts=tuple(
            _payload_reason_code_count(item) for item in payload["reason_code_counts"]
        ),
        derived_validation_digest=_require_public_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _payload_row(payload: dict[str, Any]) -> ResearchStrategyTeamDecisionQueueLatencyRow:
    return ResearchStrategyTeamDecisionQueueLatencyRow(
        queue_item_hash=_require_public_digest("queue_item_hash", payload["queue_item_hash"]),
        team_key=_require_public_key("team_key", payload["team_key"]),
        decision_lane_key=_require_public_key(
            "decision_lane_key",
            payload["decision_lane_key"],
        ),
        status=_require_status("status", payload["status"]),
        queue_age_seconds=_payload_nonnegative_decimal(
            "queue_age_seconds",
            payload["queue_age_seconds"],
        ),
        assignment_lag_seconds=_payload_nonnegative_decimal(
            "assignment_lag_seconds",
            payload["assignment_lag_seconds"],
        ),
        required_reviewer_count=_payload_count_decimal(
            "required_reviewer_count",
            payload["required_reviewer_count"],
        ),
        available_reviewer_count=_payload_count_decimal(
            "available_reviewer_count",
            payload["available_reviewer_count"],
        ),
        reviewer_gap_ratio=_payload_ratio_decimal(
            "reviewer_gap_ratio",
            payload["reviewer_gap_ratio"],
        ),
        open_decision_count=_payload_count_decimal(
            "open_decision_count",
            payload["open_decision_count"],
        ),
        decision_capacity_count=_payload_count_decimal(
            "decision_capacity_count",
            payload["decision_capacity_count"],
        ),
        queue_load_ratio=_payload_nonnegative_decimal(
            "queue_load_ratio",
            payload["queue_load_ratio"],
        ),
        queue_load_pressure=_payload_ratio_decimal(
            "queue_load_pressure",
            payload["queue_load_pressure"],
        ),
        sla_breached_count=_payload_count_decimal(
            "sla_breached_count",
            payload["sla_breached_count"],
        ),
        sla_breach_ratio=_payload_ratio_decimal(
            "sla_breach_ratio",
            payload["sla_breach_ratio"],
        ),
        sla_breach_pressure=_payload_ratio_decimal(
            "sla_breach_pressure",
            payload["sla_breach_pressure"],
        ),
        rework_count=_payload_count_decimal("rework_count", payload["rework_count"]),
        rework_pressure=_payload_ratio_decimal(
            "rework_pressure",
            payload["rework_pressure"],
        ),
        escalation_pressure=_payload_ratio_decimal(
            "escalation_pressure",
            payload["escalation_pressure"],
        ),
        queue_age_pressure=_payload_ratio_decimal(
            "queue_age_pressure",
            payload["queue_age_pressure"],
        ),
        assignment_lag_pressure=_payload_ratio_decimal(
            "assignment_lag_pressure",
            payload["assignment_lag_pressure"],
        ),
        reviewer_gap_pressure=_payload_ratio_decimal(
            "reviewer_gap_pressure",
            payload["reviewer_gap_pressure"],
        ),
        latency_score=_payload_ratio_decimal(
            "latency_score",
            payload["latency_score"],
        ),
        reason_codes=tuple(payload["reason_codes"]),
        derived_validation_digest=_require_public_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _payload_reason_code_count(
    payload: dict[str, Any],
) -> ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount:
    return ResearchStrategyTeamDecisionQueueLatencyReasonCodeCount(
        reason_code=payload["reason_code"],
        count=_payload_count_decimal("count", payload["count"]),
        queue_item_ratio=_payload_ratio_decimal(
            "queue_item_ratio",
            payload["queue_item_ratio"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_count_decimal(field_name, _payload_decimal(field_name, value))


def _payload_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, _payload_decimal(field_name, value))


def _payload_ratio_decimal(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(field_name, _payload_decimal(field_name, value))


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not _PUBLIC_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public Decimal string")
    return _require_decimal(field_name, Decimal(value))


def _validate_payload_flags(value: dict[str, Any]) -> None:
    for flag_name in _FLAG_NAMES:
        if value.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _validate_payload_digest(value: dict[str, Any]) -> None:
    digest = value.get("derived_validation_digest")
    _require_public_digest("derived_validation_digest", digest)
    unsigned = dict(value)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    expected = sha256(encoded.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest must match payload")


def _public_digest_for_dataclass(value: object) -> str:
    if not is_dataclass(value):
        raise ValueError("value must be a dataclass")
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_text(key):
                raise ValueError(f"unsafe public payload key: {key}")
            if type(item) is int or type(item) is float:
                raise ValueError(f"{key} must be encoded as a string")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        if _has_unsafe_public_text(value):
            raise ValueError("unsafe public payload value")
        return value
    if type(value) is bool:
        return value
    if value is None:
        return None
    if type(value) is int or type(value) is float:
        raise ValueError("JSON numeric values must be encoded as strings")
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if _has_unsafe_public_text(field.name):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _has_unsafe_public_text(key):
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_public_text(value):
        raise ValueError(f"{label} contains unsafe public value")


def _has_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)
