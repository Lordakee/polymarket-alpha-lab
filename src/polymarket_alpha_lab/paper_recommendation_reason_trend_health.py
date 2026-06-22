"""Health reducer for paper recommendation reason trend reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.paper_recommendation_reason_trend import (
    PaperRecommendationReasonTrendReport,
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
HEALTH_STATUSES = ("pass", "watch", "blocked")


@dataclass(frozen=True)
class PaperRecommendationReasonTrendHealthConfig:
    config_version: str
    max_blocked_status_share: Decimal = Decimal("0.500000")
    max_reject_status_share: Decimal = Decimal("0.500000")
    max_new_reason_code_count: int = 0
    max_transition_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_blocked_status_share",
            _normalize_probability_decimal(
                "max_blocked_status_share",
                self.max_blocked_status_share,
            ),
        )
        object.__setattr__(
            self,
            "max_reject_status_share",
            _normalize_probability_decimal(
                "max_reject_status_share",
                self.max_reject_status_share,
            ),
        )
        _require_nonnegative_int(
            "max_new_reason_code_count",
            self.max_new_reason_code_count,
        )
        _require_nonnegative_int("max_transition_count", self.max_transition_count)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperRecommendationReasonTrendHealthReport:
    generated_at: datetime
    config_version: str
    health_status: str
    source_report_count: int
    reason_code_count: int
    blocked_status_count: int
    blocked_status_share: Decimal | None
    reject_status_count: int
    reject_status_share: Decimal | None
    new_reason_code_count: int
    transition_count: int
    persistent_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    max_blocked_status_share: Decimal
    max_reject_status_share: Decimal
    max_new_reason_code_count: int
    max_transition_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_health_status("health_status", self.health_status)
        for field_name in (
            "source_report_count",
            "reason_code_count",
            "blocked_status_count",
            "reject_status_count",
            "new_reason_code_count",
            "transition_count",
            "max_new_reason_code_count",
            "max_transition_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "blocked_status_share",
            _normalize_optional_probability_decimal(
                "blocked_status_share",
                self.blocked_status_share,
            ),
        )
        object.__setattr__(
            self,
            "reject_status_share",
            _normalize_optional_probability_decimal(
                "reject_status_share",
                self.reject_status_share,
            ),
        )
        object.__setattr__(
            self,
            "max_blocked_status_share",
            _normalize_probability_decimal(
                "max_blocked_status_share",
                self.max_blocked_status_share,
            ),
        )
        object.__setattr__(
            self,
            "max_reject_status_share",
            _normalize_probability_decimal(
                "max_reject_status_share",
                self.max_reject_status_share,
            ),
        )
        object.__setattr__(
            self,
            "persistent_reason_codes",
            _normalize_reason_codes("persistent_reason_codes", self.persistent_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_paper_recommendation_reason_trend_health_report(
    reason_trend_report: object,
    *,
    config: PaperRecommendationReasonTrendHealthConfig,
    generated_at: datetime,
) -> PaperRecommendationReasonTrendHealthReport:
    if type(reason_trend_report) is not PaperRecommendationReasonTrendReport:
        raise ValueError("reason_trend_report must be a PaperRecommendationReasonTrendReport")
    if type(config) is not PaperRecommendationReasonTrendHealthConfig:
        raise ValueError("config must be a PaperRecommendationReasonTrendHealthConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("reason_trend_report", reason_trend_report)
    _require_hard_flags("config", config)

    reason_rows = reason_trend_report.reason_trend_rows
    total_reason_count = sum(row.count for row in reason_rows)
    blocked_status_count = _status_count(reason_rows, "blocked")
    reject_status_count = _status_count(reason_rows, "reject")
    new_reason_code_count = sum(
        1
        for row in reason_rows
        if row.first_seen_at == reason_trend_report.generated_at
    )
    transition_count = sum(
        row.transition_count for row in reason_trend_report.transition_trend_rows
    )
    reason_codes = tuple(sorted({row.reason_code for row in reason_rows}))
    persistent_reason_codes = tuple(
        sorted(
            {
                row.reason_code
                for row in reason_rows
                if row.first_seen_at < reason_trend_report.generated_at
                and row.latest_seen_at == reason_trend_report.generated_at
            },
        ),
    )

    return PaperRecommendationReasonTrendHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        health_status=_health_status(
            source_report_count=reason_trend_report.source_report_count,
            blocked_status_share=_ratio(blocked_status_count, total_reason_count),
            reject_status_share=_ratio(reject_status_count, total_reason_count),
            new_reason_code_count=new_reason_code_count,
            transition_count=transition_count,
            config=config,
        ),
        source_report_count=reason_trend_report.source_report_count,
        reason_code_count=len(reason_codes),
        blocked_status_count=blocked_status_count,
        blocked_status_share=_ratio(blocked_status_count, total_reason_count),
        reject_status_count=reject_status_count,
        reject_status_share=_ratio(reject_status_count, total_reason_count),
        new_reason_code_count=new_reason_code_count,
        transition_count=transition_count,
        persistent_reason_codes=persistent_reason_codes,
        reason_codes=reason_codes,
        max_blocked_status_share=config.max_blocked_status_share,
        max_reject_status_share=config.max_reject_status_share,
        max_new_reason_code_count=config.max_new_reason_code_count,
        max_transition_count=config.max_transition_count,
    )


def _health_status(
    *,
    source_report_count: int,
    blocked_status_share: Decimal | None,
    reject_status_share: Decimal | None,
    new_reason_code_count: int,
    transition_count: int,
    config: PaperRecommendationReasonTrendHealthConfig,
) -> str:
    if source_report_count == 0:
        return "blocked"
    if (
        blocked_status_share is not None
        and blocked_status_share > config.max_blocked_status_share
    ):
        return "blocked"
    if (
        reject_status_share is not None
        and reject_status_share > config.max_reject_status_share
    ):
        return "blocked"
    if new_reason_code_count > config.max_new_reason_code_count:
        return "watch"
    if transition_count > config.max_transition_count:
        return "watch"
    return "pass"


def _status_count(rows: object, source_status: str) -> int:
    return sum(row.count for row in rows if row.source_status == source_status)


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _validate_report_consistency(
    report: PaperRecommendationReasonTrendHealthReport,
) -> None:
    if report.source_report_count == 0:
        if report.health_status != "blocked":
            raise ValueError("health_status must be blocked without source history")
        if report.reason_codes:
            raise ValueError("reason_codes must be empty without source history")
        if report.persistent_reason_codes:
            raise ValueError(
                "persistent_reason_codes must be empty without source history",
            )
    if report.reason_code_count != len(report.reason_codes):
        raise ValueError("reason_code_count must match reason_codes")
    if report.persistent_reason_codes != tuple(sorted(report.persistent_reason_codes)):
        raise ValueError("persistent_reason_codes must use deterministic sorting")
    if report.reason_codes != tuple(sorted(report.reason_codes)):
        raise ValueError("reason_codes must use deterministic sorting")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability_decimal(field_name, value)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(reason_codes)


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
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


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperRecommendationReasonTrendHealthConfig",
    "PaperRecommendationReasonTrendHealthReport",
    "build_paper_recommendation_reason_trend_health_report",
)
