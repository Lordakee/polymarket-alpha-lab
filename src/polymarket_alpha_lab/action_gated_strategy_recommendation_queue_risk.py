"""Pure paper-only exposure guard for action-gated recommendation queues."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)


__all__ = (
    "PaperActionGatedStrategyRecommendationQueueRiskConfig",
    "PaperActionGatedStrategyRecommendationQueueRiskReport",
    "build_paper_action_gated_strategy_recommendation_queue_risk_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
NOTIONAL_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "allocate_paper_research_queue",
    "watch": "throttle_paper_research_queue",
    "blocked": "block_paper_research_queue",
}
BLOCKING_REASON_CODES = (
    "empty_queue_reports",
    "source_queue_blocked",
    "total_ready_notional_cap_exceeded",
    "single_queue_ready_notional_cap_exceeded",
    "ready_candidate_count_cap_exceeded",
    "candidate_count_cap_exceeded",
)
WATCH_REASON_CODES = (
    "source_queue_watch",
    "near_total_ready_notional_cap",
    "near_single_queue_ready_notional_cap",
    "near_ready_candidate_count_cap",
    "near_candidate_count_cap",
)
PASS_REASON_CODE = "queue_risk_passed"


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueRiskConfig:
    config_version: str
    max_total_ready_notional: Decimal
    max_single_queue_ready_notional: Decimal
    max_ready_candidate_count: int
    max_total_candidate_count: int
    throttle_utilization_threshold: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_total_ready_notional",
            _quantize_notional(
                "max_total_ready_notional",
                self.max_total_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "max_single_queue_ready_notional",
            _quantize_notional(
                "max_single_queue_ready_notional",
                self.max_single_queue_ready_notional,
            ),
        )
        _require_nonnegative_int(
            "max_ready_candidate_count",
            self.max_ready_candidate_count,
        )
        _require_nonnegative_int(
            "max_total_candidate_count",
            self.max_total_candidate_count,
        )
        object.__setattr__(
            self,
            "throttle_utilization_threshold",
            _quantize_ratio(
                "throttle_utilization_threshold",
                self.throttle_utilization_threshold,
            ),
        )


@dataclass(frozen=True)
class PaperActionGatedStrategyRecommendationQueueRiskReport:
    generated_at: datetime
    config_version: str
    source_config_versions: tuple[str, ...]
    status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    source_queue_count: int
    research_ready_source_count: int
    watch_source_count: int
    blocked_source_count: int
    candidate_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    blocked_reason_count: int
    watch_reason_count: int
    total_ready_notional: Decimal
    largest_queue_ready_notional: Decimal
    total_ready_notional_utilization: Decimal | None
    largest_queue_ready_notional_utilization: Decimal | None
    max_total_ready_notional: Decimal
    max_single_queue_ready_notional: Decimal
    max_ready_candidate_count: int
    max_total_candidate_count: int
    throttle_utilization_threshold: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        _require_status("status", self.status)
        _require_next_step("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "source_queue_count",
            "research_ready_source_count",
            "watch_source_count",
            "blocked_source_count",
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "blocked_reason_count",
            "watch_reason_count",
            "max_ready_candidate_count",
            "max_total_candidate_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_ready_notional",
            _quantize_notional("total_ready_notional", self.total_ready_notional),
        )
        object.__setattr__(
            self,
            "largest_queue_ready_notional",
            _quantize_notional(
                "largest_queue_ready_notional",
                self.largest_queue_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "total_ready_notional_utilization",
            _quantize_optional_utilization(
                "total_ready_notional_utilization",
                self.total_ready_notional_utilization,
            ),
        )
        object.__setattr__(
            self,
            "largest_queue_ready_notional_utilization",
            _quantize_optional_utilization(
                "largest_queue_ready_notional_utilization",
                self.largest_queue_ready_notional_utilization,
            ),
        )
        object.__setattr__(
            self,
            "max_total_ready_notional",
            _quantize_notional(
                "max_total_ready_notional",
                self.max_total_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "max_single_queue_ready_notional",
            _quantize_notional(
                "max_single_queue_ready_notional",
                self.max_single_queue_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "throttle_utilization_threshold",
            _quantize_ratio(
                "throttle_utilization_threshold",
                self.throttle_utilization_threshold,
            ),
        )
        _validate_report_consistency(self)
        _require_hard_flags("queue_risk_report", self)


def build_paper_action_gated_strategy_recommendation_queue_risk_report(
    queue_reports: object,
    *,
    config: PaperActionGatedStrategyRecommendationQueueRiskConfig,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueRiskReport:
    """Summarize paper queue exposure and recommend allocation throttling."""

    if type(config) is not PaperActionGatedStrategyRecommendationQueueRiskConfig:
        raise ValueError(
            "config must be a "
            "PaperActionGatedStrategyRecommendationQueueRiskConfig",
        )
    generated_at = _as_utc(generated_at)
    reports = _normalize_queue_reports(queue_reports)
    for report in reports:
        _validate_queue_report(report)

    source_status_counts = Counter(report.action_status for report in reports)
    candidate_count = sum(report.candidate_count for report in reports)
    ready_count = sum(report.ready_count for report in reports)
    watch_count = sum(report.watch_count for report in reports)
    blocked_count = sum(report.blocked_count for report in reports)
    total_ready_notional = _quantize_notional(
        "total_ready_notional",
        sum((report.total_ready_notional for report in reports), ZERO),
    )
    largest_queue_ready_notional = _quantize_notional(
        "largest_queue_ready_notional",
        max((report.total_ready_notional for report in reports), default=ZERO),
    )
    total_ready_notional_utilization = _optional_utilization(
        total_ready_notional,
        config.max_total_ready_notional,
    )
    largest_queue_ready_notional_utilization = _optional_utilization(
        largest_queue_ready_notional,
        config.max_single_queue_ready_notional,
    )
    reason_codes = _risk_reason_codes(
        source_queue_count=len(reports),
        watch_source_count=source_status_counts["watch"],
        blocked_source_count=source_status_counts["blocked"],
        candidate_count=candidate_count,
        ready_count=ready_count,
        total_ready_notional=total_ready_notional,
        largest_queue_ready_notional=largest_queue_ready_notional,
        total_ready_notional_utilization=total_ready_notional_utilization,
        largest_queue_ready_notional_utilization=(
            largest_queue_ready_notional_utilization
        ),
        max_total_ready_notional=config.max_total_ready_notional,
        max_single_queue_ready_notional=config.max_single_queue_ready_notional,
        max_ready_candidate_count=config.max_ready_candidate_count,
        max_total_candidate_count=config.max_total_candidate_count,
        throttle_utilization_threshold=config.throttle_utilization_threshold,
    )
    status = _status_from_reason_codes(reason_codes)

    return PaperActionGatedStrategyRecommendationQueueRiskReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_versions=_source_config_versions(reports),
        status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        reason_codes=reason_codes,
        source_queue_count=len(reports),
        research_ready_source_count=source_status_counts["research_ready"],
        watch_source_count=source_status_counts["watch"],
        blocked_source_count=source_status_counts["blocked"],
        candidate_count=candidate_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        blocked_reason_count=_blocked_reason_count(reason_codes),
        watch_reason_count=_watch_reason_count(reason_codes),
        total_ready_notional=total_ready_notional,
        largest_queue_ready_notional=largest_queue_ready_notional,
        total_ready_notional_utilization=total_ready_notional_utilization,
        largest_queue_ready_notional_utilization=(
            largest_queue_ready_notional_utilization
        ),
        max_total_ready_notional=config.max_total_ready_notional,
        max_single_queue_ready_notional=config.max_single_queue_ready_notional,
        max_ready_candidate_count=config.max_ready_candidate_count,
        max_total_candidate_count=config.max_total_candidate_count,
        throttle_utilization_threshold=config.throttle_utilization_threshold,
    )


def _normalize_queue_reports(
    value: object,
) -> tuple[PaperActionGatedStrategyRecommendationQueueReport, ...]:
    if type(value) is PaperActionGatedStrategyRecommendationQueueReport:
        return (value,)
    if isinstance(value, (str, bytes)):
        raise ValueError("queue_reports must be an iterable")
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("queue_reports must be an iterable") from exc


def _validate_queue_report(report: object) -> None:
    if type(report) is not PaperActionGatedStrategyRecommendationQueueReport:
        raise ValueError(
            "queue_reports must contain "
            "PaperActionGatedStrategyRecommendationQueueReport values",
        )
    _require_hard_flags("queue_report", report)


def _source_config_versions(
    reports: tuple[PaperActionGatedStrategyRecommendationQueueReport, ...],
) -> tuple[str, ...]:
    return tuple(sorted({report.config_version for report in reports}))


def _risk_reason_codes(
    *,
    source_queue_count: int,
    watch_source_count: int,
    blocked_source_count: int,
    candidate_count: int,
    ready_count: int,
    total_ready_notional: Decimal,
    largest_queue_ready_notional: Decimal,
    total_ready_notional_utilization: Decimal | None,
    largest_queue_ready_notional_utilization: Decimal | None,
    max_total_ready_notional: Decimal,
    max_single_queue_ready_notional: Decimal,
    max_ready_candidate_count: int,
    max_total_candidate_count: int,
    throttle_utilization_threshold: Decimal,
) -> tuple[str, ...]:
    blocking_reasons: list[str] = []
    watch_reasons: list[str] = []

    if source_queue_count == 0:
        blocking_reasons.append("empty_queue_reports")
    if blocked_source_count > 0:
        blocking_reasons.append("source_queue_blocked")
    if total_ready_notional > max_total_ready_notional:
        blocking_reasons.append("total_ready_notional_cap_exceeded")
    elif (
        total_ready_notional_utilization is not None
        and total_ready_notional_utilization >= throttle_utilization_threshold
    ):
        watch_reasons.append("near_total_ready_notional_cap")
    if largest_queue_ready_notional > max_single_queue_ready_notional:
        blocking_reasons.append("single_queue_ready_notional_cap_exceeded")
    elif (
        largest_queue_ready_notional_utilization is not None
        and largest_queue_ready_notional_utilization >= throttle_utilization_threshold
    ):
        watch_reasons.append("near_single_queue_ready_notional_cap")
    if ready_count > max_ready_candidate_count:
        blocking_reasons.append("ready_candidate_count_cap_exceeded")
    elif max_ready_candidate_count > 0 and ready_count == max_ready_candidate_count:
        watch_reasons.append("near_ready_candidate_count_cap")
    if candidate_count > max_total_candidate_count:
        blocking_reasons.append("candidate_count_cap_exceeded")
    elif max_total_candidate_count > 0 and candidate_count == max_total_candidate_count:
        watch_reasons.append("near_candidate_count_cap")
    if watch_source_count > 0:
        watch_reasons.append("source_queue_watch")

    if blocking_reasons:
        return tuple(blocking_reasons)
    if watch_reasons:
        return tuple(watch_reasons)
    return (PASS_REASON_CODE,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _blocked_reason_count(reason_codes: tuple[str, ...]) -> int:
    return sum(1 for reason_code in reason_codes if reason_code in BLOCKING_REASON_CODES)


def _watch_reason_count(reason_codes: tuple[str, ...]) -> int:
    return sum(1 for reason_code in reason_codes if reason_code in WATCH_REASON_CODES)


def _validate_report_consistency(
    report: PaperActionGatedStrategyRecommendationQueueRiskReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if (
        report.source_queue_count
        != report.research_ready_source_count
        + report.watch_source_count
        + report.blocked_source_count
    ):
        raise ValueError("source_queue_count must match source status counts")
    if report.candidate_count != report.ready_count + report.watch_count + report.blocked_count:
        raise ValueError("candidate_count must match candidate status counts")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.blocked_reason_count != _blocked_reason_count(report.reason_codes):
        raise ValueError("blocked_reason_count must match reason_codes")
    if report.watch_reason_count != _watch_reason_count(report.reason_codes):
        raise ValueError("watch_reason_count must match reason_codes")
    expected_total_utilization = _optional_utilization(
        report.total_ready_notional,
        report.max_total_ready_notional,
    )
    if report.total_ready_notional_utilization != expected_total_utilization:
        raise ValueError(
            "total_ready_notional_utilization must match total_ready_notional",
        )
    expected_largest_utilization = _optional_utilization(
        report.largest_queue_ready_notional,
        report.max_single_queue_ready_notional,
    )
    if report.largest_queue_ready_notional_utilization != expected_largest_utilization:
        raise ValueError(
            "largest_queue_ready_notional_utilization must match "
            "largest_queue_ready_notional",
        )
    expected_reason_codes = _risk_reason_codes(
        source_queue_count=report.source_queue_count,
        watch_source_count=report.watch_source_count,
        blocked_source_count=report.blocked_source_count,
        candidate_count=report.candidate_count,
        ready_count=report.ready_count,
        total_ready_notional=report.total_ready_notional,
        largest_queue_ready_notional=report.largest_queue_ready_notional,
        total_ready_notional_utilization=report.total_ready_notional_utilization,
        largest_queue_ready_notional_utilization=(
            report.largest_queue_ready_notional_utilization
        ),
        max_total_ready_notional=report.max_total_ready_notional,
        max_single_queue_ready_notional=report.max_single_queue_ready_notional,
        max_ready_candidate_count=report.max_ready_candidate_count,
        max_total_candidate_count=report.max_total_candidate_count,
        throttle_utilization_threshold=report.throttle_utilization_threshold,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match queue risk metrics")


def _normalize_source_config_versions(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_config_versions must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("source_config_versions must be an iterable") from exc
    if len(set(items)) != len(items):
        raise ValueError("source_config_versions must not contain duplicates")
    for item in items:
        _require_canonical_string("source_config_versions", item)
    return items


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError("reason_codes must not contain duplicates")
    allowed = set(BLOCKING_REASON_CODES) | set(WATCH_REASON_CODES) | {PASS_REASON_CODE}
    for item in items:
        _require_canonical_string("reason_codes", item)
        if item not in allowed:
            raise ValueError("reason_codes must match queue risk semantics")
    return items


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in set(NEXT_STEP_BY_STATUS.values()):
        raise ValueError(f"{field_name} must be a known next step")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_notional(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value).quantize(NOTIONAL_QUANTUM)


def _quantize_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if ratio > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return ratio


def _quantize_utilization(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _quantize_optional_utilization(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _quantize_utilization(field_name, value)


def _optional_utilization(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return _quantize_utilization("utilization", numerator / denominator)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
