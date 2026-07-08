"""Pure report-only reducer for weather event team memory readiness."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_WEATHER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-weather-event-team-memory-report-v0"
)

EMPTY_REASON = "weather_event_memory_report_empty"
CALIBRATION_BRIER_BLOCK_REASON = "weather_event_memory_calibration_brier_block"
CALIBRATION_SAMPLE_BLOCK_REASON = "weather_event_memory_calibration_sample_block"
EVIDENCE_REUSE_BLOCK_REASON = "weather_event_memory_evidence_reuse_block"
FORECAST_SOURCE_STALE_BLOCK_REASON = (
    "weather_event_memory_forecast_source_stale_block"
)
MEMORY_STALE_BLOCK_REASON = "weather_event_memory_stale_block"
CALIBRATION_BRIER_WATCH_REASON = "weather_event_memory_calibration_brier_watch"
CALIBRATION_SAMPLE_WATCH_REASON = "weather_event_memory_calibration_sample_watch"
EVIDENCE_REUSE_WATCH_REASON = "weather_event_memory_evidence_reuse_watch"
FORECAST_SOURCE_STALE_WATCH_REASON = (
    "weather_event_memory_forecast_source_stale_watch"
)
MEMORY_STALE_WATCH_REASON = "weather_event_memory_stale_watch"
READY_REASON = "weather_event_memory_ready"

REASON_CODES = (
    EMPTY_REASON,
    CALIBRATION_BRIER_BLOCK_REASON,
    CALIBRATION_SAMPLE_BLOCK_REASON,
    EVIDENCE_REUSE_BLOCK_REASON,
    FORECAST_SOURCE_STALE_BLOCK_REASON,
    MEMORY_STALE_BLOCK_REASON,
    CALIBRATION_BRIER_WATCH_REASON,
    CALIBRATION_SAMPLE_WATCH_REASON,
    EVIDENCE_REUSE_WATCH_REASON,
    FORECAST_SOURCE_STALE_WATCH_REASON,
    MEMORY_STALE_WATCH_REASON,
    READY_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCK_REASONS = (
    EMPTY_REASON,
    CALIBRATION_BRIER_BLOCK_REASON,
    CALIBRATION_SAMPLE_BLOCK_REASON,
    EVIDENCE_REUSE_BLOCK_REASON,
    FORECAST_SOURCE_STALE_BLOCK_REASON,
    MEMORY_STALE_BLOCK_REASON,
)
WATCH_REASONS = (
    CALIBRATION_BRIER_WATCH_REASON,
    CALIBRATION_SAMPLE_WATCH_REASON,
    EVIDENCE_REUSE_WATCH_REASON,
    FORECAST_SOURCE_STALE_WATCH_REASON,
    MEMORY_STALE_WATCH_REASON,
)
STATUSES = ("pass", "watch", "block")
NEXT_REVIEW_STEPS = {
    "pass": "reuse_weather_event_memory",
    "watch": "review_weather_event_memory",
    "block": "pause_weather_event_memory_reuse",
}

VALUE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
AGGREGATE_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "slug",
    "question",
    "market",
    "candidate",
    "source_url",
    "url",
    "token",
    "sec" + "ret",
    "au" + "th",
    "priv" + "ate" + "_" + "key",
    "wall" + "et",
    "ord" + "er",
    "sig" + "ning",
    "trade",
)

__all__ = (
    "DEFAULT_RESEARCH_WEATHER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "ResearchWeatherEventTeamMemoryObservation",
    "ResearchWeatherEventTeamMemoryReport",
    "ResearchWeatherEventTeamMemoryReportConfig",
    "ResearchWeatherEventTeamMemoryReportReasonCodeCount",
    "ResearchWeatherEventTeamMemoryReportRow",
    "build_research_weather_event_team_memory_report",
    "research_weather_event_team_memory_report_digest",
    "research_weather_event_team_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchWeatherEventTeamMemoryReportConfig:
    config_version: str = DEFAULT_RESEARCH_WEATHER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    memory_stale_watch_age_seconds: Decimal = Decimal("1209600.000000")
    memory_stale_block_age_seconds: Decimal = Decimal("2592000.000000")
    forecast_source_stale_watch_age_seconds: Decimal = Decimal("21600.000000")
    forecast_source_stale_block_age_seconds: Decimal = Decimal("172800.000000")
    min_evidence_reuse_ratio_watch: Decimal = Decimal("0.600000")
    min_evidence_reuse_ratio_block: Decimal = Decimal("0.250000")
    min_calibration_sample_count_watch: Decimal = Decimal("5.000000")
    min_calibration_sample_count_block: Decimal = Decimal("2.000000")
    max_recent_brier_score_watch: Decimal = Decimal("0.200000")
    max_recent_brier_score_block: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "memory_stale_watch_age_seconds",
            "memory_stale_block_age_seconds",
            "forecast_source_stale_watch_age_seconds",
            "forecast_source_stale_block_age_seconds",
            "min_calibration_sample_count_watch",
            "min_calibration_sample_count_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_evidence_reuse_ratio_watch",
            "min_evidence_reuse_ratio_block",
            "max_recent_brier_score_watch",
            "max_recent_brier_score_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("weather event memory config", self)


@dataclass(frozen=True)
class ResearchWeatherEventTeamMemoryObservation:
    team_id: str
    specialist_role: str
    event_family: str
    region_bucket: str
    memory_last_refreshed_at: datetime
    forecast_source_last_seen_at: datetime
    evidence_reuse_count: Decimal
    evidence_reuse_ratio: Decimal
    calibration_sample_count: Decimal
    recent_brier_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "specialist_role",
            "event_family",
            "region_bucket",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_aggregate_safe_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_last_refreshed_at",
            _as_utc("memory_last_refreshed_at", self.memory_last_refreshed_at),
        )
        object.__setattr__(
            self,
            "forecast_source_last_seen_at",
            _as_utc("forecast_source_last_seen_at", self.forecast_source_last_seen_at),
        )
        object.__setattr__(
            self,
            "evidence_reuse_count",
            _normalize_nonnegative_decimal(
                "evidence_reuse_count",
                self.evidence_reuse_count,
            ),
        )
        object.__setattr__(
            self,
            "evidence_reuse_ratio",
            _normalize_ratio("evidence_reuse_ratio", self.evidence_reuse_ratio),
        )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _normalize_nonnegative_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "recent_brier_score",
            _normalize_ratio("recent_brier_score", self.recent_brier_score),
        )
        _require_hard_flags("weather event memory observation", self)


@dataclass(frozen=True)
class ResearchWeatherEventTeamMemoryReportRow:
    team_id: str
    specialist_role: str
    event_family: str
    region_bucket: str
    readiness_status: str
    memory_age_seconds: Decimal
    forecast_source_age_seconds: Decimal
    evidence_reuse_count: Decimal
    evidence_reuse_ratio: Decimal
    calibration_sample_count: Decimal
    recent_brier_score: Decimal
    readiness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "specialist_role",
            "event_family",
            "region_bucket",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_aggregate_safe_label(field_name, getattr(self, field_name)),
            )
        _require_status("readiness_status", self.readiness_status)
        for field_name in (
            "memory_age_seconds",
            "forecast_source_age_seconds",
            "evidence_reuse_count",
            "calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_reuse_ratio",
            "recent_brier_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.readiness_status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("readiness_status must match reason_codes")
        _require_hard_flags("weather event memory row", self)


@dataclass(frozen=True)
class ResearchWeatherEventTeamMemoryReportReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("weather event memory reason count", self)


@dataclass(frozen=True)
class ResearchWeatherEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_review_step: str
    observation_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_count: Decimal
    stale_forecast_source_count: Decimal
    evidence_reuse_gap_count: Decimal
    calibration_gap_count: Decimal
    mean_evidence_reuse_ratio: Decimal
    mean_recent_brier_score: Decimal
    max_memory_age_seconds: Decimal
    max_forecast_source_age_seconds: Decimal
    rows: tuple[ResearchWeatherEventTeamMemoryReportRow, ...]
    reason_code_counts: tuple[ResearchWeatherEventTeamMemoryReportReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("next_review_step", self.next_review_step)
        for field_name in (
            "observation_count",
            "team_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "stale_forecast_source_count",
            "evidence_reuse_gap_count",
            "calibration_gap_count",
            "max_memory_age_seconds",
            "max_forecast_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_evidence_reuse_ratio", "mean_recent_brier_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("weather event memory report", self)


def build_research_weather_event_team_memory_report(
    observations: list[ResearchWeatherEventTeamMemoryObservation]
    | tuple[ResearchWeatherEventTeamMemoryObservation, ...],
    *,
    config: ResearchWeatherEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> ResearchWeatherEventTeamMemoryReport:
    if type(config) is not ResearchWeatherEventTeamMemoryReportConfig:
        raise ValueError("config must be ResearchWeatherEventTeamMemoryReportConfig")
    _require_hard_flags("weather event memory config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _build_row(
                    observation=observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=lambda row: (
                {"block": 0, "watch": 1, "pass": 2}[row.readiness_status],
                row.team_id,
                row.specialist_role,
                row.event_family,
                row.region_bucket,
            ),
        )
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _status_for_reason_codes(reason_codes)
    return ResearchWeatherEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        next_review_step=NEXT_REVIEW_STEPS[digest_status],
        observation_count=_decimal_count(len(rows)),
        team_count=_decimal_count(len({row.team_id for row in rows})),
        specialist_count=_decimal_count(len({row.specialist_role for row in rows})),
        pass_count=_decimal_count(sum(1 for row in rows if row.readiness_status == "pass")),
        watch_count=_decimal_count(
            sum(1 for row in rows if row.readiness_status == "watch"),
        ),
        block_count=_decimal_count(
            sum(1 for row in rows if row.readiness_status == "block"),
        ),
        stale_memory_count=_decimal_count(
            sum(
                1
                for row in rows
                if MEMORY_STALE_BLOCK_REASON in row.reason_codes
                or MEMORY_STALE_WATCH_REASON in row.reason_codes
            ),
        ),
        stale_forecast_source_count=_decimal_count(
            sum(
                1
                for row in rows
                if FORECAST_SOURCE_STALE_BLOCK_REASON in row.reason_codes
                or FORECAST_SOURCE_STALE_WATCH_REASON in row.reason_codes
            ),
        ),
        evidence_reuse_gap_count=_decimal_count(
            sum(
                1
                for row in rows
                if EVIDENCE_REUSE_BLOCK_REASON in row.reason_codes
                or EVIDENCE_REUSE_WATCH_REASON in row.reason_codes
            ),
        ),
        calibration_gap_count=_decimal_count(
            sum(
                1
                for row in rows
                if CALIBRATION_BRIER_BLOCK_REASON in row.reason_codes
                or CALIBRATION_BRIER_WATCH_REASON in row.reason_codes
                or CALIBRATION_SAMPLE_BLOCK_REASON in row.reason_codes
                or CALIBRATION_SAMPLE_WATCH_REASON in row.reason_codes
            ),
        ),
        mean_evidence_reuse_ratio=_average_decimal(
            tuple(row.evidence_reuse_ratio for row in rows),
        ),
        mean_recent_brier_score=_average_decimal(
            tuple(row.recent_brier_score for row in rows),
        ),
        max_memory_age_seconds=max(
            (row.memory_age_seconds for row in rows),
            default=ZERO,
        ),
        max_forecast_source_age_seconds=max(
            (row.forecast_source_age_seconds for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_weather_event_team_memory_report_payload(value: object) -> dict[str, Any]:
    if isinstance(
        value,
        (
            ResearchWeatherEventTeamMemoryReportConfig,
            ResearchWeatherEventTeamMemoryObservation,
            ResearchWeatherEventTeamMemoryReportRow,
            ResearchWeatherEventTeamMemoryReportReasonCodeCount,
            ResearchWeatherEventTeamMemoryReport,
        ),
    ):
        _require_hard_flags("weather event memory payload", value)
    elif type(value) is not dict:
        raise ValueError("value must be a weather event memory dataclass or JSON object")
    _reject_unsafe_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("weather event memory payload must be a JSON object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    return payload


def research_weather_event_team_memory_report_digest(value: object) -> str:
    payload = research_weather_event_team_memory_report_payload(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _build_row(
    *,
    observation: ResearchWeatherEventTeamMemoryObservation,
    config: ResearchWeatherEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> ResearchWeatherEventTeamMemoryReportRow:
    memory_age_seconds = _age_seconds(generated_at, observation.memory_last_refreshed_at)
    forecast_source_age_seconds = _age_seconds(
        generated_at,
        observation.forecast_source_last_seen_at,
    )
    reason_codes = _row_reason_codes(
        memory_age_seconds=memory_age_seconds,
        forecast_source_age_seconds=forecast_source_age_seconds,
        evidence_reuse_ratio=observation.evidence_reuse_ratio,
        calibration_sample_count=observation.calibration_sample_count,
        recent_brier_score=observation.recent_brier_score,
        config=config,
    )
    return ResearchWeatherEventTeamMemoryReportRow(
        team_id=observation.team_id,
        specialist_role=observation.specialist_role,
        event_family=observation.event_family,
        region_bucket=observation.region_bucket,
        readiness_status=_status_for_reason_codes(reason_codes),
        memory_age_seconds=memory_age_seconds,
        forecast_source_age_seconds=forecast_source_age_seconds,
        evidence_reuse_count=observation.evidence_reuse_count,
        evidence_reuse_ratio=observation.evidence_reuse_ratio,
        calibration_sample_count=observation.calibration_sample_count,
        recent_brier_score=observation.recent_brier_score,
        readiness_score=_readiness_score(observation, reason_codes, config),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    memory_age_seconds: Decimal,
    forecast_source_age_seconds: Decimal,
    evidence_reuse_ratio: Decimal,
    calibration_sample_count: Decimal,
    recent_brier_score: Decimal,
    config: ResearchWeatherEventTeamMemoryReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if recent_brier_score >= config.max_recent_brier_score_block:
        reason_codes.append(CALIBRATION_BRIER_BLOCK_REASON)
    elif recent_brier_score >= config.max_recent_brier_score_watch:
        reason_codes.append(CALIBRATION_BRIER_WATCH_REASON)
    if calibration_sample_count < config.min_calibration_sample_count_block:
        reason_codes.append(CALIBRATION_SAMPLE_BLOCK_REASON)
    elif calibration_sample_count < config.min_calibration_sample_count_watch:
        reason_codes.append(CALIBRATION_SAMPLE_WATCH_REASON)
    if evidence_reuse_ratio < config.min_evidence_reuse_ratio_block:
        reason_codes.append(EVIDENCE_REUSE_BLOCK_REASON)
    elif evidence_reuse_ratio < config.min_evidence_reuse_ratio_watch:
        reason_codes.append(EVIDENCE_REUSE_WATCH_REASON)
    if forecast_source_age_seconds >= config.forecast_source_stale_block_age_seconds:
        reason_codes.append(FORECAST_SOURCE_STALE_BLOCK_REASON)
    elif forecast_source_age_seconds >= config.forecast_source_stale_watch_age_seconds:
        reason_codes.append(FORECAST_SOURCE_STALE_WATCH_REASON)
    if memory_age_seconds >= config.memory_stale_block_age_seconds:
        reason_codes.append(MEMORY_STALE_BLOCK_REASON)
    elif memory_age_seconds >= config.memory_stale_watch_age_seconds:
        reason_codes.append(MEMORY_STALE_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _readiness_score(
    observation: ResearchWeatherEventTeamMemoryObservation,
    reason_codes: tuple[str, ...],
    config: ResearchWeatherEventTeamMemoryReportConfig,
) -> Decimal:
    if _status_for_reason_codes(reason_codes) == "block":
        return ZERO
    calibration_sample_score = _cap_ratio(
        observation.calibration_sample_count / config.min_calibration_sample_count_watch,
    )
    return _average_decimal(
        (
            ONE,
            ONE,
            observation.evidence_reuse_ratio,
            calibration_sample_score,
            ONE - observation.recent_brier_score,
        ),
    )


def _normalize_observations(
    observations: list[ResearchWeatherEventTeamMemoryObservation]
    | tuple[ResearchWeatherEventTeamMemoryObservation, ...],
    *,
    generated_at: datetime,
) -> tuple[ResearchWeatherEventTeamMemoryObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen: set[tuple[str, str, str, str]] = set()
    for observation in normalized:
        if type(observation) is not ResearchWeatherEventTeamMemoryObservation:
            raise ValueError(
                "observations must contain ResearchWeatherEventTeamMemoryObservation",
            )
        _require_hard_flags("weather event memory observation", observation)
        if observation.memory_last_refreshed_at > generated_at:
            raise ValueError("memory_last_refreshed_at must not be after generated_at")
        if observation.forecast_source_last_seen_at > generated_at:
            raise ValueError("forecast_source_last_seen_at must not be after generated_at")
        key = (
            observation.team_id,
            observation.specialist_role,
            observation.event_family,
            observation.region_bucket,
        )
        if key in seen:
            raise ValueError("observations must not contain duplicate aggregate keys")
        seen.add(key)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_id,
                item.specialist_role,
                item.event_family,
                item.region_bucket,
            ),
        )
    )


def _report_reason_codes(
    rows: tuple[ResearchWeatherEventTeamMemoryReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        )
    )


def _reason_code_counts(
    rows: tuple[ResearchWeatherEventTeamMemoryReportRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchWeatherEventTeamMemoryReportReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchWeatherEventTeamMemoryReportReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchWeatherEventTeamMemoryReportReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_quantize(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_config(config: ResearchWeatherEventTeamMemoryReportConfig) -> None:
    if config.memory_stale_watch_age_seconds >= config.memory_stale_block_age_seconds:
        raise ValueError("memory stale watch threshold must be below block threshold")
    if (
        config.forecast_source_stale_watch_age_seconds
        >= config.forecast_source_stale_block_age_seconds
    ):
        raise ValueError("forecast source stale watch threshold must be below block threshold")
    if config.min_evidence_reuse_ratio_block >= config.min_evidence_reuse_ratio_watch:
        raise ValueError("evidence reuse block threshold must be below watch threshold")
    if config.min_calibration_sample_count_block >= config.min_calibration_sample_count_watch:
        raise ValueError("calibration sample block threshold must be below watch threshold")
    if config.max_recent_brier_score_watch >= config.max_recent_brier_score_block:
        raise ValueError("recent brier watch threshold must be below block threshold")


def _validate_report(report: ResearchWeatherEventTeamMemoryReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.team_count != _decimal_count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_count != _decimal_count(
        len({row.specialist_role for row in report.rows}),
    ):
        raise ValueError("specialist_count must match rows")
    if report.pass_count != _decimal_count(
        sum(1 for row in report.rows if row.readiness_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.readiness_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(
        sum(1 for row in report.rows if row.readiness_status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.digest_status]:
        raise ValueError("next_review_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchWeatherEventTeamMemoryReportRow, ...],
) -> tuple[ResearchWeatherEventTeamMemoryReportRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchWeatherEventTeamMemoryReportRow:
            raise ValueError("rows must contain ResearchWeatherEventTeamMemoryReportRow")
        _require_hard_flags("weather event memory row", row)
        key = (row.team_id, row.specialist_role, row.event_family, row.region_bucket)
        if key in seen:
            raise ValueError("rows must not contain duplicate aggregate keys")
        seen.add(key)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                {"block": 0, "watch": 1, "pass": 2}[row.readiness_status],
                row.team_id,
                row.specialist_role,
                row.event_family,
                row.region_bucket,
            ),
        )
    ):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[ResearchWeatherEventTeamMemoryReportReasonCodeCount, ...],
) -> tuple[ResearchWeatherEventTeamMemoryReportReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    seen: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchWeatherEventTeamMemoryReportReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchWeatherEventTeamMemoryReportReasonCodeCount",
            )
        _require_hard_flags("weather event memory reason count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(count.reason_code)
    if normalized != tuple(
        sorted(normalized, key=lambda count: REASON_CODE_RANK[count.reason_code])
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    stable_codes = tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)
    if stable_codes != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) is dict:
        return _payload_dict(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_dict(value: dict[Any, Any]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        payload[key] = _payload_value(item)
    return payload


def _validate_payload_flags(value: object, field_path: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in value:
                raise ValueError(f"{field_path}.{flag} must be present")
            if value[flag] is not True:
                raise ValueError(f"{field_path}.{flag} must be True")
        for key, item in value.items():
            if type(item) is dict:
                _validate_payload_flags(item, f"{field_path}.{key}")
            elif type(item) is list:
                for index, nested_item in enumerate(item):
                    if type(nested_item) is dict:
                        _validate_payload_flags(nested_item, f"{field_path}.{key}.{index}")


def _reject_unsafe_public_payload(value: object) -> None:
    for key in _iter_payload_keys(value):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
            raise ValueError(f"unsafe surface field in payload: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        keys: list[str] = []
        for item in fields(value):
            keys.append(item.name)
            keys.extend(_iter_payload_keys(getattr(value, item.name)))
        return tuple(keys)
    if type(value) is dict:
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if type(value) in (list, tuple):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    micros = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _normalize_nonnegative_decimal(
        "age_seconds",
        micros / MICROSECONDS_PER_SECOND,
    )


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _cap_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), ZERO), ONE)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANT, rounding=ROUND_HALF_EVEN)


def _require_aggregate_safe_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if AGGREGATE_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be an aggregate-safe label")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
