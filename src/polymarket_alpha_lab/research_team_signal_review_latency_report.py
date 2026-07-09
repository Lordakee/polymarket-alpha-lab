"""Public-safe report-only summaries for team signal review latency."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_LATENCY_REPORT_CONFIG_VERSION = (
    "research-team-signal-review-latency-report-v0"
)
STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT_PREC = 64
_PUBLIC_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")

_SIGNAL_AGE_WEIGHT = Decimal("0.125000000000")
_REVIEWER_AVAILABILITY_WEIGHT = Decimal("0.180177746269")
_UNRESOLVED_DISSENT_WEIGHT = Decimal("0.200000000000")
_MEMORY_WRITEBACK_WEIGHT = Decimal("0.151125134328")
_QUEUE_PRESSURE_WEIGHT = Decimal("0.219824253731")
_MANUAL_ESCALATION_WEIGHT = Decimal("0.123872865672")

_PASS_REASON_CODE = "signal_review_latency_pass"
_EMPTY_REASON_CODE = "signal_review_latency_no_inputs"
_REPORT_BLOCK_REASON_CODE = "signal_review_latency_report_block_rows"
_REPORT_WATCH_REASON_CODE = "signal_review_latency_report_watch_rows"
_REPORT_PASS_REASON_CODE = "signal_review_latency_report_pass"
_ROW_REASON_CODE_SEQUENCE = (
    _PASS_REASON_CODE,
    "signal_age_watch",
    "signal_age_block",
    "reviewer_availability_watch",
    "reviewer_availability_block",
    "unresolved_dissent_watch",
    "unresolved_dissent_block",
    "memory_writeback_lag_watch",
    "memory_writeback_lag_block",
    "queue_pressure_watch",
    "queue_pressure_block",
    "manual_escalation_watch",
    "manual_escalation_block",
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
    "candidate",
    "candidates",
    "event",
    "market",
    "markets",
    "slug",
    "slugs",
    "question",
    "questions",
    "source",
    "sources",
    "url",
    "urls",
    "d" + "sn",
    "d" + "sns",
    "ta" + "ble",
    "ta" + "bles",
    "token",
    "tokens",
    "secret",
    "credential",
    "credentials",
    "password",
    "private_key",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "database_url",
    "wal" + "let",
    "wal" + "lets",
    "au" + "th",
    "or" + "der",
    "or" + "ders",
    "tr" + "ade",
    "tr" + "ades",
    "tr" + "ading",
    "li" + "ve",
    "bu" + "y",
    "bu" + "ys",
    "bu" + "ying",
    "se" + "ll",
    "se" + "lls",
    "se" + "lling",
    "recom" + "mendation",
    "recom" + "mendations",
    "siz" + "ing",
    "siz" + "ings",
    "position",
    "positions",
    "exec" + "ution",
    "exec" + "utions",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_LATENCY_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamSignalReviewLatencyConfig",
    "ResearchTeamSignalReviewLatencyInput",
    "ResearchTeamSignalReviewLatencyReasonCodeCount",
    "ResearchTeamSignalReviewLatencyReport",
    "ResearchTeamSignalReviewLatencyRow",
    "build_research_team_signal_review_latency_report",
    "research_team_signal_review_latency_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSignalReviewLatencyConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_LATENCY_REPORT_CONFIG_VERSION
    pass_latency_score_threshold: Decimal = Decimal("0.350000")
    block_latency_score_threshold: Decimal = Decimal("0.750000")
    watch_signal_age_seconds: Decimal = Decimal("3600.000000")
    block_signal_age_seconds: Decimal = Decimal("7200.000000")
    watch_min_reviewer_availability_ratio: Decimal = Decimal("0.600000")
    block_min_reviewer_availability_ratio: Decimal = Decimal("0.300000")
    watch_unresolved_dissent_ratio: Decimal = Decimal("0.200000")
    block_unresolved_dissent_ratio: Decimal = Decimal("0.500000")
    watch_memory_writeback_lag_seconds: Decimal = Decimal("3600.000000")
    block_memory_writeback_lag_seconds: Decimal = Decimal("7200.000000")
    watch_queue_pressure_ratio: Decimal = Decimal("0.750000")
    block_queue_pressure_ratio: Decimal = Decimal("1.250000")
    watch_manual_escalation_urgency: Decimal = Decimal("0.300000")
    block_manual_escalation_urgency: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewLatencyConfig:
            raise TypeError("ResearchTeamSignalReviewLatencyConfig subclass is not allowed")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewLatencyConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_key("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SIGNAL_REVIEW_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_latency_score_threshold",
            "block_latency_score_threshold",
            "watch_min_reviewer_availability_ratio",
            "block_min_reviewer_availability_ratio",
            "watch_unresolved_dissent_ratio",
            "block_unresolved_dissent_ratio",
            "watch_manual_escalation_urgency",
            "block_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_signal_age_seconds",
            "block_signal_age_seconds",
            "watch_memory_writeback_lag_seconds",
            "block_memory_writeback_lag_seconds",
            "watch_queue_pressure_ratio",
            "block_queue_pressure_ratio",
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
class ResearchTeamSignalReviewLatencyInput:
    team_key: str
    review_lane_key: str
    pending_signal_count: Decimal
    required_reviewer_count: Decimal
    available_reviewer_count: Decimal
    mean_signal_age_seconds: Decimal
    unresolved_dissent_count: Decimal
    memory_writeback_lag_seconds: Decimal
    pending_review_queue_count: Decimal
    review_queue_capacity_count: Decimal
    manual_escalation_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewLatencyInput:
            raise TypeError("ResearchTeamSignalReviewLatencyInput subclass is not allowed")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewLatencyInput, "input")
        object.__setattr__(
            self,
            "team_key",
            _require_public_key("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "review_lane_key",
            _require_public_key("review_lane_key", self.review_lane_key),
        )
        for field_name in (
            "pending_signal_count",
            "required_reviewer_count",
            "available_reviewer_count",
            "unresolved_dissent_count",
            "pending_review_queue_count",
            "review_queue_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_reviewer_count <= _ZERO:
            raise ValueError("required_reviewer_count must be positive")
        if self.review_queue_capacity_count <= _ZERO:
            raise ValueError("review_queue_capacity_count must be positive")
        if self.available_reviewer_count > self.required_reviewer_count:
            raise ValueError(
                "available_reviewer_count must be at most required_reviewer_count",
            )
        if self.unresolved_dissent_count > self.pending_signal_count:
            raise ValueError(
                "unresolved_dissent_count must be at most pending_signal_count",
            )
        for field_name in ("mean_signal_age_seconds", "memory_writeback_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_escalation_urgency",
            _require_ratio_decimal(
                "manual_escalation_urgency",
                self.manual_escalation_urgency,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamSignalReviewLatencyRow:
    team_key: str
    review_lane_key: str
    status: str
    pending_signal_count: Decimal
    required_reviewer_count: Decimal
    available_reviewer_count: Decimal
    reviewer_availability_ratio: Decimal
    mean_signal_age_seconds: Decimal
    signal_age_pressure: Decimal
    unresolved_dissent_count: Decimal
    unresolved_dissent_ratio: Decimal
    unresolved_dissent_pressure: Decimal
    memory_writeback_lag_seconds: Decimal
    memory_writeback_lag_pressure: Decimal
    pending_review_queue_count: Decimal
    review_queue_capacity_count: Decimal
    queue_pressure_ratio: Decimal
    queue_pressure_load: Decimal
    manual_escalation_urgency: Decimal
    manual_escalation_pressure: Decimal
    reviewer_availability_gap_pressure: Decimal
    latency_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewLatencyRow:
            raise TypeError("ResearchTeamSignalReviewLatencyRow subclass is not allowed")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewLatencyRow, "row")
        object.__setattr__(
            self,
            "team_key",
            _require_public_key("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "review_lane_key",
            _require_public_key("review_lane_key", self.review_lane_key),
        )
        _require_status("status", self.status)
        for field_name in (
            "pending_signal_count",
            "required_reviewer_count",
            "available_reviewer_count",
            "unresolved_dissent_count",
            "pending_review_queue_count",
            "review_queue_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_reviewer_count <= _ZERO:
            raise ValueError("required_reviewer_count must be positive")
        if self.review_queue_capacity_count <= _ZERO:
            raise ValueError("review_queue_capacity_count must be positive")
        for field_name in (
            "reviewer_availability_ratio",
            "signal_age_pressure",
            "unresolved_dissent_ratio",
            "unresolved_dissent_pressure",
            "memory_writeback_lag_pressure",
            "queue_pressure_load",
            "manual_escalation_urgency",
            "manual_escalation_pressure",
            "reviewer_availability_gap_pressure",
            "latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_signal_age_seconds",
            "memory_writeback_lag_seconds",
            "queue_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSignalReviewLatencyReasonCodeCount:
    reason_code: str
    count: Decimal
    review_group_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewLatencyReasonCodeCount:
            raise TypeError(
                "ResearchTeamSignalReviewLatencyReasonCodeCount subclass is not allowed",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSignalReviewLatencyReasonCodeCount,
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
            "review_group_ratio",
            _require_ratio_decimal("review_group_ratio", self.review_group_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSignalReviewLatencyReport:
    generated_at: datetime
    config_version: str
    status: str
    review_group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_pending_signals: Decimal
    total_pending_review_queue: Decimal
    average_signal_age_seconds: Decimal
    average_reviewer_availability_ratio: Decimal
    average_unresolved_dissent_ratio: Decimal
    average_memory_writeback_lag_seconds: Decimal
    average_queue_pressure_ratio: Decimal
    max_manual_escalation_urgency: Decimal
    max_latency_score: Decimal
    rows: tuple[ResearchTeamSignalReviewLatencyRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamSignalReviewLatencyReasonCodeCount, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamSignalReviewLatencyReport:
            raise TypeError("ResearchTeamSignalReviewLatencyReport subclass is not allowed")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSignalReviewLatencyReport, "report")
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
            "review_group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_pending_signals",
            "total_pending_review_queue",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_signal_age_seconds",
            "average_reviewer_availability_ratio",
            "average_unresolved_dissent_ratio",
            "average_memory_writeback_lag_seconds",
            "average_queue_pressure_ratio",
            "max_manual_escalation_urgency",
            "max_latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reviewer_availability_ratio",
            "average_unresolved_dissent_ratio",
            "max_manual_escalation_urgency",
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
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        else:
            _require_public_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")


def build_research_team_signal_review_latency_report(
    inputs: Sequence[ResearchTeamSignalReviewLatencyInput],
    *,
    config: ResearchTeamSignalReviewLatencyConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamSignalReviewLatencyReport:
    cfg = config or ResearchTeamSignalReviewLatencyConfig()
    if type(cfg) is not ResearchTeamSignalReviewLatencyConfig:
        raise ValueError("config must be a ResearchTeamSignalReviewLatencyConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, cfg) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamSignalReviewLatencyReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_report_status(rows),
        review_group_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        total_pending_signals=_sum_decimal(row.pending_signal_count for row in rows),
        total_pending_review_queue=_sum_decimal(
            row.pending_review_queue_count for row in rows
        ),
        average_signal_age_seconds=_average_decimal(
            row.mean_signal_age_seconds for row in rows
        ),
        average_reviewer_availability_ratio=_average_decimal(
            row.reviewer_availability_ratio for row in rows
        ),
        average_unresolved_dissent_ratio=_average_decimal(
            row.unresolved_dissent_ratio for row in rows
        ),
        average_memory_writeback_lag_seconds=_average_decimal(
            row.memory_writeback_lag_seconds for row in rows
        ),
        average_queue_pressure_ratio=_average_decimal(
            row.queue_pressure_ratio for row in rows
        ),
        max_manual_escalation_urgency=max(
            (row.manual_escalation_urgency for row in rows),
            default=_ZERO,
        ),
        max_latency_score=max((row.latency_score for row in rows), default=_ZERO),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_team_signal_review_latency_report_payload(
    report: ResearchTeamSignalReviewLatencyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSignalReviewLatencyReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_statuses(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_payload_flags(payload)
        _validate_payload_statuses(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError("report must be a ResearchTeamSignalReviewLatencyReport or payload")


def _row_from_input(
    item: ResearchTeamSignalReviewLatencyInput,
    config: ResearchTeamSignalReviewLatencyConfig,
) -> ResearchTeamSignalReviewLatencyRow:
    reviewer_availability_ratio = _ratio_or_zero(
        item.available_reviewer_count,
        item.required_reviewer_count,
    )
    unresolved_dissent_ratio = _ratio_or_zero(
        item.unresolved_dissent_count,
        item.pending_signal_count,
    )
    queue_pressure_ratio = _ratio_or_zero(
        item.pending_review_queue_count,
        item.review_queue_capacity_count,
    )
    signal_age_pressure = _clamp_ratio(
        item.mean_signal_age_seconds / config.block_signal_age_seconds,
    )
    unresolved_dissent_pressure = _clamp_ratio(
        unresolved_dissent_ratio / config.block_unresolved_dissent_ratio,
    )
    memory_writeback_lag_pressure = _clamp_ratio(
        item.memory_writeback_lag_seconds / config.block_memory_writeback_lag_seconds,
    )
    queue_pressure_load = _clamp_ratio(
        queue_pressure_ratio / config.block_queue_pressure_ratio,
    )
    manual_escalation_pressure = _clamp_ratio(
        item.manual_escalation_urgency / config.block_manual_escalation_urgency,
    )
    reviewer_availability_gap_pressure = _reviewer_availability_gap_pressure(
        reviewer_availability_ratio,
        config,
    )
    latency_score = _latency_score(
        signal_age_pressure=signal_age_pressure,
        reviewer_availability_gap_pressure=reviewer_availability_gap_pressure,
        unresolved_dissent_pressure=unresolved_dissent_pressure,
        memory_writeback_lag_pressure=memory_writeback_lag_pressure,
        queue_pressure_load=queue_pressure_load,
        manual_escalation_pressure=manual_escalation_pressure,
    )
    status = _score_status(latency_score, config)
    return ResearchTeamSignalReviewLatencyRow(
        team_key=item.team_key,
        review_lane_key=item.review_lane_key,
        status=status,
        pending_signal_count=item.pending_signal_count,
        required_reviewer_count=item.required_reviewer_count,
        available_reviewer_count=item.available_reviewer_count,
        reviewer_availability_ratio=reviewer_availability_ratio,
        mean_signal_age_seconds=item.mean_signal_age_seconds,
        signal_age_pressure=signal_age_pressure,
        unresolved_dissent_count=item.unresolved_dissent_count,
        unresolved_dissent_ratio=unresolved_dissent_ratio,
        unresolved_dissent_pressure=unresolved_dissent_pressure,
        memory_writeback_lag_seconds=item.memory_writeback_lag_seconds,
        memory_writeback_lag_pressure=memory_writeback_lag_pressure,
        pending_review_queue_count=item.pending_review_queue_count,
        review_queue_capacity_count=item.review_queue_capacity_count,
        queue_pressure_ratio=queue_pressure_ratio,
        queue_pressure_load=queue_pressure_load,
        manual_escalation_urgency=item.manual_escalation_urgency,
        manual_escalation_pressure=manual_escalation_pressure,
        reviewer_availability_gap_pressure=reviewer_availability_gap_pressure,
        latency_score=latency_score,
        reason_codes=_row_reason_codes(item, config),
    )


def _row_reason_codes(
    item: ResearchTeamSignalReviewLatencyInput,
    config: ResearchTeamSignalReviewLatencyConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    reviewer_availability_ratio = _ratio_or_zero(
        item.available_reviewer_count,
        item.required_reviewer_count,
    )
    unresolved_dissent_ratio = _ratio_or_zero(
        item.unresolved_dissent_count,
        item.pending_signal_count,
    )
    queue_pressure_ratio = _ratio_or_zero(
        item.pending_review_queue_count,
        item.review_queue_capacity_count,
    )
    _append_metric_reason(
        codes,
        "signal_age",
        _metric_status_above(
            item.mean_signal_age_seconds,
            config.watch_signal_age_seconds,
            config.block_signal_age_seconds,
        ),
    )
    _append_metric_reason(
        codes,
        "reviewer_availability",
        _metric_status_below(
            reviewer_availability_ratio,
            config.watch_min_reviewer_availability_ratio,
            config.block_min_reviewer_availability_ratio,
        ),
    )
    _append_metric_reason(
        codes,
        "unresolved_dissent",
        _metric_status_above(
            unresolved_dissent_ratio,
            config.watch_unresolved_dissent_ratio,
            config.block_unresolved_dissent_ratio,
        ),
    )
    _append_metric_reason(
        codes,
        "memory_writeback_lag",
        _metric_status_above(
            item.memory_writeback_lag_seconds,
            config.watch_memory_writeback_lag_seconds,
            config.block_memory_writeback_lag_seconds,
        ),
    )
    _append_metric_reason(
        codes,
        "queue_pressure",
        _metric_status_above(
            queue_pressure_ratio,
            config.watch_queue_pressure_ratio,
            config.block_queue_pressure_ratio,
        ),
    )
    _append_metric_reason(
        codes,
        "manual_escalation",
        _metric_status_above(
            item.manual_escalation_urgency,
            config.watch_manual_escalation_urgency,
            config.block_manual_escalation_urgency,
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


def _metric_status_below(
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value <= block_threshold:
        return "block"
    if value < watch_threshold:
        return "watch"
    return "pass"


def _reviewer_availability_gap_pressure(
    reviewer_availability_ratio: Decimal,
    config: ResearchTeamSignalReviewLatencyConfig,
) -> Decimal:
    if reviewer_availability_ratio >= config.watch_min_reviewer_availability_ratio:
        return _ZERO
    if reviewer_availability_ratio <= config.block_min_reviewer_availability_ratio:
        return _ONE
    return _clamp_ratio(
        (config.watch_min_reviewer_availability_ratio - reviewer_availability_ratio)
        / (
            config.watch_min_reviewer_availability_ratio
            - config.block_min_reviewer_availability_ratio
        ),
    )


def _latency_score(
    *,
    signal_age_pressure: Decimal,
    reviewer_availability_gap_pressure: Decimal,
    unresolved_dissent_pressure: Decimal,
    memory_writeback_lag_pressure: Decimal,
    queue_pressure_load: Decimal,
    manual_escalation_pressure: Decimal,
) -> Decimal:
    return _clamp_ratio(
        signal_age_pressure * _SIGNAL_AGE_WEIGHT
        + reviewer_availability_gap_pressure * _REVIEWER_AVAILABILITY_WEIGHT
        + unresolved_dissent_pressure * _UNRESOLVED_DISSENT_WEIGHT
        + memory_writeback_lag_pressure * _MEMORY_WRITEBACK_WEIGHT
        + queue_pressure_load * _QUEUE_PRESSURE_WEIGHT
        + manual_escalation_pressure * _MANUAL_ESCALATION_WEIGHT,
    )


def _score_status(score: Decimal, config: ResearchTeamSignalReviewLatencyConfig) -> str:
    if score >= config.block_latency_score_threshold:
        return "block"
    if score > config.pass_latency_score_threshold:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Sequence[ResearchTeamSignalReviewLatencyInput],
) -> tuple[ResearchTeamSignalReviewLatencyInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized = tuple(inputs)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchTeamSignalReviewLatencyInput:
            raise ValueError("inputs must contain ResearchTeamSignalReviewLatencyInput")
        key = (item.team_key, item.review_lane_key)
        if key in seen:
            raise ValueError("duplicate team_key/review_lane_key")
        seen.add(key)
    return tuple(sorted(normalized, key=lambda item: (item.team_key, item.review_lane_key)))


def _normalize_rows(rows: object) -> tuple[ResearchTeamSignalReviewLatencyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamSignalReviewLatencyRow")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain ResearchTeamSignalReviewLatencyRow") from exc
    for row in normalized:
        if type(row) is not ResearchTeamSignalReviewLatencyRow:
            raise ValueError("rows must contain ResearchTeamSignalReviewLatencyRow")
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchTeamSignalReviewLatencyReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError(
            "reason_code_counts must contain ResearchTeamSignalReviewLatencyReasonCodeCount",
        )
    try:
        normalized = tuple(counts)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "reason_code_counts must contain ResearchTeamSignalReviewLatencyReasonCodeCount",
        ) from exc
    for count in normalized:
        if type(count) is not ResearchTeamSignalReviewLatencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchTeamSignalReviewLatencyReasonCodeCount",
            )
    return tuple(sorted(normalized, key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code)))


def _row_sort_key(row: ResearchTeamSignalReviewLatencyRow) -> tuple[int, Decimal, str, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (status_rank[row.status], -row.latency_score, row.team_key, row.review_lane_key)


def _report_status(rows: tuple[ResearchTeamSignalReviewLatencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(rows: tuple[ResearchTeamSignalReviewLatencyRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_reason_codes(rows: tuple[ResearchTeamSignalReviewLatencyRow, ...]) -> tuple[str, ...]:
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
    rows: tuple[ResearchTeamSignalReviewLatencyRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamSignalReviewLatencyReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    counter.update(report_reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamSignalReviewLatencyReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            review_group_ratio=_ratio_or_zero(_count(count), row_count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: _REASON_CODE_SEQUENCE.index(item[0]),
        )
    )


def _validate_config(config: ResearchTeamSignalReviewLatencyConfig) -> None:
    if config.pass_latency_score_threshold > config.block_latency_score_threshold:
        raise ValueError(
            "pass_latency_score_threshold must be at most block_latency_score_threshold",
        )
    _require_threshold_pair(
        "watch_signal_age_seconds",
        config.watch_signal_age_seconds,
        "block_signal_age_seconds",
        config.block_signal_age_seconds,
    )
    _require_threshold_pair(
        "watch_unresolved_dissent_ratio",
        config.watch_unresolved_dissent_ratio,
        "block_unresolved_dissent_ratio",
        config.block_unresolved_dissent_ratio,
    )
    _require_threshold_pair(
        "watch_memory_writeback_lag_seconds",
        config.watch_memory_writeback_lag_seconds,
        "block_memory_writeback_lag_seconds",
        config.block_memory_writeback_lag_seconds,
    )
    _require_threshold_pair(
        "watch_queue_pressure_ratio",
        config.watch_queue_pressure_ratio,
        "block_queue_pressure_ratio",
        config.block_queue_pressure_ratio,
    )
    _require_threshold_pair(
        "watch_manual_escalation_urgency",
        config.watch_manual_escalation_urgency,
        "block_manual_escalation_urgency",
        config.block_manual_escalation_urgency,
    )
    if (
        config.block_min_reviewer_availability_ratio
        > config.watch_min_reviewer_availability_ratio
    ):
        raise ValueError(
            "block_min_reviewer_availability_ratio must be at most "
            "watch_min_reviewer_availability_ratio",
        )


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_name} must be at most {block_name}")


def _validate_row(row: ResearchTeamSignalReviewLatencyRow) -> None:
    if row.available_reviewer_count > row.required_reviewer_count:
        raise ValueError(
            "available_reviewer_count must be at most required_reviewer_count",
        )
    if row.unresolved_dissent_count > row.pending_signal_count:
        raise ValueError(
            "unresolved_dissent_count must be at most pending_signal_count",
        )
    if row.reviewer_availability_ratio != _ratio_or_zero(
        row.available_reviewer_count,
        row.required_reviewer_count,
    ):
        raise ValueError("reviewer_availability_ratio must match reviewer counts")
    if row.unresolved_dissent_ratio != _ratio_or_zero(
        row.unresolved_dissent_count,
        row.pending_signal_count,
    ):
        raise ValueError("unresolved_dissent_ratio must match signal counts")
    if row.queue_pressure_ratio != _ratio_or_zero(
        row.pending_review_queue_count,
        row.review_queue_capacity_count,
    ):
        raise ValueError("queue_pressure_ratio must match queue counts")
    expected_score = _latency_score(
        signal_age_pressure=row.signal_age_pressure,
        reviewer_availability_gap_pressure=row.reviewer_availability_gap_pressure,
        unresolved_dissent_pressure=row.unresolved_dissent_pressure,
        memory_writeback_lag_pressure=row.memory_writeback_lag_pressure,
        queue_pressure_load=row.queue_pressure_load,
        manual_escalation_pressure=row.manual_escalation_pressure,
    )
    if row.latency_score != expected_score:
        raise ValueError("latency_score must match pressure components")
    if row.status == "pass" and row.reason_codes != (_PASS_REASON_CODE,):
        raise ValueError("reason_codes must match status")
    if row.status != "pass" and row.reason_codes == (_PASS_REASON_CODE,):
        raise ValueError("reason_codes must match status")


def _validate_report(report: ResearchTeamSignalReviewLatencyReport) -> None:
    rows = report.rows
    if report.review_group_count != _count(len(rows)):
        raise ValueError("review_group_count must match rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.total_pending_signals != _sum_decimal(row.pending_signal_count for row in rows):
        raise ValueError("total_pending_signals must match rows")
    if report.total_pending_review_queue != _sum_decimal(
        row.pending_review_queue_count for row in rows
    ):
        raise ValueError("total_pending_review_queue must match rows")
    if report.average_signal_age_seconds != _average_decimal(
        row.mean_signal_age_seconds for row in rows
    ):
        raise ValueError("average_signal_age_seconds must match rows")
    if report.average_reviewer_availability_ratio != _average_decimal(
        row.reviewer_availability_ratio for row in rows
    ):
        raise ValueError("average_reviewer_availability_ratio must match rows")
    if report.average_unresolved_dissent_ratio != _average_decimal(
        row.unresolved_dissent_ratio for row in rows
    ):
        raise ValueError("average_unresolved_dissent_ratio must match rows")
    if report.average_memory_writeback_lag_seconds != _average_decimal(
        row.memory_writeback_lag_seconds for row in rows
    ):
        raise ValueError("average_memory_writeback_lag_seconds must match rows")
    if report.average_queue_pressure_ratio != _average_decimal(
        row.queue_pressure_ratio for row in rows
    ):
        raise ValueError("average_queue_pressure_ratio must match rows")
    if report.max_manual_escalation_urgency != max(
        (row.manual_escalation_urgency for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_manual_escalation_urgency must match rows")
    if report.max_latency_score != max((row.latency_score for row in rows), default=_ZERO):
        raise ValueError("max_latency_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _ROW_REASON_CODE_SEQUENCE)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value, _REPORT_REASON_CODE_SEQUENCE)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in allowed:
            raise ValueError("reason_code must be a supported public reason code")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=allowed.index))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank str")
    if _PUBLIC_KEY_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public aggregate key")
    _reject_unsafe_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public sha256 digest")


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(_COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must set {field_name}=True")


def _validate_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in _FLAG_NAMES:
        if field_name not in payload or payload[field_name] is not True:
            raise ValueError(f"payload must set {field_name}=True")
    _validate_nested_payload_flags("payload", payload)


def _validate_nested_payload_flags(path: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            nested_path = f"{path}.{key}"
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _validate_nested_payload_flags(nested_path, item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_nested_payload_flags(f"{path}[{index}]", item)


def _validate_payload_statuses(value: object, path: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            nested_path = f"{path}.{key}"
            if key == "status":
                _require_status(nested_path, item)
            _validate_payload_statuses(item, nested_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_statuses(item, f"{path}[{index}]")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == "public_digest":
                continue
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key == "public_digest":
                continue
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(_unsafe_term_matches(lowered, term) for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(
            f"{field_name} must not expose raw identifiers in private public payload",
        )


def _unsafe_term_matches(value: str, term: str) -> bool:
    if "://" in term or "_" in term:
        return term in value
    return re.search(rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)", value) is not None


def _public_digest_for_report(report: ResearchTeamSignalReviewLatencyReport) -> str:
    values = asdict(report)
    values.pop("public_digest", None)
    return _public_digest(values)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest: object = None
    if "public_digest" in payload:
        digest = payload["public_digest"]
    _require_public_digest("public_digest", digest)
    values = dict(payload)
    values.pop("public_digest", None)
    expected = _public_digest(values)
    if digest != expected:
        raise ValueError("public_digest must match payload")


def _public_digest(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return f"{value:.6f}"
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if isinstance(value, float):
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str or type(value) is bool or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _sum_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    total = _ZERO
    for value in values:
        total = _decimal(total + value)
    return total


def _average_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return _decimal(_sum_decimal(normalized) / Decimal(len(normalized)))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _decimal(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _decimal(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = _DECIMAL_CONTEXT_PREC
        context.rounding = ROUND_HALF_UP
        return value.quantize(_QUANT)
