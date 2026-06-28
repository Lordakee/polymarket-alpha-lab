from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable


DEFAULT_AUTONOMOUS_MARKET_SCORER_HISTORY_CONFIG_VERSION = (
    "autonomous-market-scorer-history-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
GATE_STATUSES = ("pass", "watch", "blocked")
HISTORY_STATUSES = (
    "insufficient_history",
    "blocked",
    "stale",
    "no_candidates",
    "stable",
)


@dataclass(frozen=True)
class AutonomousMarketScorerHistoryConfig:
    config_version: str = DEFAULT_AUTONOMOUS_MARKET_SCORER_HISTORY_CONFIG_VERSION
    min_report_count: int = 3
    max_latest_age_seconds: int = 86_400
    max_blocked_report_count: int = 0
    max_skipped_report_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "AutonomousMarketScorerHistoryConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScorerHistoryConfig:
            raise ValueError(
                "config must be exactly AutonomousMarketScorerHistoryConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_report_count", self.min_report_count)
        _require_nonnegative_int("max_latest_age_seconds", self.max_latest_age_seconds)
        _require_nonnegative_int(
            "max_blocked_report_count",
            self.max_blocked_report_count,
        )
        _require_nonnegative_int(
            "max_skipped_report_count",
            self.max_skipped_report_count,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class AutonomousMarketScorerHistoryMarketSlugCount:
    market_slug: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "AutonomousMarketScorerHistoryMarketSlugCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScorerHistoryMarketSlugCount:
            raise ValueError(
                "market_slug_count must be exactly "
                "AutonomousMarketScorerHistoryMarketSlugCount",
            )
        _require_canonical_string("market_slug", self.market_slug)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("market_slug_count", self)


@dataclass(frozen=True)
class AutonomousMarketScorerHistoryConditionIdCount:
    condition_id: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "AutonomousMarketScorerHistoryConditionIdCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScorerHistoryConditionIdCount:
            raise ValueError(
                "condition_id_count must be exactly "
                "AutonomousMarketScorerHistoryConditionIdCount",
            )
        _require_canonical_string("condition_id", self.condition_id)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("condition_id_count", self)


@dataclass(frozen=True)
class AutonomousMarketScorerHistoryReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "AutonomousMarketScorerHistoryReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScorerHistoryReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "AutonomousMarketScorerHistoryReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class AutonomousMarketScorerHistoryReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    first_generated_at: datetime
    latest_generated_at: datetime
    history_span_seconds: int
    latest_gate_status: str
    latest_gate_status_streak: int
    recurring_market_slug_counts: tuple[
        AutonomousMarketScorerHistoryMarketSlugCount,
        ...,
    ]
    recurring_condition_id_counts: tuple[
        AutonomousMarketScorerHistoryConditionIdCount,
        ...,
    ]
    recurring_reason_code_counts: tuple[
        AutonomousMarketScorerHistoryReasonCodeCount,
        ...,
    ]
    latest_candidate_count: int
    average_candidate_count: Decimal
    latest_recommended_notional: Decimal
    total_recommended_notional: Decimal
    notional_delta: Decimal
    blocked_report_count: int
    skipped_report_count: int
    history_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "AutonomousMarketScorerHistoryReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not AutonomousMarketScorerHistoryReport:
            raise ValueError(
                "history_report must be exactly AutonomousMarketScorerHistoryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_utc(self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_utc(self.latest_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_report_count",
            "history_span_seconds",
            "latest_gate_status_streak",
            "latest_candidate_count",
            "blocked_report_count",
            "skipped_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_gate_status("latest_gate_status", self.latest_gate_status)
        object.__setattr__(
            self,
            "recurring_market_slug_counts",
            _normalize_market_slug_counts(self.recurring_market_slug_counts),
        )
        object.__setattr__(
            self,
            "recurring_condition_id_counts",
            _normalize_condition_id_counts(self.recurring_condition_id_counts),
        )
        object.__setattr__(
            self,
            "recurring_reason_code_counts",
            _normalize_reason_code_counts(self.recurring_reason_code_counts),
        )
        object.__setattr__(
            self,
            "average_candidate_count",
            _quantize_nonnegative_decimal(
                "average_candidate_count",
                self.average_candidate_count,
            ),
        )
        object.__setattr__(
            self,
            "latest_recommended_notional",
            _quantize_nonnegative_decimal(
                "latest_recommended_notional",
                self.latest_recommended_notional,
            ),
        )
        object.__setattr__(
            self,
            "total_recommended_notional",
            _quantize_nonnegative_decimal(
                "total_recommended_notional",
                self.total_recommended_notional,
            ),
        )
        object.__setattr__(
            self,
            "notional_delta",
            _quantize_decimal("notional_delta", self.notional_delta),
        )
        _require_history_status(self.history_status)
        _require_next_step(self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("history_report", self)


def build_autonomous_market_scorer_history_report(
    reports: Iterable[object],
    *,
    generated_at: datetime,
    config: AutonomousMarketScorerHistoryConfig | None = None,
) -> AutonomousMarketScorerHistoryReport:
    if config is None:
        config = AutonomousMarketScorerHistoryConfig()
    if type(config) is not AutonomousMarketScorerHistoryConfig:
        raise ValueError(
            "config must be exactly AutonomousMarketScorerHistoryConfig",
        )
    generated_at_utc = _as_utc(generated_at)
    source_reports = _normalize_reports(reports)
    first_report = source_reports[0]
    latest_report = source_reports[-1]
    first_generated_at = _source_generated_at(first_report)
    latest_generated_at = _source_generated_at(latest_report)
    if generated_at_utc < latest_generated_at:
        raise ValueError("generated_at must not be before latest_generated_at")

    candidate_counts = tuple(_candidate_count(report) for report in source_reports)
    latest_candidate_count = candidate_counts[-1]
    notional_values = tuple(_total_notional(report) for report in source_reports)
    latest_recommended_notional = notional_values[-1]
    total_recommended_notional = sum(notional_values, ZERO)
    blocked_report_count = sum(
        1 for report in source_reports if _is_blocked_report(report)
    )
    skipped_report_count = sum(
        1 for report in source_reports if _is_skipped_report(report)
    )
    latest_gate_status = _source_gate_status(latest_report)
    history_status = _history_status(
        source_report_count=len(source_reports),
        min_report_count=config.min_report_count,
        latest_age_seconds=_seconds_between(latest_generated_at, generated_at_utc),
        max_latest_age_seconds=config.max_latest_age_seconds,
        latest_candidate_count=latest_candidate_count,
        blocked_report_count=blocked_report_count,
        max_blocked_report_count=config.max_blocked_report_count,
        skipped_report_count=skipped_report_count,
        max_skipped_report_count=config.max_skipped_report_count,
    )
    source_reason_codes = _source_reason_codes(source_reports)

    return AutonomousMarketScorerHistoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_report_count=len(source_reports),
        first_generated_at=first_generated_at,
        latest_generated_at=latest_generated_at,
        history_span_seconds=_seconds_between(first_generated_at, latest_generated_at),
        latest_gate_status=latest_gate_status,
        latest_gate_status_streak=_latest_gate_status_streak(source_reports),
        recurring_market_slug_counts=_recurring_market_slug_counts(source_reports),
        recurring_condition_id_counts=_recurring_condition_id_counts(source_reports),
        recurring_reason_code_counts=_recurring_reason_code_counts(source_reports),
        latest_candidate_count=latest_candidate_count,
        average_candidate_count=_average_candidate_count(candidate_counts),
        latest_recommended_notional=latest_recommended_notional,
        total_recommended_notional=total_recommended_notional,
        notional_delta=notional_values[-1] - notional_values[0],
        blocked_report_count=blocked_report_count,
        skipped_report_count=skipped_report_count,
        history_status=history_status,
        recommended_next_step=_next_step(history_status),
        reason_codes=tuple(
            sorted(
                (*source_reason_codes, _history_status_reason_code(history_status)),
            ),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _normalize_reports(reports: Iterable[object]) -> tuple[object, ...]:
    if isinstance(reports, (str, bytes)):
        raise ValueError("reports must be an iterable")
    try:
        source_reports = tuple(reports)
    except TypeError as exc:
        raise ValueError("reports must be an iterable") from exc
    if not source_reports:
        raise ValueError("reports must be non-empty")

    previous_generated_at: datetime | None = None
    for report in source_reports:
        _require_hard_flags("source report", report)
        config = getattr(report, "config", None)
        if config is not None:
            _require_hard_flags("source config", config)
        generated_at = _source_generated_at(report)
        if previous_generated_at is not None and generated_at < previous_generated_at:
            raise ValueError("reports must be chronological by generated_at")
        _source_gate_status(report)
        _candidate_count(report)
        _total_notional(report)
        _require_nonnegative_int("markets_skipped", _source_int(report, "markets_skipped", 0))
        _require_nonnegative_int("markets_blocked", _source_int(report, "markets_blocked", 0))
        _normalize_reason_codes(_source_tuple(report, "reason_codes", ()))
        for row in _source_tuple(report, "score_rows", ()):
            _source_row_market_slug(row)
            _source_row_condition_id(row)
            if hasattr(row, "recommended_notional"):
                _quantize_nonnegative_decimal(
                    "score_rows recommended_notional",
                    getattr(row, "recommended_notional"),
                )
        previous_generated_at = generated_at
    return source_reports


def _history_status(
    *,
    source_report_count: int,
    min_report_count: int,
    latest_age_seconds: int,
    max_latest_age_seconds: int,
    latest_candidate_count: int,
    blocked_report_count: int,
    max_blocked_report_count: int,
    skipped_report_count: int,
    max_skipped_report_count: int,
) -> str:
    if source_report_count < min_report_count:
        return "insufficient_history"
    if latest_age_seconds > max_latest_age_seconds:
        return "stale"
    if latest_candidate_count == 0:
        return "no_candidates"
    if (
        blocked_report_count > max_blocked_report_count
        or skipped_report_count > max_skipped_report_count
    ):
        return "blocked"
    return "stable"


def _next_step(history_status: str) -> str:
    if history_status == "insufficient_history":
        return "collect_more_scorer_history"
    if history_status in ("blocked", "stale", "no_candidates"):
        return "review_scorer_inputs"
    return "continue_monitoring"


def _history_status_reason_code(history_status: str) -> str:
    return f"autonomous_market_scorer_history_{history_status}"


def _latest_gate_status_streak(reports: tuple[object, ...]) -> int:
    latest_status = _source_gate_status(reports[-1])
    streak = 0
    for report in reversed(reports):
        if _source_gate_status(report) != latest_status:
            break
        streak += 1
    return streak


def _recurring_market_slug_counts(
    reports: tuple[object, ...],
) -> tuple[AutonomousMarketScorerHistoryMarketSlugCount, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for value in _source_market_slugs(report):
            counts[value] = counts.get(value, 0) + 1
    return tuple(
        AutonomousMarketScorerHistoryMarketSlugCount(value, count)
        for value, count in _recurring_items(counts)
    )


def _recurring_condition_id_counts(
    reports: tuple[object, ...],
) -> tuple[AutonomousMarketScorerHistoryConditionIdCount, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for value in _source_condition_ids(report):
            counts[value] = counts.get(value, 0) + 1
    return tuple(
        AutonomousMarketScorerHistoryConditionIdCount(value, count)
        for value, count in _recurring_items(counts)
    )


def _recurring_reason_code_counts(
    reports: tuple[object, ...],
) -> tuple[AutonomousMarketScorerHistoryReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for report in reports:
        for value in _source_report_reason_codes(report):
            counts[value] = counts.get(value, 0) + 1
    return tuple(
        AutonomousMarketScorerHistoryReasonCodeCount(value, count)
        for value, count in _recurring_items(counts)
    )


def _recurring_items(counts: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(
        sorted(
            (
                (value, count)
                for value, count in counts.items()
                if count > 1
            ),
            key=lambda item: (-item[1], item[0]),
        ),
    )


def _source_reason_codes(reports: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            reason_code
            for report in reports
            for reason_code in _source_report_reason_codes(report)
        ),
    )


def _source_report_reason_codes(report: object) -> tuple[str, ...]:
    return tuple(
        sorted(
            dict.fromkeys(
                (
                    *_source_tuple(report, "reason_codes", ()),
                    *(
                        reason_code
                        for row in _candidate_rows(report)
                        for reason_code in _source_tuple(row, "reason_codes", ())
                    ),
                ),
            ),
        ),
    )


def _source_market_slugs(report: object) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            _source_row_market_slug(row)
            for row in _candidate_rows(report)
        ),
    )


def _source_condition_ids(report: object) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            _source_row_condition_id(row)
            for row in _candidate_rows(report)
        ),
    )


def _candidate_rows(report: object) -> tuple[object, ...]:
    rows = _source_tuple(report, "score_rows", ())
    return tuple(row for row in rows if _source_row_status(row) == "scored")


def _average_candidate_count(candidate_counts: tuple[int, ...]) -> Decimal:
    return (Decimal(sum(candidate_counts)) / Decimal(len(candidate_counts))).quantize(
        QUANTUM,
    )


def _candidate_count(report: object) -> int:
    value = getattr(report, "markets_scored", None)
    if value is not None:
        _require_nonnegative_int("markets_scored", value)
        return value
    return len(_candidate_rows(report))


def _total_notional(report: object) -> Decimal:
    value = getattr(report, "total_recommended_notional", None)
    if value is None:
        return sum(
            (
                _quantize_nonnegative_decimal(
                    "score_rows recommended_notional",
                    getattr(row, "recommended_notional"),
                )
                for row in _candidate_rows(report)
            ),
            ZERO,
        )
    return _quantize_nonnegative_decimal("total_recommended_notional", value)


def _is_blocked_report(report: object) -> bool:
    return (
        _source_gate_status(report) == "blocked"
        or _source_int(report, "markets_blocked", 0) > 0
    )


def _is_skipped_report(report: object) -> bool:
    return (
        _source_gate_status(report) == "watch"
        or _source_int(report, "markets_skipped", 0) > 0
    )


def _source_generated_at(report: object) -> datetime:
    return _as_utc(getattr(report, "generated_at"))


def _source_gate_status(report: object) -> str:
    value = getattr(report, "gate_status")
    _require_gate_status("gate_status", value)
    return value


def _source_int(report: object, field_name: str, default: int) -> int:
    value = getattr(report, field_name, default)
    _require_nonnegative_int(field_name, value)
    return value


def _source_tuple(report: object, field_name: str, default: tuple[object, ...]) -> tuple:
    value = getattr(report, field_name, default)
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _source_row_market_slug(row: object) -> str:
    value = getattr(row, "market_slug")
    _require_canonical_string("market_slug", value)
    return value


def _source_row_condition_id(row: object) -> str:
    value = getattr(row, "condition_id")
    _require_canonical_string("condition_id", value)
    return value


def _source_row_status(row: object) -> str:
    value = getattr(row, "score_status", "scored")
    if value not in ("scored", "skipped", "blocked"):
        raise ValueError("score_status must be scored, skipped, or blocked")
    return value


def _normalize_market_slug_counts(
    values: tuple[AutonomousMarketScorerHistoryMarketSlugCount, ...],
) -> tuple[AutonomousMarketScorerHistoryMarketSlugCount, ...]:
    if type(values) is not tuple:
        raise ValueError("recurring_market_slug_counts must be a tuple")
    for value in values:
        if type(value) is not AutonomousMarketScorerHistoryMarketSlugCount:
            raise ValueError(
                "recurring_market_slug_counts entries must be "
                "AutonomousMarketScorerHistoryMarketSlugCount",
            )
    return values


def _normalize_condition_id_counts(
    values: tuple[AutonomousMarketScorerHistoryConditionIdCount, ...],
) -> tuple[AutonomousMarketScorerHistoryConditionIdCount, ...]:
    if type(values) is not tuple:
        raise ValueError("recurring_condition_id_counts must be a tuple")
    for value in values:
        if type(value) is not AutonomousMarketScorerHistoryConditionIdCount:
            raise ValueError(
                "recurring_condition_id_counts entries must be "
                "AutonomousMarketScorerHistoryConditionIdCount",
            )
    return values


def _normalize_reason_code_counts(
    values: tuple[AutonomousMarketScorerHistoryReasonCodeCount, ...],
) -> tuple[AutonomousMarketScorerHistoryReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("recurring_reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not AutonomousMarketScorerHistoryReasonCodeCount:
            raise ValueError(
                "recurring_reason_code_counts entries must be "
                "AutonomousMarketScorerHistoryReasonCodeCount",
            )
    return values


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    previous: str | None = None
    for value in values:
        _require_canonical_string("reason_code", value)
        if previous is not None and previous >= value:
            raise ValueError("reason_codes must be sorted and unique")
        previous = value
    return values


def _seconds_between(first: datetime, latest: datetime) -> int:
    delta = latest - first
    return delta.days * 86_400 + delta.seconds


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")


def _require_gate_status(field_name: str, value: object) -> None:
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_history_status(value: object) -> None:
    if value not in HISTORY_STATUSES:
        raise ValueError("history_status must be a known status")


def _require_next_step(value: object) -> None:
    if value not in (
        "collect_more_scorer_history",
        "review_scorer_inputs",
        "continue_monitoring",
    ):
        raise ValueError("recommended_next_step must be a known next step")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


__all__ = (
    "DEFAULT_AUTONOMOUS_MARKET_SCORER_HISTORY_CONFIG_VERSION",
    "AutonomousMarketScorerHistoryConfig",
    "AutonomousMarketScorerHistoryConditionIdCount",
    "AutonomousMarketScorerHistoryMarketSlugCount",
    "AutonomousMarketScorerHistoryReasonCodeCount",
    "AutonomousMarketScorerHistoryReport",
    "build_autonomous_market_scorer_history_report",
)
