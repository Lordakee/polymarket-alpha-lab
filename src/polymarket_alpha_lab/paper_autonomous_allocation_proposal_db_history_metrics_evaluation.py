"""Pure evaluation reducer for persisted allocation proposal metrics.

Operators: v0 evaluates exactly one metrics report into deterministic
pass/watch/blocked diagnostics for paper-only research use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext, Context

__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION",
    "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig",
    "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount",
    "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics",
    "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport",
    "build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report",
)

DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION = (
    "paper-autonomous-allocation-proposal-db-history-metrics-evaluation-v0"
)

DEFAULT_DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")
TOP_REASON_CODE_LIMIT = 6

NEXT_STEP_BY_STATUS = {
    "pass": "review_paper_autonomous_allocation_proposal",
    "watch": "hold_paper_autonomous_allocation_proposal",
    "blocked": "block_paper_autonomous_allocation_proposal",
}

ALLOWED_REASON_CODES = (
    "missing_paper_autonomous_allocation_proposal_metrics_source_history",
    "stale_paper_autonomous_allocation_proposal_metrics_latest_report",
    "metrics_budget_utilization_watch",
    "metrics_requested_fill_ratio_watch",
    "metrics_concentration_market_watch",
    "metrics_concentration_event_watch",
    "metrics_concentration_theme_watch",
    "metrics_concentration_correlation_group_watch",
    "metrics_churn_share_watch",
    "metrics_edge_coverage_watch",
    "metrics_edge_quality_watch",
    "paper_autonomous_allocation_proposal_metrics_evaluation_passed",
)

_BLOCKED_REASON_CODES = frozenset(
    {
        "missing_paper_autonomous_allocation_proposal_metrics_source_history",
    }
)
_WATCH_REASON_CODES = frozenset(
    {
        "stale_paper_autonomous_allocation_proposal_metrics_latest_report",
        "metrics_budget_utilization_watch",
        "metrics_requested_fill_ratio_watch",
        "metrics_concentration_market_watch",
        "metrics_concentration_event_watch",
        "metrics_concentration_theme_watch",
        "metrics_concentration_correlation_group_watch",
        "metrics_churn_share_watch",
        "metrics_edge_coverage_watch",
        "metrics_edge_quality_watch",
    }
)
_PASS_REASON_CODE = "paper_autonomous_allocation_proposal_metrics_evaluation_passed"
_GROUP_TYPE_TO_REASON_CODE = {
    "market": "metrics_concentration_market_watch",
    "event": "metrics_concentration_event_watch",
    "theme": "metrics_concentration_theme_watch",
    "correlation_group": "metrics_concentration_correlation_group_watch",
}
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig:
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_METRICS_EVALUATION_CONFIG_VERSION
    )
    min_source_report_count: int = 1
    max_latest_age_seconds: int = 86_400
    max_budget_utilization: Decimal = Decimal("0.900000")
    min_requested_fill_ratio: Decimal = Decimal("0.300000")
    max_concentration_share: Decimal = Decimal("0.600000")
    max_churn_share: Decimal = Decimal("0.600000")
    min_edge_coverage: Decimal = Decimal("0.250000")
    max_expected_edge_notional_share: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig:
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig:
            raise ValueError(
                "config must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("min_source_report_count", self.min_source_report_count)
        _require_nonnegative_int("max_latest_age_seconds", self.max_latest_age_seconds)
        for field_name in (
            "max_budget_utilization",
            "min_requested_fill_ratio",
            "max_concentration_share",
            "max_churn_share",
            "min_edge_coverage",
            "max_expected_edge_notional_share",
        ):
            _require_quantized_decimal(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)




@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if (
            cls
            is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount
        ):
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics:
    evaluated_min_source_report_count: bool
    evaluated_latest_age: bool
    evaluated_budget_utilization: bool
    evaluated_requested_fill_ratio: bool
    evaluated_concentration: bool
    evaluated_churn: bool
    evaluated_edge_coverage: bool
    evaluated_edge_quality: bool
    source_report_count: int
    latest_source_age_seconds: int | None
    latest_budget_utilization: Decimal | None
    latest_requested_fill_ratio: Decimal | None
    largest_concentration_group_type: str | None
    largest_concentration_share: Decimal | None
    churn_share: Decimal | None
    latest_allocated_edge_share: Decimal | None
    latest_expected_edge_notional_share: Decimal | None
    top_reason_codes: tuple[str, ...]
    top_reason_code_limit: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if (
            cls
            is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics
        ):
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics
        ):
            raise ValueError(
                "diagnostics must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics",
            )
        _require_nonnegative_int("source_report_count", self.source_report_count)
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        _require_optional_quantized_decimal(
            "latest_budget_utilization",
            self.latest_budget_utilization,
        )
        _require_optional_quantized_decimal(
            "latest_requested_fill_ratio",
            self.latest_requested_fill_ratio,
        )
        if self.largest_concentration_group_type is not None:
            _require_canonical_string(
                "largest_concentration_group_type",
                self.largest_concentration_group_type,
            )
        _require_optional_quantized_decimal(
            "largest_concentration_share",
            self.largest_concentration_share,
        )
        _require_optional_quantized_decimal("churn_share", self.churn_share)
        _require_optional_quantized_decimal(
            "latest_allocated_edge_share",
            self.latest_allocated_edge_share,
        )
        _require_optional_quantized_decimal(
            "latest_expected_edge_notional_share",
            self.latest_expected_edge_notional_share,
        )
        _require_positive_int("top_reason_code_limit", self.top_reason_code_limit)
        _validate_hard_flags("diagnostics", self)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    generated_at: datetime
    config_version: str
    evaluation_status: str
    recommended_next_step: str
    source_report_count: int
    latest_report_generated_at: datetime | None
    reason_code_counts: tuple[
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    diagnostics: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if (
            cls
            is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport
        ):
            raise TypeError(
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport
        ):
            raise ValueError(
                "evaluation report must be exactly "
                "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "latest_report_generated_at",
            _as_optional_utc(
                "latest_report_generated_at",
                self.latest_report_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("evaluation_status", self.evaluation_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("source_report_count", self.source_report_count)
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
        _validate_report_consistency(self)
        _validate_hard_flags("evaluation report", self)


def build_paper_autonomous_allocation_proposal_db_history_metrics_evaluation_report(
    metrics_report: object,
    *,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
    generated_at: datetime,
) -> PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport:
    # The reducer consumes an existing metrics report from the sibling metrics
    # module. Keep the import local to avoid hard coupling in the module header
    # while still requiring an exact typed input at runtime.
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics import (
        PaperAutonomousAllocationProposalDbHistoryMetricsReport,
    )

    if (
        type(config)
        is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig
    ):
        raise ValueError(
            "config must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig",
        )
    if (
        type(metrics_report)
        is not PaperAutonomousAllocationProposalDbHistoryMetricsReport
    ):
        raise ValueError(
            "metrics_report must be a "
            "PaperAutonomousAllocationProposalDbHistoryMetricsReport",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)

    with localcontext(DEFAULT_DECIMAL_CONTEXT):
        source_report_count = int(metrics_report.source_report_count)
        latest_report_generated_at = metrics_report.latest_report_generated_at
        age_seconds = _age_seconds(
            generated_at_utc=generated_at_utc,
            latest_report_generated_at=latest_report_generated_at,
        )
        latest_budget_utilization = _optional_quantized_decimal(
            metrics_report.latest_budget_utilization,
        )
        latest_requested_fill_ratio = _optional_quantized_decimal(
            metrics_report.latest_requested_fill_ratio,
        )
        largest_concentration_group_type, largest_concentration_share = (
            _largest_concentration_pair(
                concentration_rows=metrics_report.latest_largest_concentration_rows,
            )
        )
        churn_share = _churn_share(
            latest_notional_turnover=metrics_report.latest_notional_turnover,
            latest_total_allocated_paper_notional=(
                metrics_report.latest_total_allocated_paper_notional
            ),
        )
        latest_allocated_edge_share = _optional_quantized_decimal(
            metrics_report.latest_allocated_edge_share,
        )
        latest_expected_edge_notional_share = _optional_quantized_decimal(
            metrics_report.latest_expected_edge_notional_share,
        )

        reason_codes, evaluated_flags = _evaluation_reason_codes(
            source_report_count=source_report_count,
            age_seconds=age_seconds,
            latest_budget_utilization=latest_budget_utilization,
            latest_requested_fill_ratio=latest_requested_fill_ratio,
            concentration_rows=metrics_report.latest_largest_concentration_rows,
            churn_share=churn_share,
            latest_allocated_edge_share=latest_allocated_edge_share,
            latest_expected_edge_notional_share=latest_expected_edge_notional_share,
            config=config,
        )

    evaluation_status = _evaluation_status(reason_codes)
    reason_code_counts = tuple(
        PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount(
            reason_code=reason_code,
            report_count=1,
        )
        for reason_code in reason_codes
    )
    top_reason_codes = reason_codes[:TOP_REASON_CODE_LIMIT]
    diagnostics = PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationDiagnostics(
        evaluated_min_source_report_count=evaluated_flags["min_source_report_count"],
        evaluated_latest_age=evaluated_flags["latest_age"],
        evaluated_budget_utilization=evaluated_flags["budget_utilization"],
        evaluated_requested_fill_ratio=evaluated_flags["requested_fill_ratio"],
        evaluated_concentration=evaluated_flags["concentration"],
        evaluated_churn=evaluated_flags["churn"],
        evaluated_edge_coverage=evaluated_flags["edge_coverage"],
        evaluated_edge_quality=evaluated_flags["edge_quality"],
        source_report_count=source_report_count,
        latest_source_age_seconds=age_seconds,
        latest_budget_utilization=latest_budget_utilization,
        latest_requested_fill_ratio=latest_requested_fill_ratio,
        largest_concentration_group_type=largest_concentration_group_type,
        largest_concentration_share=largest_concentration_share,
        churn_share=churn_share,
        latest_allocated_edge_share=latest_allocated_edge_share,
        latest_expected_edge_notional_share=latest_expected_edge_notional_share,
        top_reason_codes=top_reason_codes,
        top_reason_code_limit=TOP_REASON_CODE_LIMIT,
    )
    return PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        evaluation_status=evaluation_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[evaluation_status],
        source_report_count=source_report_count,
        latest_report_generated_at=latest_report_generated_at,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        diagnostics=diagnostics,
    )


def _evaluation_reason_codes(
    *,
    source_report_count: int,
    age_seconds: int | None,
    latest_budget_utilization: Decimal | None,
    latest_requested_fill_ratio: Decimal | None,
    concentration_rows: object,
    churn_share: Decimal | None,
    latest_allocated_edge_share: Decimal | None,
    latest_expected_edge_notional_share: Decimal | None,
    config: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationConfig,
) -> tuple[tuple[str, ...], dict[str, bool]]:
    reason_codes: list[str] = []
    evaluated = {
        "min_source_report_count": True,
        "latest_age": False,
        "budget_utilization": False,
        "requested_fill_ratio": False,
        "concentration": False,
        "churn": False,
        "edge_coverage": False,
        "edge_quality": False,
    }
    if source_report_count < config.min_source_report_count:
        reason_codes.append(
            "missing_paper_autonomous_allocation_proposal_metrics_source_history",
        )
        return tuple(sorted(set(reason_codes))), evaluated

    evaluated["latest_age"] = True
    if age_seconds is None:
        evaluated["latest_age"] = False
    elif age_seconds < 0:
        raise ValueError("latest_source_age_seconds must not be negative")
    elif age_seconds > config.max_latest_age_seconds:
        reason_codes.append(
            "stale_paper_autonomous_allocation_proposal_metrics_latest_report",
        )

    if latest_budget_utilization is not None:
        evaluated["budget_utilization"] = True
        if latest_budget_utilization > config.max_budget_utilization:
            reason_codes.append("metrics_budget_utilization_watch")

    if latest_requested_fill_ratio is not None:
        evaluated["requested_fill_ratio"] = True
        if latest_requested_fill_ratio < config.min_requested_fill_ratio:
            reason_codes.append("metrics_requested_fill_ratio_watch")

    concentration_breaches = _concentration_reason_codes(
        concentration_rows=concentration_rows,
        max_concentration_share=config.max_concentration_share,
    )
    if concentration_breaches:
        evaluated["concentration"] = True
        reason_codes.extend(concentration_breaches)

    if churn_share is not None:
        evaluated["churn"] = True
        if churn_share > config.max_churn_share:
            reason_codes.append("metrics_churn_share_watch")

    if latest_allocated_edge_share is not None:
        evaluated["edge_coverage"] = True
        if latest_allocated_edge_share < config.min_edge_coverage:
            reason_codes.append("metrics_edge_coverage_watch")

    if latest_expected_edge_notional_share is not None:
        evaluated["edge_quality"] = True
        if latest_expected_edge_notional_share > config.max_expected_edge_notional_share:
            reason_codes.append("metrics_edge_quality_watch")

    if not reason_codes:
        reason_codes.append(_PASS_REASON_CODE)

    return tuple(sorted(set(reason_codes))), evaluated


def _concentration_reason_codes(
    *,
    concentration_rows: object,
    max_concentration_share: Decimal,
) -> tuple[str, ...]:
    if not isinstance(concentration_rows, (tuple, list)):
        raise ValueError("concentration_rows must be a tuple or list")
    breaches: list[str] = []
    for row in concentration_rows:
        group_type = getattr(row, "group_type", None)
        allocated_paper_notional_share = getattr(
            row,
            "allocated_paper_notional_share",
            None,
        )
        if group_type not in _GROUP_TYPE_TO_REASON_CODE:
            raise ValueError("group_type must be known")
        if allocated_paper_notional_share is None:
            continue
        if not isinstance(allocated_paper_notional_share, Decimal):
            raise ValueError("allocated_paper_notional_share must be a Decimal")
        if allocated_paper_notional_share > max_concentration_share:
            breaches.append(_GROUP_TYPE_TO_REASON_CODE[group_type])
    return tuple(sorted(set(breaches)))


def _largest_concentration_pair(
    *,
    concentration_rows: object,
) -> tuple[str | None, Decimal | None]:
    if not isinstance(concentration_rows, (tuple, list)):
        raise ValueError("concentration_rows must be a tuple or list")
    if not concentration_rows:
        return None, None
    # Prefer breach set implicitly by evaluating all rows and choosing the
    # largest share; ties are broken by descending share and alphabetical
    # group_type, which matches the metrics report ordering contract.
    best_type: str | None = None
    best_share: Decimal | None = None
    for row in concentration_rows:
        group_type = str(getattr(row, "group_type"))
        share = getattr(row, "allocated_paper_notional_share", None)
        if share is None:
            continue
        if not isinstance(share, Decimal):
            raise ValueError("allocated_paper_notional_share must be a Decimal")
        if best_share is None or (share, group_type) > (best_share, str(best_type)):
            best_type = group_type
            best_share = share
    return best_type, best_share


def _churn_share(
    *,
    latest_notional_turnover: object,
    latest_total_allocated_paper_notional: object,
) -> Decimal | None:
    if latest_total_allocated_paper_notional is None:
        return None
    if not isinstance(latest_total_allocated_paper_notional, Decimal):
        raise ValueError(
            "latest_total_allocated_paper_notional must be a Decimal or None",
        )
    if not isinstance(latest_notional_turnover, Decimal):
        raise ValueError("latest_notional_turnover must be a Decimal")
    if latest_total_allocated_paper_notional <= ZERO:
        return None
    return _quantize(latest_notional_turnover / latest_total_allocated_paper_notional)


def _evaluation_status(reason_codes: tuple[str, ...]) -> str:
    if any(code in _BLOCKED_REASON_CODES for code in reason_codes):
        return "blocked"
    if any(code in _WATCH_REASON_CODES for code in reason_codes):
        return "watch"
    return "pass"


def _age_seconds(
    *,
    generated_at_utc: datetime,
    latest_report_generated_at: datetime | None,
) -> int | None:
    if latest_report_generated_at is None:
        return None
    latest_utc = _as_utc("latest_report_generated_at", latest_report_generated_at)
    return int((generated_at_utc - latest_utc).total_seconds())


def _validate_report_consistency(
    report: PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.evaluation_status]:
        raise ValueError("recommended_next_step must match evaluation_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if any(row.report_count != 1 for row in report.reason_code_counts):
        raise ValueError("reason_code_counts must be presence counts")
    if report.evaluation_status != _evaluation_status(report.reason_codes):
        raise ValueError("evaluation_status must match reason_codes")
    has_pass_reason = _PASS_REASON_CODE in report.reason_codes
    has_other_reason = any(
        code in _BLOCKED_REASON_CODES or code in _WATCH_REASON_CODES
        for code in report.reason_codes
    )
    if has_pass_reason and has_other_reason:
        raise ValueError("pass reason must not be mixed with watch or blocked reasons")
    if tuple(report.reason_codes[:TOP_REASON_CODE_LIMIT]) != tuple(
        report.diagnostics.top_reason_codes
    ):
        raise ValueError("top_reason_codes must be the leading actual reason codes")


def _normalize_reason_code_counts(
    value: object,
) -> tuple[
    PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount,
    ...,
]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    seen: set[str] = set()
    previous_key: tuple[int, str] | None = None
    for row in rows:
        if (
            type(row)
            is not PaperAutonomousAllocationProposalDbHistoryMetricsEvaluationReasonCodeCount
        ):
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
        if reason_code not in ALLOWED_REASON_CODES:
            raise ValueError(f"{field_name} contains an unallowed reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _optional_quantized_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if not isinstance(value, Decimal):
        raise ValueError("metric decimal must be a Decimal or None")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


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


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in NEXT_STEP_BY_STATUS:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_quantized_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if value != Decimal(value).quantize(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_optional_quantized_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_quantized_decimal(field_name, value)


def _validate_hard_flags(label: str, obj: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        value = getattr(obj, field_name, None)
        if value is not True:
            raise ValueError(f"{field_name} must be True for {label}")
