"""Pure report-only reducer for football signal memory quality."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_DOMAIN_FOOTBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-football-signal-memory-quality-report-v0"
)
FOOTBALL_SIGNAL_MEMORY_QUALITY_STATUSES = ("pass", "watch", "block")
FOOTBALL_SIGNAL_MEMORY_QUALITY_REASON_CODES = (
    "no_football_signal_memory_inputs",
    "team_memory_missing",
    "team_memory_stale_block",
    "team_memory_stale_watch",
    "injury_memory_missing",
    "injury_memory_stale_block",
    "injury_memory_stale_watch",
    "weather_memory_missing",
    "weather_memory_stale_block",
    "weather_memory_stale_watch",
    "schedule_memory_missing",
    "schedule_memory_stale_block",
    "schedule_memory_stale_watch",
    "memory_conflicts_block",
    "memory_conflicts_watch",
    "forecast_handoff_urgency_block",
    "forecast_handoff_urgency_watch",
    "football_signal_memory_quality_block",
    "football_signal_memory_quality_watch",
    "football_signal_memory_quality_pass",
)

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_ZERO_COUNT = Decimal("0")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4")
_DECIMAL_CONTEXT = Context(prec=64)
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_ROW_REASON_PRIORITY = FOOTBALL_SIGNAL_MEMORY_QUALITY_REASON_CODES[1:]
_UNSAFE_PUBLIC_LABEL_FRAGMENTS = frozenset(
    (
        "candidate" "_" "id",
        "market" "_" "id",
        "market" "_" "slug",
        "sl" "ug",
        "ques" "tion",
        "u" "rl",
        "source" "_" "text",
        "dsn",
        "table" "_" "name",
        "to" "ken",
        "wal" "let",
        "acc" "ount",
        "or" "der",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "cl" "ob",
        "au" "th",
        "net" "work",
        "reco" "mmend",
        "siz" "ing",
        "ad" "vice",
        "tr" "ade",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_FOOTBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "FOOTBALL_SIGNAL_MEMORY_QUALITY_STATUSES",
    "FOOTBALL_SIGNAL_MEMORY_QUALITY_REASON_CODES",
    "ResearchDomainFootballSignalMemoryQualityConfig",
    "ResearchDomainFootballSignalMemoryQualityInput",
    "ResearchDomainFootballSignalMemoryQualityReport",
    "ResearchDomainFootballSignalMemoryQualityRow",
    "build_research_domain_football_signal_memory_quality_report",
    "research_domain_football_signal_memory_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainFootballSignalMemoryQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_FOOTBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    watch_stale_memory_seconds: Decimal = Decimal("86400.000000")
    block_stale_memory_seconds: Decimal = Decimal("604800.000000")
    freshness_zero_age_seconds: Decimal = Decimal("133333.333333")
    watch_conflicting_memory_count: Decimal = Decimal("1")
    block_conflicting_memory_count: Decimal = Decimal("2")
    watch_forecast_handoff_urgency_score: Decimal = Decimal("0.500000")
    block_forecast_handoff_urgency_score: Decimal = Decimal("0.850000")
    quality_pass_threshold: Decimal = Decimal("0.800000")
    quality_watch_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainFootballSignalMemoryQualityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchDomainFootballSignalMemoryQualityConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_FOOTBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_stale_memory_seconds",
            "block_stale_memory_seconds",
            "freshness_zero_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflicting_memory_count",
            "block_conflicting_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_forecast_handoff_urgency_score",
            "block_forecast_handoff_urgency_score",
            "quality_pass_threshold",
            "quality_watch_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_stale_memory_seconds <= self.watch_stale_memory_seconds:
            raise ValueError("block_stale_memory_seconds must exceed watch threshold")
        if self.block_conflicting_memory_count < self.watch_conflicting_memory_count:
            raise ValueError("block_conflicting_memory_count must be at least watch count")
        if (
            self.block_forecast_handoff_urgency_score
            < self.watch_forecast_handoff_urgency_score
        ):
            raise ValueError("block urgency threshold must be at least watch threshold")
        if self.quality_pass_threshold < self.quality_watch_threshold:
            raise ValueError("quality_pass_threshold must be at least watch threshold")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchDomainFootballSignalMemoryQualityInput:
    team_label: str
    memory_context: str
    team_memory_count: Decimal
    injury_memory_count: Decimal
    weather_memory_count: Decimal
    schedule_memory_count: Decimal
    team_memory_age_seconds: Decimal
    injury_memory_age_seconds: Decimal
    weather_memory_age_seconds: Decimal
    schedule_memory_age_seconds: Decimal
    conflicting_memory_count: Decimal
    forecast_handoff_urgency_score: Decimal
    observed_at: datetime
    redaction_confirmed: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainFootballSignalMemoryQualityInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("memory_input", self, ResearchDomainFootballSignalMemoryQualityInput)
        for field_name in ("team_label", "memory_context"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in _MEMORY_COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in _MEMORY_AGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflicting_memory_count",
            _normalize_count("conflicting_memory_count", self.conflicting_memory_count),
        )
        object.__setattr__(
            self,
            "forecast_handoff_urgency_score",
            _normalize_ratio(
                "forecast_handoff_urgency_score",
                self.forecast_handoff_urgency_score,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.redaction_confirmed is not True:
            raise ValueError("redaction_confirmed must be True")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("memory_input", self)


@dataclass(frozen=True)
class ResearchDomainFootballSignalMemoryQualityRow:
    team_label: str
    memory_context: str
    missing_memory_lane_count: Decimal
    stale_memory_lane_count: Decimal
    conflicting_memory_count: Decimal
    team_memory_age_seconds: Decimal
    injury_memory_age_seconds: Decimal
    weather_memory_age_seconds: Decimal
    schedule_memory_age_seconds: Decimal
    memory_coverage_ratio: Decimal
    memory_freshness_ratio: Decimal
    non_conflict_score: Decimal
    forecast_handoff_urgency_score: Decimal
    signal_memory_quality_score: Decimal
    row_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainFootballSignalMemoryQualityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchDomainFootballSignalMemoryQualityRow)
        for field_name in ("team_label", "memory_context"):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "missing_memory_lane_count",
            "stale_memory_lane_count",
            "conflicting_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in _MEMORY_AGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_coverage_ratio",
            "memory_freshness_ratio",
            "non_conflict_score",
            "forecast_handoff_urgency_score",
            "signal_memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchDomainFootballSignalMemoryQualityReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_memory_lane_total: Decimal
    stale_memory_lane_total: Decimal
    conflicting_memory_total: Decimal
    forecast_handoff_ready_count: Decimal
    average_signal_memory_quality_score: Decimal
    rows: tuple[ResearchDomainFootballSignalMemoryQualityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainFootballSignalMemoryQualityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchDomainFootballSignalMemoryQualityReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_FOOTBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_memory_lane_total",
            "stale_memory_lane_total",
            "conflicting_memory_total",
            "forecast_handoff_ready_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_signal_memory_quality_score",
            _normalize_ratio(
                "average_signal_memory_quality_score",
                self.average_signal_memory_quality_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_surface("payload", payload)
        _reject_public_numeric_values(payload)
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


_MEMORY_COUNT_FIELDS = (
    "team_memory_count",
    "injury_memory_count",
    "weather_memory_count",
    "schedule_memory_count",
)
_MEMORY_AGE_FIELDS = (
    "team_memory_age_seconds",
    "injury_memory_age_seconds",
    "weather_memory_age_seconds",
    "schedule_memory_age_seconds",
)
_LANES = ("team", "injury", "weather", "schedule")


def build_research_domain_football_signal_memory_quality_report(
    inputs: Iterable[ResearchDomainFootballSignalMemoryQualityInput],
    *,
    generated_at: datetime,
    config: ResearchDomainFootballSignalMemoryQualityConfig | None = None,
) -> ResearchDomainFootballSignalMemoryQualityReport:
    if config is None:
        config = ResearchDomainFootballSignalMemoryQualityConfig()
    _require_exact_type("config", config, ResearchDomainFootballSignalMemoryQualityConfig)
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if _seconds_between(value.observed_at, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after observed_at")
    rows = tuple(
        sorted(
            (_row_from_input(value, config) for value in normalized),
            key=_row_sort_key,
        ),
    )
    return ResearchDomainFootballSignalMemoryQualityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(normalized)),
        row_count=_decimal_count(len(rows)),
        team_count=_decimal_count(len({row.team_label for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        missing_memory_lane_total=_sum_decimal(
            tuple(row.missing_memory_lane_count for row in rows),
        ),
        stale_memory_lane_total=_sum_decimal(
            tuple(row.stale_memory_lane_count for row in rows),
        ),
        conflicting_memory_total=_sum_decimal(
            tuple(row.conflicting_memory_count for row in rows),
        ),
        forecast_handoff_ready_count=_status_count(rows, "pass"),
        average_signal_memory_quality_score=_average_score(
            tuple(row.signal_memory_quality_score for row in rows),
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_domain_football_signal_memory_quality_report_payload(
    report: ResearchDomainFootballSignalMemoryQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchDomainFootballSignalMemoryQualityReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        _reject_public_numeric_values(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags(_DictFlags(payload))
        _validate_payload_digest(payload)
        return payload
    raise ValueError(
        "report must be a ResearchDomainFootballSignalMemoryQualityReport or payload",
    )


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    value: ResearchDomainFootballSignalMemoryQualityInput,
    config: ResearchDomainFootballSignalMemoryQualityConfig,
) -> ResearchDomainFootballSignalMemoryQualityRow:
    lane_counts = _lane_counts(value)
    lane_ages = _lane_ages(value)
    missing_count = _decimal_count(
        sum(1 for lane in _LANES if lane_counts[lane] == _ZERO_COUNT),
    )
    stale_count = _decimal_count(
        sum(
            1
            for lane in _LANES
            if lane_counts[lane] > _ZERO_COUNT
            and lane_ages[lane] >= config.watch_stale_memory_seconds
        ),
    )
    coverage_ratio = _coverage_ratio(missing_count)
    freshness_ratio = _freshness_ratio(lane_counts, lane_ages, config)
    non_conflict_score = _non_conflict_score(value.conflicting_memory_count, config)
    urgency_safety_score = _quantize(_ONE - value.forecast_handoff_urgency_score)
    quality_score = _quality_score(
        coverage_ratio=coverage_ratio,
        freshness_ratio=freshness_ratio,
        non_conflict_score=non_conflict_score,
        urgency_safety_score=urgency_safety_score,
    )
    reason_codes = _row_reason_codes(
        lane_counts=lane_counts,
        lane_ages=lane_ages,
        conflicting_memory_count=value.conflicting_memory_count,
        forecast_handoff_urgency_score=value.forecast_handoff_urgency_score,
        quality_score=quality_score,
        config=config,
    )
    return ResearchDomainFootballSignalMemoryQualityRow(
        team_label=value.team_label,
        memory_context=value.memory_context,
        missing_memory_lane_count=missing_count,
        stale_memory_lane_count=stale_count,
        conflicting_memory_count=value.conflicting_memory_count,
        team_memory_age_seconds=value.team_memory_age_seconds,
        injury_memory_age_seconds=value.injury_memory_age_seconds,
        weather_memory_age_seconds=value.weather_memory_age_seconds,
        schedule_memory_age_seconds=value.schedule_memory_age_seconds,
        memory_coverage_ratio=coverage_ratio,
        memory_freshness_ratio=freshness_ratio,
        non_conflict_score=non_conflict_score,
        forecast_handoff_urgency_score=value.forecast_handoff_urgency_score,
        signal_memory_quality_score=quality_score,
        row_status=_status_from_reason_codes(reason_codes),
        observed_at=value.observed_at,
        reason_codes=reason_codes,
    )


def _lane_counts(
    value: ResearchDomainFootballSignalMemoryQualityInput,
) -> dict[str, Decimal]:
    return {
        "team": value.team_memory_count,
        "injury": value.injury_memory_count,
        "weather": value.weather_memory_count,
        "schedule": value.schedule_memory_count,
    }


def _lane_ages(
    value: ResearchDomainFootballSignalMemoryQualityInput,
) -> dict[str, Decimal]:
    return {
        "team": value.team_memory_age_seconds,
        "injury": value.injury_memory_age_seconds,
        "weather": value.weather_memory_age_seconds,
        "schedule": value.schedule_memory_age_seconds,
    }


def _coverage_ratio(missing_count: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize((_FOUR - missing_count) / _FOUR)


def _freshness_ratio(
    lane_counts: dict[str, Decimal],
    lane_ages: dict[str, Decimal],
    config: ResearchDomainFootballSignalMemoryQualityConfig,
) -> Decimal:
    active_ages = tuple(
        lane_ages[lane] for lane in _LANES if lane_counts[lane] > _ZERO_COUNT
    )
    if not active_ages:
        return _ZERO
    max_age = max(active_ages)
    if max_age < config.watch_stale_memory_seconds:
        return _ONE
    if max_age >= config.block_stale_memory_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        score = _ONE - (max_age / config.freshness_zero_age_seconds)
    if score <= _ZERO:
        return _ZERO
    if score >= _ONE:
        return _ONE
    return _quantize(score)


def _non_conflict_score(
    conflicting_memory_count: Decimal,
    config: ResearchDomainFootballSignalMemoryQualityConfig,
) -> Decimal:
    if conflicting_memory_count <= _ZERO_COUNT:
        return _ONE
    if conflicting_memory_count >= config.block_conflicting_memory_count:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            _ONE - (conflicting_memory_count / config.block_conflicting_memory_count),
        )


def _quality_score(
    *,
    coverage_ratio: Decimal,
    freshness_ratio: Decimal,
    non_conflict_score: Decimal,
    urgency_safety_score: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            (coverage_ratio + freshness_ratio + non_conflict_score + urgency_safety_score)
            / _FOUR,
        )


def _row_reason_codes(
    *,
    lane_counts: dict[str, Decimal],
    lane_ages: dict[str, Decimal],
    conflicting_memory_count: Decimal,
    forecast_handoff_urgency_score: Decimal,
    quality_score: Decimal,
    config: ResearchDomainFootballSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for lane in _LANES:
        if lane_counts[lane] == _ZERO_COUNT:
            reasons.append(f"{lane}_memory_missing")
        elif lane_ages[lane] >= config.block_stale_memory_seconds:
            reasons.append(f"{lane}_memory_stale_block")
        elif lane_ages[lane] >= config.watch_stale_memory_seconds:
            reasons.append(f"{lane}_memory_stale_watch")
    if conflicting_memory_count >= config.block_conflicting_memory_count:
        reasons.append("memory_conflicts_block")
    elif conflicting_memory_count >= config.watch_conflicting_memory_count:
        reasons.append("memory_conflicts_watch")
    if forecast_handoff_urgency_score >= config.block_forecast_handoff_urgency_score:
        reasons.append("forecast_handoff_urgency_block")
    elif forecast_handoff_urgency_score >= config.watch_forecast_handoff_urgency_score:
        reasons.append("forecast_handoff_urgency_watch")
    if any(reason.endswith("_block") for reason in reasons) or (
        quality_score < config.quality_watch_threshold
    ):
        reasons.append("football_signal_memory_quality_block")
    elif reasons or quality_score < config.quality_pass_threshold:
        reasons.append("football_signal_memory_quality_watch")
    else:
        reasons.append("football_signal_memory_quality_pass")
    return tuple(reason for reason in _ROW_REASON_PRIORITY if reason in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "football_signal_memory_quality_block" in reason_codes:
        return "block"
    if "football_signal_memory_quality_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchDomainFootballSignalMemoryQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainFootballSignalMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_football_signal_memory_inputs",)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "football_signal_memory_quality_pass"
    )
    if not present:
        return ("football_signal_memory_quality_pass",)
    return tuple(reason_code for reason_code in _ROW_REASON_PRIORITY if reason_code in present)


def _normalize_inputs(
    values: Iterable[ResearchDomainFootballSignalMemoryQualityInput],
) -> tuple[ResearchDomainFootballSignalMemoryQualityInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for value in normalized:
        _require_exact_type("memory_input", value, ResearchDomainFootballSignalMemoryQualityInput)
        _require_hard_flags(value)
        _reject_unsafe_public_surface("memory_input", value)
        key = (value.team_label, value.memory_context)
        if key in seen_keys:
            raise ValueError("inputs must use unique team and memory context labels")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchDomainFootballSignalMemoryQualityRow],
) -> tuple[ResearchDomainFootballSignalMemoryQualityRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchDomainFootballSignalMemoryQualityRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchDomainFootballSignalMemoryQualityRow values",
        ) from exc
    for row in rows:
        _require_exact_type("row", row, ResearchDomainFootballSignalMemoryQualityRow)
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    if len(set((row.team_label, row.memory_context) for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_row_consistency(row: ResearchDomainFootballSignalMemoryQualityRow) -> None:
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchDomainFootballSignalMemoryQualityReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _decimal_count(len({row.team_label for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.missing_memory_lane_total != _sum_decimal(
        tuple(row.missing_memory_lane_count for row in report.rows),
    ):
        raise ValueError("missing_memory_lane_total must match rows")
    if report.stale_memory_lane_total != _sum_decimal(
        tuple(row.stale_memory_lane_count for row in report.rows),
    ):
        raise ValueError("stale_memory_lane_total must match rows")
    if report.conflicting_memory_total != _sum_decimal(
        tuple(row.conflicting_memory_count for row in report.rows),
    ):
        raise ValueError("conflicting_memory_total must match rows")
    if report.forecast_handoff_ready_count != _status_count(report.rows, "pass"):
        raise ValueError("forecast_handoff_ready_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if report.average_signal_memory_quality_score != _average_score(
        tuple(row.signal_memory_quality_score for row in report.rows),
    ):
        raise ValueError("average_signal_memory_quality_score must match rows")


def _row_sort_key(
    row: ResearchDomainFootballSignalMemoryQualityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        _STATUS_RANK[row.row_status],
        row.signal_memory_quality_score,
        row.memory_coverage_ratio,
        row.memory_freshness_ratio,
        row.team_label,
        row.memory_context,
    )


def _status_count(
    rows: tuple[ResearchDomainFootballSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, _ZERO_COUNT).quantize(_COUNT_QUANTUM)


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in FOOTBALL_SIGNAL_MEMORY_QUALITY_REASON_CODES:
            raise ValueError("reason_codes contains an unsupported value")
    return normalized


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FOOTBALL_SIGNAL_MEMORY_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _COUNT_QUANTUM)
    if normalized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal_with_quantum(field_name, value, _QUANTUM)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal_with_quantum(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        if quantum == _COUNT_QUANTUM:
            raise ValueError(f"{field_name} must be a whole Decimal")
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_LABEL_FRAGMENTS):
            raise ValueError(f"unsafe public-safe label in {label}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be serialized strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    current = payload.get(_DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be present")
    if current != _derived_digest(payload) or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    canonical = _canonical_digest_value(value)
    encoded = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("unsupported payload value")
