"""Pure public-safe forecast review rotation report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_FORECAST_REVIEW_ROTATION_REPORT_CONFIG_VERSION = (
    "research-team-forecast-review-rotation-report-v1"
)

FORECAST_REVIEW_ROTATION_STATUSES = ("pass", "watch", "block")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_PLAN_LABEL_BY_STATUS = {
    "pass": "forecast_review_rotation_pass",
    "watch": "forecast_review_rotation_watch",
    "block": "forecast_review_rotation_block",
}
STATUS_PRESSURE_SCORE = {
    "pass": ZERO,
    "watch": Decimal("0.500000"),
    "block": ONE,
}

CAPACITY_OVERLOADED_BLOCK_REASON = "forecast_review_capacity_overloaded_block"
CAPACITY_TIGHT_WATCH_REASON = "forecast_review_capacity_tight_watch"
DOMAIN_EXPERTISE_LOW_BLOCK_REASON = "forecast_review_domain_expertise_low_block"
DOMAIN_EXPERTISE_THIN_WATCH_REASON = "forecast_review_domain_expertise_thin_watch"
CALIBRATION_LOW_BLOCK_REASON = "forecast_review_calibration_low_block"
CALIBRATION_THIN_WATCH_REASON = "forecast_review_calibration_thin_watch"
MEMORY_STALE_BLOCK_REASON = "forecast_review_memory_stale_block"
MEMORY_THIN_WATCH_REASON = "forecast_review_memory_thin_watch"
SLA_PRESSURE_HIGH_BLOCK_REASON = "forecast_review_sla_pressure_high_block"
SLA_PRESSURE_ELEVATED_WATCH_REASON = "forecast_review_sla_pressure_elevated_watch"
PASS_REASON = "forecast_review_rotation_pass"
BLOCK_PRESENT_REASON = "forecast_review_rotation_block_present"
WATCH_PRESENT_REASON = "forecast_review_rotation_watch_present"
CLEAR_REASON = "forecast_review_rotation_clear"
EMPTY_REASON = "forecast_review_rotation_empty"

ROW_REASON_CODE_SEQUENCE = (
    CAPACITY_OVERLOADED_BLOCK_REASON,
    CAPACITY_TIGHT_WATCH_REASON,
    DOMAIN_EXPERTISE_LOW_BLOCK_REASON,
    DOMAIN_EXPERTISE_THIN_WATCH_REASON,
    CALIBRATION_LOW_BLOCK_REASON,
    CALIBRATION_THIN_WATCH_REASON,
    MEMORY_STALE_BLOCK_REASON,
    MEMORY_THIN_WATCH_REASON,
    SLA_PRESSURE_HIGH_BLOCK_REASON,
    SLA_PRESSURE_ELEVATED_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    CAPACITY_OVERLOADED_BLOCK_REASON,
    CAPACITY_TIGHT_WATCH_REASON,
    DOMAIN_EXPERTISE_LOW_BLOCK_REASON,
    DOMAIN_EXPERTISE_THIN_WATCH_REASON,
    CALIBRATION_LOW_BLOCK_REASON,
    CALIBRATION_THIN_WATCH_REASON,
    MEMORY_STALE_BLOCK_REASON,
    MEMORY_THIN_WATCH_REASON,
    SLA_PRESSURE_HIGH_BLOCK_REASON,
    SLA_PRESSURE_ELEVATED_WATCH_REASON,
    BLOCK_PRESENT_REASON,
    WATCH_PRESENT_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
BLOCK_REASONS = (
    CAPACITY_OVERLOADED_BLOCK_REASON,
    DOMAIN_EXPERTISE_LOW_BLOCK_REASON,
    CALIBRATION_LOW_BLOCK_REASON,
    MEMORY_STALE_BLOCK_REASON,
    SLA_PRESSURE_HIGH_BLOCK_REASON,
)

_PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "event",
    "market",
    "source",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "recommendation",
    "sizing",
    "private_key",
    "account",
    "balance",
    "submit",
    "cancel",
    "replace",
    "buy",
    "sell",
    "position",
    "database",
    "network",
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_FORECAST_REVIEW_ROTATION_REPORT_CONFIG_VERSION",
    "FORECAST_REVIEW_ROTATION_STATUSES",
    "ResearchTeamForecastReviewRotationConfig",
    "ResearchTeamForecastReviewRotationInput",
    "ResearchTeamForecastReviewRotationReasonCodeCount",
    "ResearchTeamForecastReviewRotationReport",
    "ResearchTeamForecastReviewRotationRow",
    "build_research_team_forecast_review_rotation_report",
    "research_team_forecast_review_rotation_report_payload",
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
class ResearchTeamForecastReviewRotationConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_FORECAST_REVIEW_ROTATION_REPORT_CONFIG_VERSION
    )
    max_pass_capacity_utilization_ratio: Decimal = Decimal("0.800000")
    max_watch_capacity_utilization_ratio: Decimal = Decimal("1.000000")
    min_pass_domain_expertise_score: Decimal = Decimal("0.750000")
    min_watch_domain_expertise_score: Decimal = Decimal("0.550000")
    min_pass_calibration_score: Decimal = Decimal("0.700000")
    min_watch_calibration_score: Decimal = Decimal("0.500000")
    min_pass_memory_freshness_score: Decimal = Decimal("0.700000")
    min_watch_memory_freshness_score: Decimal = Decimal("0.500000")
    max_pass_sla_pressure_score: Decimal = Decimal("0.400000")
    max_watch_sla_pressure_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamForecastReviewRotationConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_FORECAST_REVIEW_ROTATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_capacity_utilization_ratio",
            "max_watch_capacity_utilization_ratio",
            "min_pass_domain_expertise_score",
            "min_watch_domain_expertise_score",
            "min_pass_calibration_score",
            "min_watch_calibration_score",
            "min_pass_memory_freshness_score",
            "min_watch_memory_freshness_score",
            "max_pass_sla_pressure_score",
            "max_watch_sla_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_domain_expertise_score",
            "min_watch_domain_expertise_score",
            "min_pass_calibration_score",
            "min_watch_calibration_score",
            "min_pass_memory_freshness_score",
            "min_watch_memory_freshness_score",
            "max_pass_sla_pressure_score",
            "max_watch_sla_pressure_score",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        if (
            self.max_pass_capacity_utilization_ratio
            > self.max_watch_capacity_utilization_ratio
        ):
            raise ValueError(
                "max_pass_capacity_utilization_ratio must not exceed watch threshold",
            )
        if self.min_watch_domain_expertise_score > self.min_pass_domain_expertise_score:
            raise ValueError(
                "min_watch_domain_expertise_score must not exceed pass threshold",
            )
        if self.min_watch_calibration_score > self.min_pass_calibration_score:
            raise ValueError(
                "min_watch_calibration_score must not exceed pass threshold",
            )
        if self.min_watch_memory_freshness_score > self.min_pass_memory_freshness_score:
            raise ValueError(
                "min_watch_memory_freshness_score must not exceed pass threshold",
            )
        if self.max_pass_sla_pressure_score > self.max_watch_sla_pressure_score:
            raise ValueError(
                "max_pass_sla_pressure_score must not exceed watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamForecastReviewRotationInput(_FinalPublicDataclass):
    public_domain_code: str
    reviewer_capacity_count: Decimal
    available_review_minutes: Decimal
    pending_review_count: Decimal
    estimated_review_minutes: Decimal
    domain_expertise_score: Decimal
    calibration_score: Decimal
    memory_freshness_score: Decimal
    sla_pressure_score: Decimal
    observed_at: datetime
    public_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamForecastReviewRotationInput, "input")
        object.__setattr__(
            self,
            "public_domain_code",
            _require_public_identifier("public_domain_code", self.public_domain_code),
        )
        for field_name in (
            "reviewer_capacity_count",
            "available_review_minutes",
            "pending_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimated_review_minutes",
            _require_positive_decimal(
                "estimated_review_minutes",
                self.estimated_review_minutes,
            ),
        )
        for field_name in (
            "domain_expertise_score",
            "calibration_score",
            "memory_freshness_score",
            "sla_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "public_reason_codes",
            _normalize_public_reason_codes(self.public_reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamForecastReviewRotationRow(_FinalPublicDataclass):
    public_domain_code: str
    reviewer_capacity_count: Decimal
    available_review_minutes: Decimal
    pending_review_count: Decimal
    estimated_review_minutes: Decimal
    review_load_minutes: Decimal
    capacity_utilization_ratio: Decimal
    capacity_gap_minutes: Decimal
    domain_expertise_score: Decimal
    calibration_score: Decimal
    memory_freshness_score: Decimal
    sla_pressure_score: Decimal
    rotation_status: str
    rotation_pressure_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamForecastReviewRotationRow, "row")
        object.__setattr__(
            self,
            "public_domain_code",
            _require_public_identifier("public_domain_code", self.public_domain_code),
        )
        for field_name in (
            "reviewer_capacity_count",
            "available_review_minutes",
            "pending_review_count",
            "estimated_review_minutes",
            "review_load_minutes",
            "capacity_utilization_ratio",
            "capacity_gap_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.estimated_review_minutes <= ZERO:
            raise ValueError("estimated_review_minutes must be greater than zero")
        for field_name in (
            "domain_expertise_score",
            "calibration_score",
            "memory_freshness_score",
            "sla_pressure_score",
            "rotation_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rotation_status",
            _require_status("rotation_status", self.rotation_status),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)

    def to_input(self) -> ResearchTeamForecastReviewRotationInput:
        return ResearchTeamForecastReviewRotationInput(
            public_domain_code=self.public_domain_code,
            reviewer_capacity_count=self.reviewer_capacity_count,
            available_review_minutes=self.available_review_minutes,
            pending_review_count=self.pending_review_count,
            estimated_review_minutes=self.estimated_review_minutes,
            domain_expertise_score=self.domain_expertise_score,
            calibration_score=self.calibration_score,
            memory_freshness_score=self.memory_freshness_score,
            sla_pressure_score=self.sla_pressure_score,
            observed_at=self.observed_at,
            public_reason_codes=tuple(
                reason
                for reason in self.reason_codes
                if reason not in ROW_REASON_CODE_SEQUENCE
            ),
        )


@dataclass(frozen=True)
class ResearchTeamForecastReviewRotationReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamForecastReviewRotationReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_public_identifier("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamForecastReviewRotationReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    rotation_plan_status: str
    public_plan_label: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_available_review_minutes: Decimal
    total_review_load_minutes: Decimal
    total_capacity_gap_minutes: Decimal
    average_capacity_utilization_ratio: Decimal
    max_capacity_utilization_ratio: Decimal
    min_domain_expertise_score: Decimal
    min_calibration_score: Decimal
    min_memory_freshness_score: Decimal
    max_sla_pressure_score: Decimal
    max_rotation_pressure_score: Decimal
    rows: tuple[ResearchTeamForecastReviewRotationRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamForecastReviewRotationReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamForecastReviewRotationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_FORECAST_REVIEW_ROTATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "rotation_plan_status",
            _require_status("rotation_plan_status", self.rotation_plan_status),
        )
        object.__setattr__(
            self,
            "public_plan_label",
            _require_public_identifier("public_plan_label", self.public_plan_label),
        )
        if self.public_plan_label != PUBLIC_PLAN_LABEL_BY_STATUS[self.rotation_plan_status]:
            raise ValueError("public_plan_label must match rotation_plan_status")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_available_review_minutes",
            "total_review_load_minutes",
            "total_capacity_gap_minutes",
            "average_capacity_utilization_ratio",
            "max_capacity_utilization_ratio",
            "min_domain_expertise_score",
            "min_calibration_score",
            "min_memory_freshness_score",
            "max_sla_pressure_score",
            "max_rotation_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_domain_expertise_score",
            "min_calibration_score",
            "min_memory_freshness_score",
            "max_sla_pressure_score",
            "max_rotation_pressure_score",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report(self)
        if not self.derived_validation_digest:
            object.__setattr__(self, "derived_validation_digest", _report_digest(self))
        _require_hard_flags("report", self)


def build_research_team_forecast_review_rotation_report(
    inputs: Iterable[object],
    *,
    config: ResearchTeamForecastReviewRotationConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamForecastReviewRotationReport:
    active_config = config or ResearchTeamForecastReviewRotationConfig()
    if type(active_config) is not ResearchTeamForecastReviewRotationConfig:
        raise ValueError(
            "config must be exactly ResearchTeamForecastReviewRotationConfig",
        )
    _require_hard_flags("config", active_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at cannot be after generated_at")
    rows = tuple(
        sorted(
            (_build_row(item, config=active_config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(rows)
    row_count = _decimal_count(len(rows))
    total_available = _sum_decimal(row.available_review_minutes for row in rows)
    total_load = _sum_decimal(row.review_load_minutes for row in rows)
    total_gap = _sum_decimal(row.capacity_gap_minutes for row in rows)
    return ResearchTeamForecastReviewRotationReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        rotation_plan_status=status,
        public_plan_label=PUBLIC_PLAN_LABEL_BY_STATUS[status],
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_available_review_minutes=total_available,
        total_review_load_minutes=total_load,
        total_capacity_gap_minutes=total_gap,
        average_capacity_utilization_ratio=(
            _ratio(
                _sum_decimal(row.capacity_utilization_ratio for row in rows),
                row_count,
            )
            if rows
            else ZERO
        ),
        max_capacity_utilization_ratio=_max_decimal(
            (row.capacity_utilization_ratio for row in rows),
            default=ZERO,
        ),
        min_domain_expertise_score=_min_decimal(
            (row.domain_expertise_score for row in rows),
            default=ZERO,
        ),
        min_calibration_score=_min_decimal(
            (row.calibration_score for row in rows),
            default=ZERO,
        ),
        min_memory_freshness_score=_min_decimal(
            (row.memory_freshness_score for row in rows),
            default=ZERO,
        ),
        max_sla_pressure_score=_max_decimal(
            (row.sla_pressure_score for row in rows),
            default=ZERO,
        ),
        max_rotation_pressure_score=_max_decimal(
            (row.rotation_pressure_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def research_team_forecast_review_rotation_report_payload(
    report: ResearchTeamForecastReviewRotationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamForecastReviewRotationReport:
        raise ValueError(
            "report must be exactly ResearchTeamForecastReviewRotationReport",
        )
    _validate_report(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")
    return _payload_value(report)


def _build_row(
    item: ResearchTeamForecastReviewRotationInput,
    *,
    config: ResearchTeamForecastReviewRotationConfig,
) -> ResearchTeamForecastReviewRotationRow:
    review_load_minutes = _multiply(
        item.pending_review_count,
        item.estimated_review_minutes,
    )
    capacity_utilization_ratio = (
        _ratio(review_load_minutes, item.available_review_minutes)
        if item.available_review_minutes > ZERO
        else ONE
    )
    capacity_gap_minutes = _positive_delta(
        review_load_minutes,
        item.available_review_minutes,
    )
    status, report_reasons = _row_status_and_reasons(
        item,
        capacity_utilization_ratio=capacity_utilization_ratio,
        config=config,
    )
    return ResearchTeamForecastReviewRotationRow(
        public_domain_code=item.public_domain_code,
        reviewer_capacity_count=item.reviewer_capacity_count,
        available_review_minutes=item.available_review_minutes,
        pending_review_count=item.pending_review_count,
        estimated_review_minutes=item.estimated_review_minutes,
        review_load_minutes=review_load_minutes,
        capacity_utilization_ratio=capacity_utilization_ratio,
        capacity_gap_minutes=capacity_gap_minutes,
        domain_expertise_score=item.domain_expertise_score,
        calibration_score=item.calibration_score,
        memory_freshness_score=item.memory_freshness_score,
        sla_pressure_score=item.sla_pressure_score,
        rotation_status=status,
        rotation_pressure_score=STATUS_PRESSURE_SCORE[status],
        observed_at=item.observed_at,
        reason_codes=_normalize_reason_codes(item.public_reason_codes + report_reasons),
    )


def _row_status_and_reasons(
    item: ResearchTeamForecastReviewRotationInput,
    *,
    capacity_utilization_ratio: Decimal,
    config: ResearchTeamForecastReviewRotationConfig,
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    if capacity_utilization_ratio > config.max_watch_capacity_utilization_ratio:
        reasons.append(CAPACITY_OVERLOADED_BLOCK_REASON)
    elif capacity_utilization_ratio > config.max_pass_capacity_utilization_ratio:
        reasons.append(CAPACITY_TIGHT_WATCH_REASON)
    if item.domain_expertise_score < config.min_watch_domain_expertise_score:
        reasons.append(DOMAIN_EXPERTISE_LOW_BLOCK_REASON)
    elif item.domain_expertise_score < config.min_pass_domain_expertise_score:
        reasons.append(DOMAIN_EXPERTISE_THIN_WATCH_REASON)
    if item.calibration_score < config.min_watch_calibration_score:
        reasons.append(CALIBRATION_LOW_BLOCK_REASON)
    elif item.calibration_score < config.min_pass_calibration_score:
        reasons.append(CALIBRATION_THIN_WATCH_REASON)
    if item.memory_freshness_score < config.min_watch_memory_freshness_score:
        reasons.append(MEMORY_STALE_BLOCK_REASON)
    elif item.memory_freshness_score < config.min_pass_memory_freshness_score:
        reasons.append(MEMORY_THIN_WATCH_REASON)
    if item.sla_pressure_score > config.max_watch_sla_pressure_score:
        reasons.append(SLA_PRESSURE_HIGH_BLOCK_REASON)
    elif item.sla_pressure_score > config.max_pass_sla_pressure_score:
        reasons.append(SLA_PRESSURE_ELEVATED_WATCH_REASON)
    if not reasons:
        return "pass", (PASS_REASON,)
    if any(reason in BLOCK_REASONS for reason in reasons):
        return "block", tuple(reasons)
    return "watch", tuple(reasons)


def _report_status(rows: tuple[ResearchTeamForecastReviewRotationRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.rotation_status == "block" for row in rows):
        return "block"
    if any(row.rotation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamForecastReviewRotationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != PASS_REASON
    }
    open_reasons = sorted(
        reason
        for reason in present
        if reason not in REPORT_REASON_CODE_SEQUENCE
    )
    ordered_reasons = [
        reason
        for reason in REPORT_REASON_CODE_SEQUENCE
        if reason in present
        and reason not in (BLOCK_PRESENT_REASON, WATCH_PRESENT_REASON, CLEAR_REASON, EMPTY_REASON)
    ]
    reasons = [*open_reasons, *ordered_reasons]
    if any(row.rotation_status == "block" for row in rows):
        reasons.append(BLOCK_PRESENT_REASON)
    if any(row.rotation_status == "watch" for row in rows):
        reasons.append(WATCH_PRESENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchTeamForecastReviewRotationRow, ...],
) -> tuple[ResearchTeamForecastReviewRotationReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchTeamForecastReviewRotationReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchTeamForecastReviewRotationReasonCodeCount(
            reason_code=reason,
            count=_report_reason_count(reason, rows),
            row_ratio=_ratio(_report_reason_count(reason, rows), row_count),
        )
        for reason in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[ResearchTeamForecastReviewRotationRow, ...],
) -> Decimal:
    if reason_code == BLOCK_PRESENT_REASON:
        return _status_count(rows, "block")
    if reason_code == WATCH_PRESENT_REASON:
        return _status_count(rows, "watch")
    if reason_code == CLEAR_REASON:
        return _status_count(rows, "pass")
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[ResearchTeamForecastReviewRotationRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.rotation_status == status))


def _validate_row(row: ResearchTeamForecastReviewRotationRow) -> None:
    if row.review_load_minutes != _multiply(
        row.pending_review_count,
        row.estimated_review_minutes,
    ):
        raise ValueError("review_load_minutes must match pending review load")
    expected_utilization = (
        _ratio(row.review_load_minutes, row.available_review_minutes)
        if row.available_review_minutes > ZERO
        else ONE
    )
    if row.capacity_utilization_ratio != expected_utilization:
        raise ValueError("capacity_utilization_ratio must match review load")
    if row.capacity_gap_minutes != _positive_delta(
        row.review_load_minutes,
        row.available_review_minutes,
    ):
        raise ValueError("capacity_gap_minutes must match review load")
    expected_status = "pass"
    if any(reason in BLOCK_REASONS for reason in row.reason_codes):
        expected_status = "block"
    elif any(
        reason in ROW_REASON_CODE_SEQUENCE and reason != PASS_REASON
        for reason in row.reason_codes
    ):
        expected_status = "watch"
    if row.rotation_status != expected_status:
        raise ValueError("reason_codes must match rotation_status")
    if row.rotation_pressure_score != STATUS_PRESSURE_SCORE[row.rotation_status]:
        raise ValueError("rotation_pressure_score must match rotation_status")
    if row.rotation_status == "pass" and PASS_REASON not in row.reason_codes:
        raise ValueError("reason_codes must match rotation_status")
    if row.rotation_status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("reason_codes must match rotation_status")


def _validate_report(report: ResearchTeamForecastReviewRotationReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.rotation_plan_status != _report_status(rows):
        raise ValueError("rotation_plan_status must match rows")
    if report.public_plan_label != PUBLIC_PLAN_LABEL_BY_STATUS[report.rotation_plan_status]:
        raise ValueError("public_plan_label must match rotation_plan_status")
    if report.total_available_review_minutes != _sum_decimal(
        row.available_review_minutes for row in rows
    ):
        raise ValueError("total_available_review_minutes must match rows")
    if report.total_review_load_minutes != _sum_decimal(row.review_load_minutes for row in rows):
        raise ValueError("total_review_load_minutes must match rows")
    if report.total_capacity_gap_minutes != _sum_decimal(
        row.capacity_gap_minutes for row in rows
    ):
        raise ValueError("total_capacity_gap_minutes must match rows")
    row_count = _decimal_count(len(rows))
    expected_average = (
        _ratio(_sum_decimal(row.capacity_utilization_ratio for row in rows), row_count)
        if rows
        else ZERO
    )
    if report.average_capacity_utilization_ratio != expected_average:
        raise ValueError("average_capacity_utilization_ratio must match rows")
    if report.max_capacity_utilization_ratio != _max_decimal(
        (row.capacity_utilization_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_capacity_utilization_ratio must match rows")
    if report.min_domain_expertise_score != _min_decimal(
        (row.domain_expertise_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_domain_expertise_score must match rows")
    if report.min_calibration_score != _min_decimal(
        (row.calibration_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_calibration_score must match rows")
    if report.min_memory_freshness_score != _min_decimal(
        (row.memory_freshness_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_memory_freshness_score must match rows")
    if report.max_sla_pressure_score != _max_decimal(
        (row.sla_pressure_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_sla_pressure_score must match rows")
    if report.max_rotation_pressure_score != _max_decimal(
        (row.rotation_pressure_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_rotation_pressure_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchTeamForecastReviewRotationInput, ...]:
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchTeamForecastReviewRotationInput:
            raise ValueError(
                "inputs must contain ResearchTeamForecastReviewRotationInput values",
            )
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchTeamForecastReviewRotationRow, ...],
) -> tuple[ResearchTeamForecastReviewRotationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamForecastReviewRotationRow:
            raise ValueError("rows must contain ResearchTeamForecastReviewRotationRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamForecastReviewRotationReasonCodeCount, ...],
) -> tuple[ResearchTeamForecastReviewRotationReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        if type(item) is not ResearchTeamForecastReviewRotationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamForecastReviewRotationReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    return counts


def _normalize_public_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("public_reason_codes must be a tuple")
    if not value:
        raise ValueError("public_reason_codes must not be empty")
    for reason in value:
        _require_public_identifier("public_reason_code", reason)
    return tuple(sorted(dict.fromkeys(value)))


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    for reason in value:
        _require_public_identifier("reason_code", reason)
    unique = tuple(dict.fromkeys(value))
    open_reasons = sorted(
        reason
        for reason in unique
        if reason not in ROW_REASON_CODE_SEQUENCE
        and reason not in REPORT_REASON_CODE_SEQUENCE
    )
    reason_priority = tuple(
        dict.fromkeys((*ROW_REASON_CODE_SEQUENCE, *REPORT_REASON_CODE_SEQUENCE)),
    )
    ordered = [
        reason
        for reason in reason_priority
        if reason in unique
    ]
    return tuple([*open_reasons, *ordered])


def _row_sort_key(row: ResearchTeamForecastReviewRotationRow) -> tuple[Decimal, str]:
    return (-row.rotation_pressure_score, row.public_domain_code)


def _report_digest(report: ResearchTeamForecastReviewRotationReport) -> str:
    payload = _payload_value(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _payload_value(value: Any, *, include_digest: bool = True) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        data = asdict(value)
        if not include_digest:
            data.pop("derived_validation_digest", None)
        return _payload_value(data, include_digest=include_digest)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, dict):
        return {
            key: _payload_value(child, include_digest=include_digest)
            for key, child in sorted(value.items())
        }
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value: {value!r}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public identifier in {field_name}")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if value not in FORECAST_REVIEW_ROTATION_STATUSES:
        raise ValueError(f"{field_name} must be one of {FORECAST_REVIEW_ROTATION_STATUSES}")
    return value


def _require_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _positive_delta(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(max(left - right, ZERO))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    collected = tuple(values)
    if not collected:
        return default
    return _quantize(max(collected))


def _min_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    collected = tuple(values)
    if not collected:
        return default
    return _quantize(min(collected))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))
