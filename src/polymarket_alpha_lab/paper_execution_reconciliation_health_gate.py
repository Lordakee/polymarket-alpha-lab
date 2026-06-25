"""Pure reducer for paper execution reconciliation health gates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationReport,
)


DEFAULT_PAPER_EXECUTION_RECONCILIATION_HEALTH_GATE_CONFIG_VERSION = (
    "paper-execution-reconciliation-health-gate-v0"
)

HEALTH_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_execution_reconciliation",
    "watch": "watch_paper_execution_reconciliation",
    "blocked": "block_paper_execution_reconciliation",
}
PASS_REASON_CODE = "paper_execution_reconciliation_health_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_paper_execution_reconciliation_source_history",
        "missing_paper_execution_reconciliation_evidence",
        "paper_execution_reconciliation_discrepancies_present",
        "paper_execution_reconciliation_unrealized_loss_threshold_exceeded",
        "stale_paper_execution_reconciliation_evidence",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "pending_paper_execution_reconciliation_exposure",
    ),
)

__all__ = (
    "DEFAULT_PAPER_EXECUTION_RECONCILIATION_HEALTH_GATE_CONFIG_VERSION",
    "PaperExecutionReconciliationHealthGateConfig",
    "PaperExecutionReconciliationHealthGateReasonCodeCount",
    "PaperExecutionReconciliationHealthGateReport",
    "build_paper_execution_reconciliation_health_gate_report",
)


@dataclass(frozen=True)
class PaperExecutionReconciliationHealthGateConfig:
    config_version: str = DEFAULT_PAPER_EXECUTION_RECONCILIATION_HEALTH_GATE_CONFIG_VERSION
    min_source_reconciliation_report_count: int = 3
    max_latest_source_age_seconds: int = 86_400
    max_unrealized_loss: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationHealthGateConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationHealthGateConfig:
            raise ValueError(
                "config must be exactly PaperExecutionReconciliationHealthGateConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int(
            "min_source_reconciliation_report_count",
            self.min_source_reconciliation_report_count,
        )
        _require_nonnegative_int(
            "max_latest_source_age_seconds",
            self.max_latest_source_age_seconds,
        )
        _require_optional_nonnegative_decimal(
            "max_unrealized_loss",
            self.max_unrealized_loss,
        )
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationHealthGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationHealthGateReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationHealthGateReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperExecutionReconciliationHealthGateReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperExecutionReconciliationHealthGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str | None
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperExecutionReconciliationHealthGateReasonCodeCount,
        ...,
    ]
    source_reconciliation_report_count: int
    latest_reconciliation_status: str | None
    latest_reconciliation_generated_at: datetime | None
    latest_source_age_seconds: int | None
    latest_filled_pending_count: int | None
    latest_unrealized_pnl: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperExecutionReconciliationHealthGateReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperExecutionReconciliationHealthGateReport:
            raise ValueError(
                "gate report must be exactly PaperExecutionReconciliationHealthGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "latest_reconciliation_generated_at",
            _as_optional_utc(
                "latest_reconciliation_generated_at",
                self.latest_reconciliation_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.source_config_version is not None:
            _require_canonical_string("source_config_version", self.source_config_version)
        _require_health_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int(
            "source_reconciliation_report_count",
            self.source_reconciliation_report_count,
        )
        if self.latest_reconciliation_status is not None:
            _require_canonical_string(
                "latest_reconciliation_status",
                self.latest_reconciliation_status,
            )
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        _require_optional_nonnegative_int(
            "latest_filled_pending_count",
            self.latest_filled_pending_count,
        )
        _require_optional_decimal(
            "latest_unrealized_pnl",
            self.latest_unrealized_pnl,
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
        _validate_gate_report(self)
        _validate_hard_flags("gate report", self)


@dataclass(frozen=True)
class _ReconciliationEvidenceSummary:
    source_config_version: str | None
    source_reconciliation_report_count: int
    latest_reconciliation_status: str | None
    latest_reconciliation_generated_at: datetime | None
    latest_filled_pending_count: int | None
    latest_unrealized_pnl: Decimal | None
    has_discrepancies: bool


def build_paper_execution_reconciliation_health_gate_report(
    reconciliation_evidence: object,
    *,
    config: PaperExecutionReconciliationHealthGateConfig,
    generated_at: datetime,
) -> PaperExecutionReconciliationHealthGateReport:
    if type(config) is not PaperExecutionReconciliationHealthGateConfig:
        raise ValueError(
            "config must be exactly PaperExecutionReconciliationHealthGateConfig",
    )
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_summary = _reconciliation_evidence_summary(
        reconciliation_evidence,
    )

    latest_source_age_seconds: int | None = None
    if evidence_summary.latest_reconciliation_generated_at is not None:
        latest_source_age_seconds = _latest_source_age_seconds(
            generated_at=generated_at_utc,
            source_generated_at=evidence_summary.latest_reconciliation_generated_at,
        )

    reason_codes = _gate_reason_codes(
        evidence_summary=evidence_summary,
        latest_source_age_seconds=latest_source_age_seconds,
        config=config,
    )
    gate_status = _gate_status(reason_codes)
    reason_code_counts = tuple(
        PaperExecutionReconciliationHealthGateReasonCodeCount(
            reason_code=reason_code,
            report_count=1,
        )
        for reason_code in reason_codes
    )

    return PaperExecutionReconciliationHealthGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_config_version=evidence_summary.source_config_version,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=reason_code_counts,
        source_reconciliation_report_count=(
            evidence_summary.source_reconciliation_report_count
        ),
        latest_reconciliation_status=evidence_summary.latest_reconciliation_status,
        latest_reconciliation_generated_at=(
            evidence_summary.latest_reconciliation_generated_at
        ),
        latest_source_age_seconds=latest_source_age_seconds,
        latest_filled_pending_count=(
            evidence_summary.latest_filled_pending_count
        ),
        latest_unrealized_pnl=evidence_summary.latest_unrealized_pnl,
        reason_codes=reason_codes,
    )


def _reconciliation_evidence_summary(
    reconciliation_evidence: object,
) -> _ReconciliationEvidenceSummary:
    if type(reconciliation_evidence) is tuple:
        source_reports = reconciliation_evidence
    elif hasattr(reconciliation_evidence, "reconciliation_reports"):
        _validate_hard_flags("reconciliation evidence", reconciliation_evidence)
        source_reports = reconciliation_evidence.reconciliation_reports
    elif _looks_like_history_summary(reconciliation_evidence):
        return _summary_from_history_summary(reconciliation_evidence)
    else:
        source_reports = reconciliation_evidence
    if type(source_reports) is not tuple:
        raise ValueError("source reports must be a tuple")
    return _summary_from_source_reports(source_reports)


def _summary_from_source_reports(
    source_reports: tuple[PaperExecutionReconciliationReport, ...],
) -> _ReconciliationEvidenceSummary:
    _validate_source_reports(source_reports)
    latest_report = _latest_report(source_reports)
    return _ReconciliationEvidenceSummary(
        source_config_version=(
            latest_report.config_version if latest_report is not None else None
        ),
        source_reconciliation_report_count=len(source_reports),
        latest_reconciliation_status=(
            latest_report.reconciliation_status if latest_report is not None else None
        ),
        latest_reconciliation_generated_at=(
            latest_report.generated_at if latest_report is not None else None
        ),
        latest_filled_pending_count=(
            latest_report.filled_pending_count if latest_report is not None else None
        ),
        latest_unrealized_pnl=(
            latest_report.unrealized_pnl if latest_report is not None else None
        ),
        has_discrepancies=any(
            report.reconciliation_status == "has_discrepancies"
            for report in source_reports
        ),
    )


def _looks_like_history_summary(value: object) -> bool:
    return all(
        hasattr(value, field_name)
        for field_name in (
            "config_version",
            "report_count",
            "latest_report_generated_at",
            "latest_reconciliation_status",
            "discrepancy_streak_count",
            "latest_unrealized_pnl",
            "paper_only",
            "report_only",
            "readonly",
        )
    )


def _summary_from_history_summary(value: object) -> _ReconciliationEvidenceSummary:
    _validate_hard_flags("reconciliation evidence", value)
    source_config_version = getattr(value, "config_version")
    report_count = getattr(value, "report_count")
    latest_reconciliation_status = getattr(value, "latest_reconciliation_status")
    latest_report_generated_at = getattr(value, "latest_report_generated_at")
    discrepancy_streak_count = getattr(value, "discrepancy_streak_count")
    latest_unrealized_pnl = getattr(value, "latest_unrealized_pnl")

    _require_canonical_string("source_config_version", source_config_version)
    _require_nonnegative_int("report_count", report_count)
    if latest_reconciliation_status is not None:
        _require_canonical_string(
            "latest_reconciliation_status",
            latest_reconciliation_status,
        )
    latest_reconciliation_generated_at = _as_optional_utc(
        "latest_report_generated_at",
        latest_report_generated_at,
    )
    _require_nonnegative_int(
        "discrepancy_streak_count",
        discrepancy_streak_count,
    )
    _require_optional_decimal("latest_unrealized_pnl", latest_unrealized_pnl)
    return _ReconciliationEvidenceSummary(
        source_config_version=source_config_version if report_count else None,
        source_reconciliation_report_count=report_count,
        latest_reconciliation_status=latest_reconciliation_status,
        latest_reconciliation_generated_at=latest_reconciliation_generated_at,
        latest_filled_pending_count=None,
        latest_unrealized_pnl=latest_unrealized_pnl,
        has_discrepancies=discrepancy_streak_count > 0
        or latest_reconciliation_status == "has_discrepancies",
    )


def _validate_source_reports(
    source_reports: tuple[PaperExecutionReconciliationReport, ...],
) -> None:
    for index, report in enumerate(source_reports):
        if type(report) is not PaperExecutionReconciliationReport:
            raise ValueError(
                "source reports entries must be PaperExecutionReconciliationReport",
            )
        _validate_hard_flags(f"source reports.{index}", report)


def _latest_report(
    source_reports: tuple[PaperExecutionReconciliationReport, ...],
) -> PaperExecutionReconciliationReport | None:
    latest_report: PaperExecutionReconciliationReport | None = None
    for report in source_reports:
        if latest_report is None or report.generated_at >= latest_report.generated_at:
            latest_report = report
    return latest_report


def _gate_reason_codes(
    *,
    evidence_summary: _ReconciliationEvidenceSummary,
    latest_source_age_seconds: int | None,
    config: PaperExecutionReconciliationHealthGateConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if (
        evidence_summary.source_reconciliation_report_count
        < config.min_source_reconciliation_report_count
    ):
        reason_codes.add("insufficient_paper_execution_reconciliation_source_history")
    if evidence_summary.source_reconciliation_report_count == 0:
        reason_codes.add("missing_paper_execution_reconciliation_evidence")
    if evidence_summary.has_discrepancies:
        reason_codes.add("paper_execution_reconciliation_discrepancies_present")
    if (
        latest_source_age_seconds is not None
        and latest_source_age_seconds > config.max_latest_source_age_seconds
    ):
        reason_codes.add("stale_paper_execution_reconciliation_evidence")
    if evidence_summary.latest_reconciliation_status is not None:
        if (
            evidence_summary.latest_reconciliation_status == "has_pending"
            or (
                evidence_summary.latest_filled_pending_count is not None
                and evidence_summary.latest_filled_pending_count > 0
            )
        ):
            reason_codes.add("pending_paper_execution_reconciliation_exposure")
        if (
            config.max_unrealized_loss is not None
            and evidence_summary.latest_unrealized_pnl is not None
            and evidence_summary.latest_unrealized_pnl < Decimal("0")
            and -evidence_summary.latest_unrealized_pnl > config.max_unrealized_loss
        ):
            reason_codes.add(
                "paper_execution_reconciliation_unrealized_loss_threshold_exceeded",
            )
    if not reason_codes:
        reason_codes.add(PASS_REASON_CODE)
    return tuple(sorted(reason_codes))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _latest_source_age_seconds(
    *,
    generated_at: datetime,
    source_generated_at: datetime,
) -> int:
    if source_generated_at > generated_at:
        raise ValueError("source reports must not be newer than generated_at")
    difference = generated_at - source_generated_at
    whole_seconds = difference.days * 86_400 + difference.seconds
    if difference.microseconds:
        whole_seconds += 1
    return whole_seconds


def _validate_gate_report(
    report: PaperExecutionReconciliationHealthGateReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.gate_status]:
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
    if report.source_reconciliation_report_count == 0:
        if report.source_config_version is not None:
            raise ValueError("source_config_version must be absent without source reports")
        if report.latest_reconciliation_status is not None:
            raise ValueError(
                "latest_reconciliation_status must be absent without source reports",
            )
        if report.latest_reconciliation_generated_at is not None:
            raise ValueError(
                "latest_reconciliation_generated_at must be absent without source reports",
            )
        if report.latest_source_age_seconds is not None:
            raise ValueError(
                "latest_source_age_seconds must be absent without source reports",
            )
        if report.latest_filled_pending_count is not None:
            raise ValueError(
                "latest_filled_pending_count must be absent without source reports",
            )
        if report.latest_unrealized_pnl is not None:
            raise ValueError("latest_unrealized_pnl must be absent without source reports")
    else:
        if report.source_config_version is None:
            raise ValueError("source_config_version is required with source reports")
        if report.latest_reconciliation_status is None:
            raise ValueError(
                "latest_reconciliation_status is required with source reports",
            )
        if report.latest_reconciliation_generated_at is None:
            raise ValueError(
                "latest_reconciliation_generated_at is required with source reports",
            )
        if report.latest_source_age_seconds is None:
            raise ValueError(
                "latest_source_age_seconds is required with source reports",
            )
        if report.latest_unrealized_pnl is None:
            raise ValueError("latest_unrealized_pnl is required with source reports")


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperExecutionReconciliationHealthGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    seen: set[str] = set()
    previous_sort_tuple: tuple[int, str] | None = None
    for row in rows:
        if type(row) is not PaperExecutionReconciliationHealthGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        current_sort_tuple = (-row.report_count, row.reason_code)
        if (
            previous_sort_tuple is not None
            and previous_sort_tuple > current_sort_tuple
        ):
            raise ValueError("reason_code_counts must be deterministic")
        previous_sort_tuple = current_sort_tuple
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} is required")
    seen: set[str] = set()
    previous_reason_code: str | None = None
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous_reason_code is not None and previous_reason_code > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        previous_reason_code = reason_code
        seen.add(reason_code)
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_optional_decimal(field_name, value)
    if value is not None and value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
