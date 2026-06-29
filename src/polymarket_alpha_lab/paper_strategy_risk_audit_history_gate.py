from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from polymarket_alpha_lab.strategy_audit_history import (
    PaperStrategyRiskAuditHistoryReport,
)


DEFAULT_PAPER_STRATEGY_RISK_AUDIT_HISTORY_GATE_CONFIG_VERSION = (
    "paper-strategy-risk-audit-history-gate-v0"
)

NEXT_STEP_BY_STATUS = {
    "pass": "allow_strategy_risk_audit_history_gate",
    "watch": "throttle_strategy_risk_audit_history_gate",
    "blocked": "block_strategy_risk_audit_history_gate",
}

PASS_REASON_CODE = "paper_strategy_risk_audit_history_gate_passed"
SOURCE_BLOCKED_REASON_CODE = "source_strategy_risk_audit_history_blocked_by_risk"
SOURCE_INSUFFICIENT_EVIDENCE_REASON_CODE = (
    "source_strategy_risk_audit_history_insufficient_evidence"
)
STALE_REASON_CODE = "stale_strategy_risk_audit_history"
MISSING_LATEST_REASON_CODE = "missing_latest_strategy_risk_audit_history_timestamp"

REASON_CODES = frozenset(
    (
        PASS_REASON_CODE,
        SOURCE_BLOCKED_REASON_CODE,
        SOURCE_INSUFFICIENT_EVIDENCE_REASON_CODE,
        STALE_REASON_CODE,
        MISSING_LATEST_REASON_CODE,
    ),
)
SOURCE_HISTORY_STATUSES = frozenset(
    (
        "empty_audit_history",
        "latest_audit_ready",
        "latest_insufficient_evidence",
        "latest_blocked_by_risk",
    ),
)
AUDIT_STATUSES = frozenset(
    (
        "audit_ready",
        "insufficient_evidence",
        "blocked_by_risk",
    ),
)
GATE_NAMES = frozenset(
    (
        "paper_history",
        "settlement_evidence",
        "forecast_quality",
        "cost_discipline",
        "nav_drawdown",
        "open_exposure",
        "settlement_nav_risk",
    ),
)

__all__ = (
    "DEFAULT_PAPER_STRATEGY_RISK_AUDIT_HISTORY_GATE_CONFIG_VERSION",
    "PaperStrategyRiskAuditHistoryGateConfig",
    "PaperStrategyRiskAuditHistoryGateReasonCodeCount",
    "PaperStrategyRiskAuditHistoryGateReport",
    "build_paper_strategy_risk_audit_history_gate_report",
)


