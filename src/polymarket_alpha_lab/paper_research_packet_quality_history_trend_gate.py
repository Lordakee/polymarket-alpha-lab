"""Pure gate reducer for paper research packet quality history trends."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_research_packet_quality import QUALITY_STATUSES
from polymarket_alpha_lab.paper_research_packet_quality_history_trend import (
    PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow,
    PaperResearchPacketQualityHistoryTrendReport,
    PaperResearchPacketQualityHistoryTrendStatusRow,
)


DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_TREND_GATE_CONFIG_VERSION = (
    "paper-research-packet-quality-history-trend-gate-v0"
)
GATE_STATUSES = ("pass", "watch", "blocked")
TREND_STATUSES = ("stable", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_research_packet_quality_history_trend",
    "watch": "review_paper_research_packet_quality_history_trend",
    "blocked": "block_paper_research_packet_quality_history_trend",
}
PASS_REASON_CODE = "paper_research_packet_quality_history_trend_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_quality_history_trend",
        "source_quality_history_trend_blocked",
        "latest_quality_history_blocked",
        "latest_quality_blocked",
        "consecutive_quality_history_blocked_threshold_exceeded",
        "missing_latest_quality_history_trend_timestamp",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "source_quality_history_trend_watch",
        "latest_quality_history_watch",
        "latest_quality_watch",
        "consecutive_quality_history_watch_threshold_exceeded",
        "duplicate_quality_history_generated_at_threshold_exceeded",
        "stale_quality_history_trend",
    ),
)
ALLOWED_REASON_CODES = BLOCKED_REASON_CODES | WATCH_REASON_CODES | {PASS_REASON_CODE}

__all__ = (
    "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_TREND_GATE_CONFIG_VERSION",
    "NEXT_STEP_BY_STATUS",
    "PaperResearchPacketQualityHistoryTrendGateConfig",
    "PaperResearchPacketQualityHistoryTrendGateReasonCodeCount",
    "PaperResearchPacketQualityHistoryTrendGateReport",
    "build_paper_research_packet_quality_history_trend_gate_report",
)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryTrendGateConfig:
    config_version: str = (
        DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_TREND_GATE_CONFIG_VERSION
    )
    min_history_report_count: int = 3
    max_latest_history_age_seconds: int = 86_400
    max_consecutive_latest_watch_count: int = 0
    max_consecutive_latest_blocked_count: int = 0
    max_duplicate_generated_at_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_history_report_count",
            "max_latest_history_age_seconds",
            "max_consecutive_latest_watch_count",
            "max_consecutive_latest_blocked_count",
            "max_duplicate_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryTrendGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperResearchPacketQualityHistoryTrendGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperResearchPacketQualityHistoryTrendGateReasonCodeCount,
        ...,
    ]
    source_trend_status: str
    source_history_report_count: int
    latest_history_generated_at: datetime | None
    latest_history_age_seconds: int | None
    latest_history_status: str | None
    latest_quality_status: str | None
    duplicate_generated_at_count: int
    consecutive_latest_pass_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        object.__setattr__(
            self,
            "latest_history_generated_at",
            _as_optional_utc(
                "latest_history_generated_at",
                self.latest_history_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_trend_status("source_trend_status", self.source_trend_status)
        _require_nonnegative_int(
            "source_history_report_count",
            self.source_history_report_count,
        )
        _require_optional_nonnegative_int(
            "latest_history_age_seconds",
            self.latest_history_age_seconds,
        )
        if self.latest_history_status is not None:
            _require_quality_status("latest_history_status", self.latest_history_status)
        if self.latest_quality_status is not None:
            _require_quality_status("latest_quality_status", self.latest_quality_status)
        for field_name in (
            "duplicate_generated_at_count",
            "consecutive_latest_pass_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_gate_report(self)
        _validate_hard_flags("gate report", self)


def build_paper_research_packet_quality_history_trend_gate_report(
    trend_report: object,
    *,
    config: PaperResearchPacketQualityHistoryTrendGateConfig,
    generated_at: datetime,
) -> PaperResearchPacketQualityHistoryTrendGateReport:
    if type(trend_report) is not PaperResearchPacketQualityHistoryTrendReport:
        raise ValueError(
            "trend_report must be a PaperResearchPacketQualityHistoryTrendReport",
        )
    if type(config) is not PaperResearchPacketQualityHistoryTrendGateConfig:
        raise ValueError(
            "config must be a PaperResearchPacketQualityHistoryTrendGateConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_hard_flags("config", config)
    _validate_trend_report(trend_report)

    generated_at_utc = _as_utc("generated_at", generated_at)
    latest_history_generated_at = _as_optional_utc(
        "latest_history_generated_at",
        trend_report.latest_history_generated_at,
    )
    latest_history_age_seconds = _latest_history_age_seconds(
        generated_at_utc,
        latest_history_generated_at,
    )
    reason_codes = _gate_reason_codes(
        trend_report=trend_report,
        config=config,
        latest_history_age_seconds=latest_history_age_seconds,
    )
    gate_status = _gate_status(reason_codes)

    return PaperResearchPacketQualityHistoryTrendGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_config_version=trend_report.config_version,
        source_generated_at=trend_report.generated_at,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=_reason_code_counts(reason_codes),
        source_trend_status=trend_report.trend_status,
        source_history_report_count=trend_report.source_history_report_count,
        latest_history_generated_at=latest_history_generated_at,
        latest_history_age_seconds=latest_history_age_seconds,
        latest_history_status=trend_report.latest_history_status,
        latest_quality_status=trend_report.latest_quality_status,
        duplicate_generated_at_count=trend_report.duplicate_generated_at_count,
        consecutive_latest_pass_count=trend_report.consecutive_latest_pass_count,
        consecutive_latest_watch_count=trend_report.consecutive_latest_watch_count,
        consecutive_latest_blocked_count=trend_report.consecutive_latest_blocked_count,
        reason_codes=reason_codes,
    )


def _gate_reason_codes(
    *,
    trend_report: PaperResearchPacketQualityHistoryTrendReport,
    config: PaperResearchPacketQualityHistoryTrendGateConfig,
    latest_history_age_seconds: int | None,
) -> tuple[str, ...]:
    reason_codes: list[str] = []

    if trend_report.source_history_report_count < config.min_history_report_count:
        reason_codes.append("insufficient_quality_history_trend")
    if trend_report.trend_status == "blocked":
        reason_codes.append("source_quality_history_trend_blocked")
    if trend_report.latest_history_status == "blocked":
        reason_codes.append("latest_quality_history_blocked")
    if trend_report.latest_quality_status == "blocked":
        reason_codes.append("latest_quality_blocked")
    if (
        trend_report.consecutive_latest_blocked_count
        > config.max_consecutive_latest_blocked_count
    ):
        reason_codes.append("consecutive_quality_history_blocked_threshold_exceeded")
    if trend_report.latest_history_generated_at is None:
        reason_codes.append("missing_latest_quality_history_trend_timestamp")

    if trend_report.trend_status == "watch":
        reason_codes.append("source_quality_history_trend_watch")
    if trend_report.latest_history_status == "watch":
        reason_codes.append("latest_quality_history_watch")
    if trend_report.latest_quality_status == "watch":
        reason_codes.append("latest_quality_watch")
    if (
        trend_report.consecutive_latest_watch_count
        > config.max_consecutive_latest_watch_count
    ):
        reason_codes.append("consecutive_quality_history_watch_threshold_exceeded")
    if trend_report.duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append("duplicate_quality_history_generated_at_threshold_exceeded")
    if (
        latest_history_age_seconds is not None
        and latest_history_age_seconds > config.max_latest_history_age_seconds
    ):
        reason_codes.append("stale_quality_history_trend")

    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperResearchPacketQualityHistoryTrendGateReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            reason_code,
            report_count,
        )
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_trend_report(
    trend_report: PaperResearchPacketQualityHistoryTrendReport,
) -> None:
    _validate_hard_flags("trend report", trend_report)
    _require_canonical_string("source config_version", trend_report.config_version)
    _require_trend_status("source trend_status", trend_report.trend_status)
    _require_nonnegative_int(
        "source_history_report_count",
        trend_report.source_history_report_count,
    )
    _as_utc("source generated_at", trend_report.generated_at)
    _as_optional_utc(
        "source first_history_generated_at",
        trend_report.first_history_generated_at,
    )
    _as_optional_utc(
        "source latest_history_generated_at",
        trend_report.latest_history_generated_at,
    )
    _require_optional_nonnegative_int(
        "source latest_history_age_seconds",
        trend_report.latest_history_age_seconds,
    )
    if trend_report.latest_history_status is not None:
        _require_quality_status(
            "source latest_history_status",
            trend_report.latest_history_status,
        )
    if trend_report.latest_quality_status is not None:
        _require_quality_status(
            "source latest_quality_status",
            trend_report.latest_quality_status,
        )
    _validate_source_status_rows(trend_report)
    for field_name in (
        "duplicate_generated_at_count",
        "consecutive_latest_pass_count",
        "consecutive_latest_watch_count",
        "consecutive_latest_blocked_count",
    ):
        _require_nonnegative_int(field_name, getattr(trend_report, field_name))
    _normalize_reason_codes(
        "source latest_reason_codes",
        trend_report.latest_reason_codes,
        allow_empty=True,
        allowed_reason_codes=None,
    )
    _validate_source_recurring_rows(trend_report)
    _normalize_reason_codes(
        "source reason_codes",
        trend_report.reason_codes,
        allowed_reason_codes=None,
    )


def _validate_source_status_rows(
    trend_report: PaperResearchPacketQualityHistoryTrendReport,
) -> None:
    rows = trend_report.history_status_rows
    if type(rows) is not tuple or len(rows) != len(QUALITY_STATUSES):
        raise ValueError("history_status_rows must cover pass, watch, and blocked")
    seen: list[str] = []
    total_count = 0
    for row in rows:
        if type(row) is not PaperResearchPacketQualityHistoryTrendStatusRow:
            raise ValueError("history_status_rows must contain exact status rows")
        _validate_hard_flags("history status row", row)
        _require_quality_status("history_status", row.history_status)
        _require_nonnegative_int("status_count", row.status_count)
        seen.append(row.history_status)
        total_count += row.status_count
    if tuple(seen) != QUALITY_STATUSES:
        raise ValueError("history_status_rows must be pass, watch, blocked")
    if total_count != trend_report.source_history_report_count:
        raise ValueError("history_status_rows must sum to source count")


def _validate_source_recurring_rows(
    trend_report: PaperResearchPacketQualityHistoryTrendReport,
) -> None:
    rows = trend_report.recurring_reason_code_rows
    if type(rows) is not tuple:
        raise ValueError("recurring_reason_code_rows must be a tuple")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow:
            raise ValueError("recurring_reason_code_rows must contain exact recurring rows")
        _validate_hard_flags("recurring reason row", row)
        _require_recurring_status("check_status", row.check_status)
        _require_canonical_string("reason_code", row.reason_code)
        _require_positive_int("history_report_count", row.history_report_count)
        key = (row.check_status, row.reason_code)
        if key in seen:
            raise ValueError("recurring_reason_code_rows must be unique")
        seen.add(key)


def _validate_gate_report(
    report: PaperResearchPacketQualityHistoryTrendGateReport,
) -> None:
    expected_next_step = NEXT_STEP_BY_STATUS[report.gate_status]
    if report.recommended_next_step != expected_next_step:
        raise ValueError("recommended_next_step must match gate_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.gate_status != _gate_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_other_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_other_reason:
        raise ValueError("pass reason must not be mixed with watch or blocked reasons")
    if report.latest_history_generated_at is None:
        if report.latest_history_age_seconds is not None:
            raise ValueError("latest_history_age_seconds requires latest timestamp")
    else:
        expected_age = _latest_history_age_seconds(
            report.generated_at,
            report.latest_history_generated_at,
        )
        if report.latest_history_age_seconds != expected_age:
            raise ValueError("latest_history_age_seconds must match latest timestamp")
    _validate_empty_or_nonempty_source_fields(report)


def _validate_empty_or_nonempty_source_fields(
    report: PaperResearchPacketQualityHistoryTrendGateReport,
) -> None:
    if report.source_history_report_count == 0:
        if report.latest_history_generated_at is not None:
            raise ValueError("latest_history_generated_at must be absent without reports")
        if report.latest_history_status is not None:
            raise ValueError("latest_history_status must be absent without reports")
        if report.latest_quality_status is not None:
            raise ValueError("latest_quality_status must be absent without reports")
        for field_name in (
            "duplicate_generated_at_count",
            "consecutive_latest_pass_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            if getattr(report, field_name) != 0:
                raise ValueError(f"{field_name} must be zero without reports")
        return
    if report.latest_history_generated_at is None:
        raise ValueError("latest_history_generated_at is required with reports")
    if report.latest_history_status is None:
        raise ValueError("latest_history_status is required with reports")
    if report.latest_quality_status is None:
        raise ValueError("latest_quality_status is required with reports")


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperResearchPacketQualityHistoryTrendGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    previous_key: tuple[int, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not PaperResearchPacketQualityHistoryTrendGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _latest_history_age_seconds(
    generated_at: datetime,
    latest_history_generated_at: datetime | None,
) -> int | None:
    if latest_history_generated_at is None:
        return None
    age_seconds = int(
        (
            _as_utc("generated_at", generated_at)
            - _as_utc("latest_history_generated_at", latest_history_generated_at)
        ).total_seconds(),
    )
    if age_seconds < 0:
        raise ValueError("latest_history_age_seconds must be nonnegative")
    return age_seconds


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
    allowed_reason_codes: frozenset[str] | None = ALLOWED_REASON_CODES,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError(f"{field_name} is required")
    previous: str | None = None
    seen: set[str] = set()
    for code in codes:
        _require_canonical_string(field_name, code)
        if allowed_reason_codes is not None and code not in allowed_reason_codes:
            raise ValueError(f"{field_name} must match gate semantics")
        if code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > code:
            raise ValueError(f"{field_name} must be sorted")
        previous = code
        seen.add(code)
    return codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_trend_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TREND_STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_quality_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_recurring_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ("blocked", "watch"):
        raise ValueError(f"{field_name} must be blocked or watch")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
