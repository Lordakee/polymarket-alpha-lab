"""Public-safe basketball event specialist memory readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_BASKETBALL_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "REASON_CODES",
    "STATUSES",
    "ResearchBasketballEventTeamMemoryReportConfig",
    "ResearchBasketballEventTeamMemorySignal",
    "ResearchBasketballEventTeamMemoryRow",
    "ResearchBasketballEventTeamMemoryReasonCodeCount",
    "ResearchBasketballEventTeamMemoryReport",
    "build_research_basketball_event_team_memory_report",
    "research_basketball_event_team_memory_report_payload",
)


DEFAULT_RESEARCH_BASKETBALL_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-basketball-event-team-memory-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NEXT_STEP_BY_STATUS = {
    "pass": "monitor_basketball_specialist_memory",
    "watch": "review_basketball_specialist_memory_freshness",
    "block": "refresh_basketball_specialist_memory_before_research",
}

INPUT_REASON_CODES = ("basketball_memory_signal_observed",)
STATUS_REASON_CODES = (
    "basketball_event_team_memory_status_pass",
    "basketball_event_team_memory_status_watch",
    "basketball_event_team_memory_status_block",
)
REPORT_REASON_CODES = (
    "basketball_event_team_memory_report_pass",
    "basketball_event_team_memory_report_watch",
    "basketball_event_team_memory_report_block",
    "basketball_event_team_memory_report_empty",
)
BLOCK_REASON_CODES = (
    "specialist_memory_score_block",
    "lineup_memory_coverage_block",
    "rotation_memory_coverage_block",
    "evidence_recency_score_block",
    "evidence_age_block",
)
WATCH_REASON_CODES = (
    "specialist_memory_score_watch",
    "lineup_memory_coverage_watch",
    "rotation_memory_coverage_watch",
    "evidence_recency_score_watch",
    "evidence_age_watch",
)
MEMORY_BLOCK_REASON_CODES = BLOCK_REASON_CODES[:3]
MEMORY_WATCH_REASON_CODES = WATCH_REASON_CODES[:3]
EVIDENCE_BLOCK_REASON_CODES = BLOCK_REASON_CODES[3:]
EVIDENCE_WATCH_REASON_CODES = WATCH_REASON_CODES[3:]
METRIC_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES
REASON_CODES = (
    *INPUT_REASON_CODES,
    *STATUS_REASON_CODES,
    *REPORT_REASON_CODES,
    *METRIC_REASON_CODES,
)
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "event_id",
        "market",
        "condition_id",
        "token_id",
        "game_id",
        "team_id",
        "team_name",
        "source",
        "raw_text",
        "url",
        "://",
        "www.",
        "http",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "database",
        "network",
        "broker",
        "execution",
        "persist",
        "mutation",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchBasketballEventTeamMemoryReportConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_BASKETBALL_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    )
    pass_min_specialist_memory_score: Decimal = Decimal("0.850000")
    watch_min_specialist_memory_score: Decimal = Decimal("0.600000")
    pass_min_lineup_memory_coverage_ratio: Decimal = Decimal("0.800000")
    watch_min_lineup_memory_coverage_ratio: Decimal = Decimal("0.600000")
    pass_min_rotation_memory_coverage_ratio: Decimal = Decimal("0.800000")
    watch_min_rotation_memory_coverage_ratio: Decimal = Decimal("0.600000")
    pass_min_evidence_recency_score: Decimal = Decimal("0.800000")
    watch_min_evidence_recency_score: Decimal = Decimal("0.500000")
    pass_max_latest_evidence_age_seconds: Decimal = Decimal("21600.000000")
    watch_max_latest_evidence_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchBasketballEventTeamMemoryReportConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_BASKETBALL_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_specialist_memory_score",
            "watch_min_specialist_memory_score",
            "pass_min_lineup_memory_coverage_ratio",
            "watch_min_lineup_memory_coverage_ratio",
            "pass_min_rotation_memory_coverage_ratio",
            "watch_min_rotation_memory_coverage_ratio",
            "pass_min_evidence_recency_score",
            "watch_min_evidence_recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_max_latest_evidence_age_seconds",
            "watch_max_latest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchBasketballEventTeamMemorySignal(_FinalPublicDataclass):
    basketball_context_bucket: str
    memory_cohort_bucket: str
    specialist_memory_score: Decimal
    lineup_memory_coverage_ratio: Decimal
    rotation_memory_coverage_ratio: Decimal
    fresh_evidence_packet_count: Decimal
    total_evidence_packet_count: Decimal
    latest_evidence_age_seconds: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = INPUT_REASON_CODES
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchBasketballEventTeamMemorySignal, "signal")
        _require_public_bucket("basketball_context_bucket", self.basketball_context_bucket)
        _require_public_bucket("memory_cohort_bucket", self.memory_cohort_bucket)
        for field_name in (
            "specialist_memory_score",
            "lineup_memory_coverage_ratio",
            "rotation_memory_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_evidence_packet_count",
            "total_evidence_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_evidence_packet_count > self.total_evidence_packet_count:
            raise ValueError("fresh_evidence_packet_count must be at most total")
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _require_nonnegative_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                self.reason_codes,
                supported=INPUT_REASON_CODES,
                require_nonempty=True,
            ),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchBasketballEventTeamMemoryRow(_FinalPublicDataclass):
    basketball_context_bucket: str
    memory_cohort_bucket: str
    memory_status: str
    specialist_memory_score: Decimal
    lineup_memory_coverage_ratio: Decimal
    rotation_memory_coverage_ratio: Decimal
    fresh_evidence_packet_count: Decimal
    total_evidence_packet_count: Decimal
    evidence_recency_score: Decimal
    latest_evidence_age_seconds: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchBasketballEventTeamMemoryRow, "row")
        _require_public_bucket("basketball_context_bucket", self.basketball_context_bucket)
        _require_public_bucket("memory_cohort_bucket", self.memory_cohort_bucket)
        _require_status("memory_status", self.memory_status)
        for field_name in (
            "specialist_memory_score",
            "lineup_memory_coverage_ratio",
            "rotation_memory_coverage_ratio",
            "evidence_recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_evidence_packet_count",
            "total_evidence_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_evidence_packet_count > self.total_evidence_packet_count:
            raise ValueError("fresh_evidence_packet_count must be at most total")
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _require_nonnegative_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                self.reason_codes,
                supported=REASON_CODES,
                require_nonempty=True,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchBasketballEventTeamMemoryReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    signal_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchBasketballEventTeamMemoryReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "signal_ratio",
            _require_ratio_decimal("signal_ratio", self.signal_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchBasketballEventTeamMemoryReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    memory_readiness_status: str
    evidence_recency_status: str
    recommended_next_step: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_specialist_memory_score: Decimal
    average_lineup_memory_coverage_ratio: Decimal
    average_rotation_memory_coverage_ratio: Decimal
    fresh_evidence_packet_count: Decimal
    total_evidence_packet_count: Decimal
    aggregate_evidence_recency_score: Decimal
    max_latest_evidence_age_seconds: Decimal
    rows: tuple[ResearchBasketballEventTeamMemoryRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchBasketballEventTeamMemoryReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchBasketballEventTeamMemoryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_BASKETBALL_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "report_status",
            "memory_readiness_status",
            "evidence_recency_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.report_status]:
            raise ValueError("recommended_next_step must match report_status")
        for field_name in (
            "signal_count",
            "pass_count",
            "watch_count",
            "block_count",
            "fresh_evidence_packet_count",
            "total_evidence_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_specialist_memory_score",
            "average_lineup_memory_coverage_ratio",
            "average_rotation_memory_coverage_ratio",
            "aggregate_evidence_recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_evidence_age_seconds",
            _require_nonnegative_decimal(
                "max_latest_evidence_age_seconds",
                self.max_latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_basketball_event_team_memory_report_payload(self)


def build_research_basketball_event_team_memory_report(
    signals: Iterable[ResearchBasketballEventTeamMemorySignal],
    *,
    config: ResearchBasketballEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> ResearchBasketballEventTeamMemoryReport:
    if type(config) is not ResearchBasketballEventTeamMemoryReportConfig:
        raise ValueError("config must be a ResearchBasketballEventTeamMemoryReportConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signal(
                    signal,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    memory_readiness_status = _memory_readiness_status(rows)
    evidence_recency_status = _evidence_recency_status(rows)
    report_status = _rollup_status((memory_readiness_status, evidence_recency_status))
    return ResearchBasketballEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        memory_readiness_status=memory_readiness_status,
        evidence_recency_status=evidence_recency_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[report_status],
        signal_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_specialist_memory_score=_average(
            tuple(row.specialist_memory_score for row in rows),
        ),
        average_lineup_memory_coverage_ratio=_average(
            tuple(row.lineup_memory_coverage_ratio for row in rows),
        ),
        average_rotation_memory_coverage_ratio=_average(
            tuple(row.rotation_memory_coverage_ratio for row in rows),
        ),
        fresh_evidence_packet_count=_sum_decimal(
            tuple(row.fresh_evidence_packet_count for row in rows),
            count=True,
        ),
        total_evidence_packet_count=_sum_decimal(
            tuple(row.total_evidence_packet_count for row in rows),
            count=True,
        ),
        aggregate_evidence_recency_score=_ratio(
            _sum_decimal(tuple(row.fresh_evidence_packet_count for row in rows), count=True),
            _sum_decimal(tuple(row.total_evidence_packet_count for row in rows), count=True),
        ),
        max_latest_evidence_age_seconds=_max_decimal(
            tuple(row.latest_evidence_age_seconds for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
    )


def research_basketball_event_team_memory_report_payload(
    report: ResearchBasketballEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchBasketballEventTeamMemoryReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest must match report payload")
        _validate_report(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest must match report payload")
        return payload
    raise ValueError("report must be a ResearchBasketballEventTeamMemoryReport")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_signals(
    signals: Iterable[ResearchBasketballEventTeamMemorySignal],
) -> tuple[ResearchBasketballEventTeamMemorySignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not ResearchBasketballEventTeamMemorySignal:
            raise ValueError(
                "signals must contain ResearchBasketballEventTeamMemorySignal",
            )
        _require_hard_flags("signal", signal)
        key = (signal.basketball_context_bucket, signal.memory_cohort_bucket)
        if key in seen:
            raise ValueError("signals must contain unique public bucket pairs")
        seen.add(key)
    return normalized


def _row_from_signal(
    signal: ResearchBasketballEventTeamMemorySignal,
    *,
    config: ResearchBasketballEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> ResearchBasketballEventTeamMemoryRow:
    if signal.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    evidence_recency_score = _ratio(
        signal.fresh_evidence_packet_count,
        signal.total_evidence_packet_count,
    )
    metric_reasons = _metric_reason_codes(
        signal,
        evidence_recency_score=evidence_recency_score,
        config=config,
    )
    status = _row_status(metric_reasons)
    return ResearchBasketballEventTeamMemoryRow(
        basketball_context_bucket=signal.basketball_context_bucket,
        memory_cohort_bucket=signal.memory_cohort_bucket,
        memory_status=status,
        specialist_memory_score=signal.specialist_memory_score,
        lineup_memory_coverage_ratio=signal.lineup_memory_coverage_ratio,
        rotation_memory_coverage_ratio=signal.rotation_memory_coverage_ratio,
        fresh_evidence_packet_count=signal.fresh_evidence_packet_count,
        total_evidence_packet_count=signal.total_evidence_packet_count,
        evidence_recency_score=evidence_recency_score,
        latest_evidence_age_seconds=signal.latest_evidence_age_seconds,
        observed_at=signal.observed_at,
        reason_codes=(
            *signal.reason_codes,
            f"basketball_event_team_memory_status_{status}",
            *metric_reasons,
        ),
    )


def _metric_reason_codes(
    signal: ResearchBasketballEventTeamMemorySignal,
    *,
    evidence_recency_score: Decimal,
    config: ResearchBasketballEventTeamMemoryReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_min_score_reason(
        reasons,
        value=signal.specialist_memory_score,
        pass_threshold=config.pass_min_specialist_memory_score,
        watch_threshold=config.watch_min_specialist_memory_score,
        block_reason="specialist_memory_score_block",
        watch_reason="specialist_memory_score_watch",
    )
    _append_min_score_reason(
        reasons,
        value=signal.lineup_memory_coverage_ratio,
        pass_threshold=config.pass_min_lineup_memory_coverage_ratio,
        watch_threshold=config.watch_min_lineup_memory_coverage_ratio,
        block_reason="lineup_memory_coverage_block",
        watch_reason="lineup_memory_coverage_watch",
    )
    _append_min_score_reason(
        reasons,
        value=signal.rotation_memory_coverage_ratio,
        pass_threshold=config.pass_min_rotation_memory_coverage_ratio,
        watch_threshold=config.watch_min_rotation_memory_coverage_ratio,
        block_reason="rotation_memory_coverage_block",
        watch_reason="rotation_memory_coverage_watch",
    )
    _append_min_score_reason(
        reasons,
        value=evidence_recency_score,
        pass_threshold=config.pass_min_evidence_recency_score,
        watch_threshold=config.watch_min_evidence_recency_score,
        block_reason="evidence_recency_score_block",
        watch_reason="evidence_recency_score_watch",
    )
    if signal.latest_evidence_age_seconds > config.watch_max_latest_evidence_age_seconds:
        reasons.append("evidence_age_block")
    elif signal.latest_evidence_age_seconds > config.pass_max_latest_evidence_age_seconds:
        reasons.append("evidence_age_watch")
    return tuple(reasons)


def _append_min_score_reason(
    reasons: list[str],
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value < watch_threshold:
        reasons.append(block_reason)
    elif value < pass_threshold:
        reasons.append(watch_reason)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _memory_readiness_status(
    rows: tuple[ResearchBasketballEventTeamMemoryRow, ...],
) -> str:
    if not rows:
        return "block"
    reasons = tuple(reason for row in rows for reason in row.reason_codes)
    if any(reason in MEMORY_BLOCK_REASON_CODES for reason in reasons):
        return "block"
    if any(reason in MEMORY_WATCH_REASON_CODES for reason in reasons):
        return "watch"
    return "pass"


def _evidence_recency_status(
    rows: tuple[ResearchBasketballEventTeamMemoryRow, ...],
) -> str:
    if not rows:
        return "block"
    reasons = tuple(reason for row in rows for reason in row.reason_codes)
    if any(reason in EVIDENCE_BLOCK_REASON_CODES for reason in reasons):
        return "block"
    if any(reason in EVIDENCE_WATCH_REASON_CODES for reason in reasons):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchBasketballEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("basketball_event_team_memory_report_empty",)
    status = _rollup_status(tuple(row.memory_status for row in rows))
    row_reasons = frozenset(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason in METRIC_REASON_CODES
    )
    return (
        f"basketball_event_team_memory_report_{status}",
        *(reason for reason in METRIC_REASON_CODES if reason in row_reasons),
    )


def _reason_code_counts(
    rows: tuple[ResearchBasketballEventTeamMemoryRow, ...],
) -> tuple[ResearchBasketballEventTeamMemoryReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
    return tuple(
        ResearchBasketballEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=count,
            signal_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchBasketballEventTeamMemoryRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.memory_status],
        -_row_severity_score(row),
        row.basketball_context_bucket,
        row.memory_cohort_bucket,
    )


def _row_severity_score(row: ResearchBasketballEventTeamMemoryRow) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            STATUS_WEIGHT[row.memory_status]
            + (ONE - row.specialist_memory_score)
            + (ONE - row.lineup_memory_coverage_ratio)
            + (ONE - row.rotation_memory_coverage_ratio)
            + (ONE - row.evidence_recency_score)
            + _age_pressure(row.latest_evidence_age_seconds)
        ).quantize(QUANTUM)


def _age_pressure(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(value / Decimal("86400.000000"), ONE).quantize(QUANTUM)


def _status_count(
    rows: tuple[ResearchBasketballEventTeamMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.memory_status == status))


def _sum_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
        return total.quantize(QUANTUM if count else QUANTUM)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / _count(len(values))).quantize(QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _validate_config(config: ResearchBasketballEventTeamMemoryReportConfig) -> None:
    _require_min_threshold_order(
        "pass_min_specialist_memory_score",
        config.pass_min_specialist_memory_score,
        "watch_min_specialist_memory_score",
        config.watch_min_specialist_memory_score,
    )
    _require_min_threshold_order(
        "pass_min_lineup_memory_coverage_ratio",
        config.pass_min_lineup_memory_coverage_ratio,
        "watch_min_lineup_memory_coverage_ratio",
        config.watch_min_lineup_memory_coverage_ratio,
    )
    _require_min_threshold_order(
        "pass_min_rotation_memory_coverage_ratio",
        config.pass_min_rotation_memory_coverage_ratio,
        "watch_min_rotation_memory_coverage_ratio",
        config.watch_min_rotation_memory_coverage_ratio,
    )
    _require_min_threshold_order(
        "pass_min_evidence_recency_score",
        config.pass_min_evidence_recency_score,
        "watch_min_evidence_recency_score",
        config.watch_min_evidence_recency_score,
    )
    if (
        config.watch_max_latest_evidence_age_seconds
        < config.pass_max_latest_evidence_age_seconds
    ):
        raise ValueError(
            "watch_max_latest_evidence_age_seconds must not be below "
            "pass_max_latest_evidence_age_seconds",
        )


def _require_min_threshold_order(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must not be below {watch_name}")


def _validate_row(row: ResearchBasketballEventTeamMemoryRow) -> None:
    metric_reasons = tuple(
        reason for reason in row.reason_codes if reason in METRIC_REASON_CODES
    )
    if row.memory_status != _row_status(metric_reasons):
        raise ValueError("memory_status must match reason_codes")
    status_reason = f"basketball_event_team_memory_status_{row.memory_status}"
    if status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include memory_status reason")
    if row.evidence_recency_score != _ratio(
        row.fresh_evidence_packet_count,
        row.total_evidence_packet_count,
    ):
        raise ValueError("evidence_recency_score must match evidence counts")


def _validate_report(report: ResearchBasketballEventTeamMemoryReport) -> None:
    rows = report.rows
    expected = {
        "signal_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_specialist_memory_score": _average(
            tuple(row.specialist_memory_score for row in rows),
        ),
        "average_lineup_memory_coverage_ratio": _average(
            tuple(row.lineup_memory_coverage_ratio for row in rows),
        ),
        "average_rotation_memory_coverage_ratio": _average(
            tuple(row.rotation_memory_coverage_ratio for row in rows),
        ),
        "fresh_evidence_packet_count": _sum_decimal(
            tuple(row.fresh_evidence_packet_count for row in rows),
            count=True,
        ),
        "total_evidence_packet_count": _sum_decimal(
            tuple(row.total_evidence_packet_count for row in rows),
            count=True,
        ),
        "aggregate_evidence_recency_score": _ratio(
            _sum_decimal(tuple(row.fresh_evidence_packet_count for row in rows), count=True),
            _sum_decimal(tuple(row.total_evidence_packet_count for row in rows), count=True),
        ),
        "max_latest_evidence_age_seconds": _max_decimal(
            tuple(row.latest_evidence_age_seconds for row in rows),
        ),
    }
    for field_name, value in expected.items():
        if getattr(report, field_name) != value:
            raise ValueError(f"{field_name} must match rows")
    if report.memory_readiness_status != _memory_readiness_status(rows):
        raise ValueError("memory_readiness_status must match rows")
    if report.evidence_recency_status != _evidence_recency_status(rows):
        raise ValueError("evidence_recency_status must match rows")
    if report.report_status != _rollup_status(
        (report.memory_readiness_status, report.evidence_recency_status),
    ):
        raise ValueError("report_status must match component statuses")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.report_status]:
        raise ValueError("recommended_next_step must match report_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchBasketballEventTeamMemoryRow, ...],
) -> tuple[ResearchBasketballEventTeamMemoryRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchBasketballEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchBasketballEventTeamMemoryRow")
        _require_hard_flags("row", row)
        key = (row.basketball_context_bucket, row.memory_cohort_bucket)
        if key in seen:
            raise ValueError("rows must contain unique public bucket pairs")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and severity")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchBasketballEventTeamMemoryReasonCodeCount, ...],
) -> tuple[ResearchBasketballEventTeamMemoryReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchBasketballEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchBasketballEventTeamMemoryReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_public_bucket(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    supported: tuple[str, ...],
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code != reason_code.lower():
            raise ValueError("reason_code must be lowercase")
        if reason_code not in supported:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return _require_reason_codes(
        reason_codes,
        supported=(*REPORT_REASON_CODES, *METRIC_REASON_CODES),
        require_nonempty=True,
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized.quantize(QUANTUM)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(report: ResearchBasketballEventTeamMemoryReport) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready_without_digest(
    report: ResearchBasketballEventTeamMemoryReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public payload")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public payload")