@dataclass(frozen=True)
class PaperStrategyRiskAuditHistoryGateConfig:
    config_version: str = DEFAULT_PAPER_STRATEGY_RISK_AUDIT_HISTORY_GATE_CONFIG_VERSION
    max_latest_age_seconds: int = 86_400
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRiskAuditHistoryGateConfig:
            raise ValueError("config must be a PaperStrategyRiskAuditHistoryGateConfig")
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("max_latest_age_seconds", self.max_latest_age_seconds)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperStrategyRiskAuditHistoryGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRiskAuditHistoryGateReasonCodeCount:
            raise ValueError(
                "reason row must be a PaperStrategyRiskAuditHistoryGateReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("reason row", self)


@dataclass(frozen=True)
class PaperStrategyRiskAuditHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[PaperStrategyRiskAuditHistoryGateReasonCodeCount, ...]
    source_history_status: str
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    latest_audit_status: str | None
    latest_pass_count: int
    latest_fail_count: int
    latest_incomplete_count: int
    consecutive_non_ready_count: int
    consecutive_blocked_by_risk_count: int
    consecutive_insufficient_evidence_count: int
    latest_failed_gate_names: tuple[str, ...]
    latest_incomplete_gate_names: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyRiskAuditHistoryGateReport:
            raise ValueError("report must be a PaperStrategyRiskAuditHistoryGateReport")
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
        _require_source_history_status("source_history_status", self.source_history_status)
        _require_nonnegative_int("source_report_count", self.source_report_count)
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
        _require_optional_audit_status("latest_audit_status", self.latest_audit_status)
        for field_name in (
            "latest_pass_count",
            "latest_fail_count",
            "latest_incomplete_count",
            "consecutive_non_ready_count",
            "consecutive_blocked_by_risk_count",
            "consecutive_insufficient_evidence_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_failed_gate_names",
            _normalize_gate_names(
                "latest_failed_gate_names",
                self.latest_failed_gate_names,
            ),
        )
        object.__setattr__(
            self,
            "latest_incomplete_gate_names",
            _normalize_gate_names(
                "latest_incomplete_gate_names",
                self.latest_incomplete_gate_names,
            ),
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


def build_paper_strategy_risk_audit_history_gate_report(
    history_report: PaperStrategyRiskAuditHistoryReport,
    *,
    config: PaperStrategyRiskAuditHistoryGateConfig,
    generated_at: datetime,
) -> PaperStrategyRiskAuditHistoryGateReport:
    if type(history_report) is not PaperStrategyRiskAuditHistoryReport:
        raise ValueError(
            "source history report must be a PaperStrategyRiskAuditHistoryReport",
        )
    if type(config) is not PaperStrategyRiskAuditHistoryGateConfig:
        raise ValueError("config must be a PaperStrategyRiskAuditHistoryGateConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_source_hard_flags("source history report", history_report)
    _require_hard_flags("config", config)

    latest_source_generated_at = history_report.latest_audit_generated_at
    latest_source_age_seconds: int | None
    reasons: list[str] = []

    if history_report.status == "latest_blocked_by_risk":
        reasons.append(SOURCE_BLOCKED_REASON_CODE)
    elif history_report.status == "latest_insufficient_evidence":
        reasons.append(SOURCE_INSUFFICIENT_EVIDENCE_REASON_CODE)
    elif history_report.status not in ("latest_audit_ready", "empty_audit_history"):
        raise ValueError("source history status must be a known audit history status")

    if latest_source_generated_at is None:
        latest_source_age_seconds = None
        reasons.append(MISSING_LATEST_REASON_CODE)
    else:
        latest_source_generated_at = _as_utc(
            "latest_audit_generated_at",
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
    elif (
        STALE_REASON_CODE in reason_codes
        or SOURCE_INSUFFICIENT_EVIDENCE_REASON_CODE in reason_codes
    ):
        gate_status = "watch"
    else:
        gate_status = "pass"
        reason_codes = (PASS_REASON_CODE,)

    return PaperStrategyRiskAuditHistoryGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_version=history_report.config_version,
        source_generated_at=history_report.generated_at,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=tuple(
            PaperStrategyRiskAuditHistoryGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        ),
        source_history_status=history_report.status,
        source_report_count=history_report.audit_report_count,
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        latest_audit_status=history_report.latest_audit_status,
        latest_pass_count=history_report.latest_pass_count,
        latest_fail_count=history_report.latest_fail_count,
        latest_incomplete_count=history_report.latest_incomplete_count,
        consecutive_non_ready_count=history_report.consecutive_non_ready_count,
        consecutive_blocked_by_risk_count=history_report.consecutive_blocked_by_risk_count,
        consecutive_insufficient_evidence_count=(
            history_report.consecutive_insufficient_evidence_count
        ),
        latest_failed_gate_names=history_report.latest_failed_gate_names,
        latest_incomplete_gate_names=history_report.latest_incomplete_gate_names,
        reason_codes=reason_codes,
    )


def _normalize_reason_code_counts(
    rows: tuple[PaperStrategyRiskAuditHistoryGateReasonCodeCount, ...],
) -> tuple[PaperStrategyRiskAuditHistoryGateReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperStrategyRiskAuditHistoryGateReasonCodeCount:
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


def _normalize_gate_names(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for value in normalized:
        if value not in GATE_NAMES:
            raise ValueError(f"{field_name} must contain known gate names")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
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


def _require_source_history_status(field_name: str, value: Any) -> None:
    _require_canonical_string(field_name, value)
    if value not in SOURCE_HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be a known audit history status")


def _require_optional_audit_status(field_name: str, value: Any) -> None:
    if value is None:
        return
    _require_canonical_string(field_name, value)
    if value not in AUDIT_STATUSES:
        raise ValueError(f"{field_name} must be a known audit status")


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


def _require_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_source_hard_flags(field_name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", True) is not True:
        raise ValueError(f"{field_name} readonly must be True")
