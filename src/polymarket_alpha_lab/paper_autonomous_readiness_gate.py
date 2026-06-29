"""Pure reducer for paper autonomous readiness gate reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend_gate import (
    PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport,
)
from polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_trend_gate import (
    PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport,
)
from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_history_health import (
    PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport,
)
from polymarket_alpha_lab.paper_strategy_cycle_report_history_gate import (
    PaperStrategyCycleReportHistoryGateReport,
)
from polymarket_alpha_lab.paper_strategy_risk_audit_history_gate import (
    PaperStrategyRiskAuditHistoryGateReport,
)


DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_CONFIG_VERSION = (
    "paper-autonomous-readiness-gate-v0"
)
READINESS_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_readiness_review",
    "watch": "throttle_paper_autonomous_readiness_review",
    "blocked": "block_paper_autonomous_readiness_review",
}
PASS_REASON_CODE = "paper_autonomous_readiness_gate_passed"
SCREENING_SOURCE_NAME = "screening_decision_support_gate_db_history_health"
STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME = "strategy_cycle_report_history_gate"
ALLOCATION_SOURCE_NAME = "allocation_proposal_db_history_health_trend_gate"
INVESTMENT_LEDGER_SOURCE_NAME = "investment_ledger_db_history_health_trend_gate"
STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME = "strategy_risk_audit_history_gate"
CANONICAL_SOURCE_NAMES = (
    SCREENING_SOURCE_NAME,
    STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
    STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
)
REQUIRED_SOURCE_NAMES = (
    SCREENING_SOURCE_NAME,
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
)
SOURCE_NAMES = CANONICAL_SOURCE_NAMES

__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_CONFIG_VERSION",
    "PaperAutonomousReadinessGateConfig",
    "PaperAutonomousReadinessGateReasonCodeCount",
    "PaperAutonomousReadinessGateSourceStatus",
    "PaperAutonomousReadinessGateReport",
    "build_paper_autonomous_readiness_gate_report",
)


@dataclass(frozen=True)
class PaperAutonomousReadinessGateConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_READINESS_GATE_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessGateConfig:
            raise TypeError(
                "PaperAutonomousReadinessGateConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessGateConfig:
            raise ValueError(
                "config must be exactly PaperAutonomousReadinessGateConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousReadinessGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessGateReasonCodeCount:
            raise TypeError(
                "PaperAutonomousReadinessGateReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessGateReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperAutonomousReadinessGateReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousReadinessGateSourceStatus:
    source_name: str
    status: str
    recommended_next_step: str
    generated_at: datetime
    config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessGateSourceStatus:
            raise TypeError(
                "PaperAutonomousReadinessGateSourceStatus "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessGateSourceStatus:
            raise ValueError(
                "source status must be exactly "
                "PaperAutonomousReadinessGateSourceStatus",
            )
        _require_source_name("source_name", self.source_name)
        _require_readiness_status("status", self.status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _validate_hard_flags("source status", self)


@dataclass(frozen=True)
class PaperAutonomousReadinessGateReport:
    generated_at: datetime
    config_version: str
    readiness_status: str
    recommended_next_step: str
    source_statuses: tuple[PaperAutonomousReadinessGateSourceStatus, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[PaperAutonomousReadinessGateReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousReadinessGateReport:
            raise TypeError(
                "PaperAutonomousReadinessGateReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousReadinessGateReport:
            raise ValueError(
                "readiness report must be exactly PaperAutonomousReadinessGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_readiness_status("readiness_status", self.readiness_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "source_statuses",
            _normalize_source_statuses(self.source_statuses),
        )
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
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
        _validate_readiness_report(self)
        _validate_hard_flags("readiness report", self)


def build_paper_autonomous_readiness_gate_report(
    screening_report: object,
    allocation_report: object,
    investment_ledger_report: object,
    *,
    config: PaperAutonomousReadinessGateConfig,
    generated_at: datetime,
    strategy_cycle_history_gate_report: object | None = None,
    strategy_risk_audit_history_gate_report: object | None = None,
) -> PaperAutonomousReadinessGateReport:
    if type(screening_report) is not PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport:
        raise ValueError(
            "screening_report must be a "
            "PaperAutonomousScreeningDecisionSupportGateDbHistoryHealthReport",
        )
    if (
        type(allocation_report)
        is not PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport
    ):
        raise ValueError(
            "allocation_report must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthTrendGateReport",
        )
    if (
        type(investment_ledger_report)
        is not PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport
    ):
        raise ValueError(
            "investment_ledger_report must be a "
            "PaperAutonomousInvestmentLedgerDbHistoryHealthTrendGateReport",
        )
    if (
        strategy_cycle_history_gate_report is not None
        and type(strategy_cycle_history_gate_report)
        is not PaperStrategyCycleReportHistoryGateReport
    ):
        raise ValueError(
            "strategy_cycle_history_gate_report must be a "
            "PaperStrategyCycleReportHistoryGateReport",
        )
    if (
        strategy_risk_audit_history_gate_report is not None
        and type(strategy_risk_audit_history_gate_report)
        is not PaperStrategyRiskAuditHistoryGateReport
    ):
        raise ValueError(
            "strategy_risk_audit_history_gate_report must be a "
            "PaperStrategyRiskAuditHistoryGateReport",
        )
    if type(config) is not PaperAutonomousReadinessGateConfig:
        raise ValueError("config must be a PaperAutonomousReadinessGateConfig")

    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)
    _validate_hard_flags("screening_report", screening_report)
    _validate_hard_flags("allocation_report", allocation_report)
    _validate_hard_flags("investment_ledger_report", investment_ledger_report)
    if strategy_cycle_history_gate_report is not None:
        _validate_hard_flags(
            "strategy_cycle_history_gate_report",
            strategy_cycle_history_gate_report,
        )
    if strategy_risk_audit_history_gate_report is not None:
        _validate_hard_flags(
            "strategy_risk_audit_history_gate_report",
            strategy_risk_audit_history_gate_report,
        )

    source_statuses = [
        PaperAutonomousReadinessGateSourceStatus(
            source_name=SCREENING_SOURCE_NAME,
            status=screening_report.health_status,
            recommended_next_step=screening_report.recommended_next_step,
            generated_at=screening_report.generated_at,
            config_version=screening_report.config_version,
        ),
    ]
    if strategy_cycle_history_gate_report is not None:
        source_statuses.append(
            PaperAutonomousReadinessGateSourceStatus(
                source_name=STRATEGY_CYCLE_HISTORY_GATE_SOURCE_NAME,
                status=strategy_cycle_history_gate_report.gate_status,
                recommended_next_step=(
                    strategy_cycle_history_gate_report.recommended_next_step
                ),
                generated_at=strategy_cycle_history_gate_report.generated_at,
                config_version=strategy_cycle_history_gate_report.config_version,
            ),
        )
    source_statuses.extend(
        (
            PaperAutonomousReadinessGateSourceStatus(
                source_name=ALLOCATION_SOURCE_NAME,
                status=allocation_report.gate_status,
                recommended_next_step=allocation_report.recommended_next_step,
                generated_at=allocation_report.generated_at,
                config_version=allocation_report.config_version,
            ),
            PaperAutonomousReadinessGateSourceStatus(
                source_name=INVESTMENT_LEDGER_SOURCE_NAME,
                status=investment_ledger_report.gate_status,
                recommended_next_step=investment_ledger_report.recommended_next_step,
                generated_at=investment_ledger_report.generated_at,
                config_version=investment_ledger_report.config_version,
            ),
        ),
    )
    if strategy_risk_audit_history_gate_report is not None:
        source_statuses.append(
            PaperAutonomousReadinessGateSourceStatus(
                source_name=STRATEGY_RISK_AUDIT_HISTORY_GATE_SOURCE_NAME,
                status=strategy_risk_audit_history_gate_report.gate_status,
                recommended_next_step=(
                    strategy_risk_audit_history_gate_report.recommended_next_step
                ),
                generated_at=strategy_risk_audit_history_gate_report.generated_at,
                config_version=strategy_risk_audit_history_gate_report.config_version,
            ),
        )
    source_statuses_tuple = tuple(source_statuses)
    source_config_versions = tuple(
        (row.source_name, row.config_version) for row in source_statuses_tuple
    )
    reason_codes = _readiness_reason_codes(source_statuses_tuple)
    readiness_status = _readiness_status(source_statuses_tuple)

    return PaperAutonomousReadinessGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        readiness_status=readiness_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[readiness_status],
        source_statuses=source_statuses_tuple,
        source_config_versions=source_config_versions,
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def _readiness_status(
    source_statuses: tuple[PaperAutonomousReadinessGateSourceStatus, ...],
) -> str:
    if any(row.status == "blocked" for row in source_statuses):
        return "blocked"
    if any(row.status == "watch" for row in source_statuses):
        return "watch"
    return "pass"


def _readiness_reason_codes(
    source_statuses: tuple[PaperAutonomousReadinessGateSourceStatus, ...],
) -> tuple[str, ...]:
    reason_codes = [
        f"{row.source_name}_{row.status}"
        for row in source_statuses
    ]
    if _readiness_status(source_statuses) == "pass":
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousReadinessGateReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        if reason_code in counts:
            counts[reason_code] += 1
        else:
            counts[reason_code] = 1
    return tuple(
        PaperAutonomousReadinessGateReasonCodeCount(reason_code, report_count)
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _validate_readiness_report(report: PaperAutonomousReadinessGateReport) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.readiness_status]:
        raise ValueError("recommended_next_step must match readiness_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.readiness_status != _readiness_status(report.source_statuses):
        raise ValueError("readiness_status must match source statuses")
    if report.reason_codes != _readiness_reason_codes(report.source_statuses):
        raise ValueError("reason_codes must match source statuses")
    if report.source_config_versions != tuple(
        (row.source_name, row.config_version) for row in report.source_statuses
    ):
        raise ValueError("source_config_versions must match source_statuses")


def _normalize_source_statuses(
    value: object,
) -> tuple[PaperAutonomousReadinessGateSourceStatus, ...]:
    if type(value) is not tuple:
        raise ValueError("source_statuses must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not PaperAutonomousReadinessGateSourceStatus:
            raise ValueError("source_statuses must contain exact source status rows")
    _validate_source_name_sequence(
        "source_statuses",
        tuple(row.source_name for row in rows),
    )
    return rows


def _normalize_source_config_versions(
    value: object,
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    rows: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain source/version pairs")
        source_name, config_version = item
        _require_source_name("source_config_versions", source_name)
        _require_canonical_string("source_config_versions", config_version)
        rows.append((source_name, config_version))
    _validate_source_name_sequence(
        "source_config_versions",
        tuple(source_name for source_name, _config_version in rows),
    )
    return tuple(rows)


def _validate_source_name_sequence(field_name: str, source_names: tuple[str, ...]) -> None:
    if len(set(source_names)) != len(source_names):
        raise ValueError(f"{field_name} must not contain duplicate sources")
    if not set(REQUIRED_SOURCE_NAMES).issubset(source_names):
        raise ValueError(f"{field_name} must contain required sources")
    if source_names != tuple(
        name for name in CANONICAL_SOURCE_NAMES if name in source_names
    ):
        raise ValueError(f"{field_name} must contain the canonical source sequence")


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousReadinessGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    seen: set[str] = set()
    previous_key: tuple[int, str] | None = None
    for row in rows:
        if type(row) is not PaperAutonomousReadinessGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} is required")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_source_name(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_NAMES:
        raise ValueError(f"{field_name} must be a known source name")


def _require_readiness_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in READINESS_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
