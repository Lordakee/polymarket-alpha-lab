from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.paper_strategy_cycle_report_history import (
    PaperStrategyCycleReportHistoryReport,
)


DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION = (
    "paper-strategy-cycle-report-history-gate-v0"
)

NEXT_STEP_BY_STATUS = {
    "pass": "allow_strategy_cycle_history_gate",
    "watch": "throttle_strategy_cycle_history_gate",
    "blocked": "block_strategy_cycle_history_gate",
}

PASS_REASON_CODE = "paper_strategy_cycle_report_history_gate_passed"
SOURCE_BLOCKED_REASON_CODE = "source_strategy_cycle_report_history_blocked"
SOURCE_WATCH_REASON_CODE = "source_strategy_cycle_report_history_watch"
STALE_REASON_CODE = "stale_strategy_cycle_report_history"
MISSING_LATEST_REASON_CODE = "missing_latest_strategy_cycle_report_history_timestamp"

REASON_CODES = frozenset(
    (
        PASS_REASON_CODE,
        SOURCE_BLOCKED_REASON_CODE,
        SOURCE_WATCH_REASON_CODE,
        STALE_REASON_CODE,
        MISSING_LATEST_REASON_CODE,
    ),
)

__all__ = (
    "DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION",
    "PaperStrategyCycleReportHistoryGateConfig",
    "PaperStrategyCycleReportHistoryGateReasonCodeCount",
    "PaperStrategyCycleReportHistoryGateReport",
    "build_paper_strategy_cycle_report_history_gate_report",
)


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateConfig:
    config_version: str = DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_CONFIG_VERSION
    max_latest_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyCycleReportHistoryGateConfig:
            raise ValueError("config must be a PaperStrategyCycleReportHistoryGateConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("max_latest_age_seconds", self.max_latest_age_seconds)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyCycleReportHistoryGateReasonCodeCount:
            raise ValueError(
                "reason row must be a PaperStrategyCycleReportHistoryGateReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("reason row", self)


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[PaperStrategyCycleReportHistoryGateReasonCodeCount, ...]
    source_history_status: str
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    latest_snapshot_ready_share: Decimal
    blocked_market_share: Decimal
    latest_snapshot_ready_count: int
    latest_considered_count: int
    total_blocked_market_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyCycleReportHistoryGateReport:
            raise ValueError("report must be a PaperStrategyCycleReportHistoryGateReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        if self.latest_source_generated_at is not None:
            object.__setattr__(
                self,
                "latest_source_generated_at",
                _as_utc(
                    "latest_source_generated_at",
                    self.latest_source_generated_at,
                ),
            )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_status("gate_status", self.gate_status)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        _require_status("source_history_status", self.source_history_status)
        _require_positive_int("source_report_count", self.source_report_count)
        if self.latest_source_age_seconds is None:
            if self.latest_source_generated_at is not None:
                raise ValueError(
                    "latest_source_age_seconds is required when latest source exists",
                )
        else:
            _require_nonnegative_int(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            )
            if self.latest_source_generated_at is None:
                raise ValueError(
                    "latest_source_age_seconds must be None without latest source",
                )
        _require_probability_decimal(
            "latest_snapshot_ready_share",
            self.latest_snapshot_ready_share,
        )
        _require_probability_decimal("blocked_market_share", self.blocked_market_share)
        _require_nonnegative_int(
            "latest_snapshot_ready_count",
            self.latest_snapshot_ready_count,
        )
        _require_nonnegative_int("latest_considered_count", self.latest_considered_count)
        _require_nonnegative_int(
            "total_blocked_market_count",
            self.total_blocked_market_count,
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if tuple(row.reason_code for row in self.reason_code_counts) != self.reason_codes:
            raise ValueError("reason_code_counts must match reason_codes")
        if any(row.report_count != 1 for row in self.reason_code_counts):
            raise ValueError("reason_code_counts report_count must be 1")
        if self.gate_status == "pass" and self.reason_codes != (PASS_REASON_CODE,):
            raise ValueError("pass gate must have the pass reason_code")
        if self.gate_status != "pass" and PASS_REASON_CODE in self.reason_codes:
            raise ValueError("non-pass gate must not have the pass reason_code")
        _require_hard_flags("report", self)


def build_paper_strategy_cycle_report_history_gate_report(
    history_report: PaperStrategyCycleReportHistoryReport,
    *,
    config: PaperStrategyCycleReportHistoryGateConfig,
    generated_at: datetime,
) -> PaperStrategyCycleReportHistoryGateReport:
    if type(history_report) is not PaperStrategyCycleReportHistoryReport:
        raise ValueError(
            "source history report must be a PaperStrategyCycleReportHistoryReport",
        )
    if type(config) is not PaperStrategyCycleReportHistoryGateConfig:
        raise ValueError("config must be a PaperStrategyCycleReportHistoryGateConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("source history report", history_report)
    _require_hard_flags("config", config)
    _require_probability_decimal(
        "latest_snapshot_ready_share",
        history_report.latest_snapshot_ready_share,
    )
    _require_probability_decimal(
        "blocked_market_share",
        history_report.blocked_market_share,
    )

    latest_source_generated_at = history_report.latest_report_generated_at
    latest_source_age_seconds: int | None
    reasons: list[str] = []

    if history_report.history_status == "blocked":
        reasons.append(SOURCE_BLOCKED_REASON_CODE)
    elif history_report.history_status == "watch":
        reasons.append(SOURCE_WATCH_REASON_CODE)
    elif history_report.history_status != "pass":
        raise ValueError("source history status must be a known status")

    if latest_source_generated_at is None:
        latest_source_age_seconds = None
        reasons.append(MISSING_LATEST_REASON_CODE)
    else:
        latest_source_generated_at = _as_utc(
            "latest_report_generated_at",
            latest_source_generated_at,
        )
        latest_source_age_seconds = int(
            (generated_at - latest_source_generated_at).total_seconds(),
        )
        if latest_source_age_seconds < 0:
            raise ValueError("latest source timestamp must not be in the future")
        if latest_source_age_seconds > config.max_latest_age_seconds:
            reasons.append(STALE_REASON_CODE)

    reason_codes = tuple(sorted(set(reasons)))
    if (
        MISSING_LATEST_REASON_CODE in reason_codes
        or SOURCE_BLOCKED_REASON_CODE in reason_codes
    ):
        gate_status = "blocked"
    elif STALE_REASON_CODE in reason_codes or SOURCE_WATCH_REASON_CODE in reason_codes:
        gate_status = "watch"
    else:
        gate_status = "pass"
        reason_codes = (PASS_REASON_CODE,)

    return PaperStrategyCycleReportHistoryGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_version=history_report.config_version,
        source_generated_at=history_report.generated_at,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=tuple(
            PaperStrategyCycleReportHistoryGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        ),
        source_history_status=history_report.history_status,
        source_report_count=history_report.report_count,
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        latest_snapshot_ready_share=history_report.latest_snapshot_ready_share,
        blocked_market_share=history_report.blocked_market_share,
        latest_snapshot_ready_count=history_report.latest_snapshot_ready_count,
        latest_considered_count=history_report.latest_considered_count,
        total_blocked_market_count=history_report.total_blocked_market_count,
        reason_codes=reason_codes,
    )


def _normalize_reason_code_counts(
    rows: tuple[PaperStrategyCycleReportHistoryGateReasonCodeCount, ...],
) -> tuple[PaperStrategyCycleReportHistoryGateReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperStrategyCycleReportHistoryGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason rows")
        _require_hard_flags("reason row", row)
    reason_codes = tuple(row.reason_code for row in normalized)
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    for reason_code in normalized:
        _require_reason_code(field_name, reason_code)
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one reason code")
    return normalized


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: Any) -> None:
    _require_canonical_string(field_name, value)
    if value not in NEXT_STEP_BY_STATUS:
        raise ValueError(f"{field_name} must be a known status")


def _require_reason_code(field_name: str, value: Any) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: Any) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_probability_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between zero and one")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
