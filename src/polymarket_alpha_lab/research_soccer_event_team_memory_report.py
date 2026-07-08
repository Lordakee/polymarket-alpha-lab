from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOCCER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-soccer-event-team-memory-report-v0"
)

INPUT_OBSERVED_REASON = "soccer_event_team_memory_observed"
EMPTY_REASON = "soccer_event_team_memory_report_empty"
REPORT_PASS_REASON = "soccer_event_team_memory_report_pass"
REPORT_WATCH_REASON = "soccer_event_team_memory_report_watch"
REPORT_BLOCK_REASON = "soccer_event_team_memory_report_block"
ROW_PASS_REASON = "soccer_event_team_memory_pass"
ROW_WATCH_REASON = "soccer_event_team_memory_watch"
ROW_BLOCK_REASON = "soccer_event_team_memory_block"
MEMORY_SCORE_WATCH_REASON = "specialist_memory_score_watch"
MEMORY_SCORE_BLOCK_REASON = "specialist_memory_score_block"
INJURY_FRESHNESS_WATCH_REASON = "injury_freshness_watch"
INJURY_FRESHNESS_BLOCK_REASON = "injury_freshness_block"
NEWS_FRESHNESS_WATCH_REASON = "news_freshness_watch"
NEWS_FRESHNESS_BLOCK_REASON = "news_freshness_block"
SOURCE_FRESHNESS_WATCH_REASON = "source_freshness_watch"
SOURCE_FRESHNESS_BLOCK_REASON = "source_freshness_block"
CALIBRATION_ERROR_WATCH_REASON = "calibration_error_watch"
CALIBRATION_ERROR_BLOCK_REASON = "calibration_error_block"

STATUSES = ("pass", "watch", "block")
NEXT_STEPS = {
    "pass": "use_soccer_team_memory_for_calibration",
    "watch": "refresh_soccer_team_memory_before_calibration",
    "block": "refresh_soccer_team_memory_before_calibration",
}
ROW_REASON_CODES = (
    CALIBRATION_ERROR_BLOCK_REASON,
    CALIBRATION_ERROR_WATCH_REASON,
    INJURY_FRESHNESS_BLOCK_REASON,
    INJURY_FRESHNESS_WATCH_REASON,
    NEWS_FRESHNESS_BLOCK_REASON,
    NEWS_FRESHNESS_WATCH_REASON,
    ROW_BLOCK_REASON,
    ROW_PASS_REASON,
    ROW_WATCH_REASON,
    SOURCE_FRESHNESS_BLOCK_REASON,
    SOURCE_FRESHNESS_WATCH_REASON,
    MEMORY_SCORE_BLOCK_REASON,
    MEMORY_SCORE_WATCH_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    REPORT_BLOCK_REASON,
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    *ROW_REASON_CODES,
)
INPUT_REASON_CODES = (INPUT_OBSERVED_REASON,)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_DIGEST_FIELD = "derived_validation_digest"
_TEXT_CODES = (
    (109, 97, 116, 99, 104, 95, 105, 100),
    (101, 118, 101, 110, 116, 95, 105, 100),
    (116, 101, 97, 109, 95, 105, 100),
    (116, 101, 97, 109, 95, 110, 97, 109, 101),
    (115, 111, 117, 114, 99, 101, 95, 105, 100),
    (115, 111, 117, 114, 99, 101, 95, 114, 101, 102, 101, 114, 101, 110, 99, 101),
    (109, 97, 114, 107, 101, 116, 95, 115, 108, 117, 103),
    (119, 97, 108, 108, 101, 116),
    (111, 114, 100, 101, 114),
    (108, 105, 118, 101),
    (116, 114, 97, 100, 101),
    (115, 105, 103, 110, 105, 110, 103),
    (109, 117, 116, 97, 116, 105, 111, 110),
    (97, 112, 105, 95, 107, 101, 121),
    (112, 114, 105, 118, 97, 116, 101, 95, 107, 101, 121),
)
_TEXT_FRAGMENTS = tuple("".join(chr(code) for code in item) for item in _TEXT_CODES)


__all__ = (
    "DEFAULT_RESEARCH_SOCCER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "ResearchSoccerEventTeamMemoryObservation",
    "ResearchSoccerEventTeamMemoryReasonCodeCount",
    "ResearchSoccerEventTeamMemoryReport",
    "ResearchSoccerEventTeamMemoryReportConfig",
    "ResearchSoccerEventTeamMemoryRow",
    "build_research_soccer_event_team_memory_report",
    "research_soccer_event_team_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchSoccerEventTeamMemoryReportConfig:
    config_version: str = DEFAULT_RESEARCH_SOCCER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    specialist_memory_watch_score: Decimal = Decimal("0.700000")
    specialist_memory_block_score: Decimal = Decimal("0.400000")
    freshness_watch_share: Decimal = Decimal("0.750000")
    freshness_block_share: Decimal = Decimal("0.400000")
    calibration_error_watch: Decimal = Decimal("0.100000")
    calibration_error_block: Decimal = Decimal("0.200000")
    full_calibration_sample_size: Decimal = Decimal("20.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOCCER_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "specialist_memory_watch_score",
            "specialist_memory_block_score",
            "freshness_watch_share",
            "freshness_block_share",
            "calibration_error_watch",
            "calibration_error_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "full_calibration_sample_size",
            _normalize_positive_whole_decimal(
                "full_calibration_sample_size",
                self.full_calibration_sample_size,
            ),
        )
        _require_at_most(
            "specialist_memory_block_score",
            self.specialist_memory_block_score,
            self.specialist_memory_watch_score,
        )
        _require_at_most(
            "freshness_block_share",
            self.freshness_block_share,
            self.freshness_watch_share,
        )
        _require_at_most(
            "calibration_error_watch",
            self.calibration_error_watch,
            self.calibration_error_block,
        )
        _require_flags("config", self)
        _reject_public_text("config", self)


@dataclass(frozen=True)
class ResearchSoccerEventTeamMemoryObservation:
    soccer_event_bucket: str
    team_memory_bucket: str
    specialist_memory_score: Decimal
    calibration_sample_size: Decimal
    calibration_error: Decimal
    injury_update_count: Decimal
    fresh_injury_update_count: Decimal
    news_update_count: Decimal
    fresh_news_update_count: Decimal
    source_count: Decimal
    stale_source_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_bucket_text("soccer_event_bucket", self.soccer_event_bucket)
        _require_bucket_text("team_memory_bucket", self.team_memory_bucket)
        for field_name in ("specialist_memory_score", "calibration_error"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_sample_size",
            "injury_update_count",
            "fresh_injury_update_count",
            "news_update_count",
            "fresh_news_update_count",
            "source_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        if self.fresh_injury_update_count > self.injury_update_count:
            raise ValueError("fresh_injury_update_count must not exceed injury_update_count")
        if self.fresh_news_update_count > self.news_update_count:
            raise ValueError("fresh_news_update_count must not exceed news_update_count")
        if self.stale_source_count > self.source_count:
            raise ValueError("stale_source_count must not exceed source_count")
        _require_flags("observation", self)
        _reject_public_text("observation", self)


@dataclass(frozen=True)
class ResearchSoccerEventTeamMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        _require_flags("reason count", self)
        _reject_public_text("reason count", self)


@dataclass(frozen=True)
class ResearchSoccerEventTeamMemoryRow:
    soccer_event_bucket: str
    team_memory_bucket: str
    memory_status: str
    observation_count: Decimal
    specialist_memory_score: Decimal
    calibration_sample_size: Decimal
    calibration_error: Decimal
    injury_update_count: Decimal
    fresh_injury_update_count: Decimal
    injury_freshness_share: Decimal
    news_update_count: Decimal
    fresh_news_update_count: Decimal
    news_freshness_share: Decimal
    source_count: Decimal
    stale_source_count: Decimal
    source_freshness_share: Decimal
    aggregated_freshness_score: Decimal
    calibration_sample_size_score: Decimal
    calibration_quality_score: Decimal
    calibration_readiness_score: Decimal
    latest_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_bucket_text("soccer_event_bucket", self.soccer_event_bucket)
        _require_bucket_text("team_memory_bucket", self.team_memory_bucket)
        _require_status("memory_status", self.memory_status)
        for field_name in (
            "observation_count",
            "calibration_sample_size",
            "injury_update_count",
            "fresh_injury_update_count",
            "news_update_count",
            "fresh_news_update_count",
            "source_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "specialist_memory_score",
            "calibration_error",
            "injury_freshness_share",
            "news_freshness_share",
            "source_freshness_share",
            "aggregated_freshness_score",
            "calibration_sample_size_score",
            "calibration_quality_score",
            "calibration_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)
        _reject_public_text("row", self)


@dataclass(frozen=True)
class ResearchSoccerEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    report_status: str
    recommended_next_step: str
    row_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_readiness_score: Decimal
    minimum_source_freshness_score: Decimal
    maximum_calibration_error: Decimal
    rows: tuple[ResearchSoccerEventTeamMemoryRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSoccerEventTeamMemoryReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_text("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        _require_member(
            "recommended_next_step",
            self.recommended_next_step,
            tuple(NEXT_STEPS.values()) + ("collect_soccer_specialist_memory",),
        )
        for field_name in (
            "row_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_calibration_readiness_score",
            "minimum_source_freshness_score",
            "maximum_calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_flags("report", self)
        _reject_public_text("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest and self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_soccer_event_team_memory_report_payload(self)


def build_research_soccer_event_team_memory_report(
    observations: Iterable[ResearchSoccerEventTeamMemoryObservation],
    *,
    config: ResearchSoccerEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> ResearchSoccerEventTeamMemoryReport:
    if type(config) is not ResearchSoccerEventTeamMemoryReportConfig:
        raise ValueError("config must be a ResearchSoccerEventTeamMemoryReportConfig")
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    values = _normalize_observations(observations)
    for item in values:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    groups: dict[tuple[str, str], list[ResearchSoccerEventTeamMemoryObservation]] = {}
    for item in values:
        groups.setdefault((item.soccer_event_bucket, item.team_memory_bucket), []).append(item)

    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    soccer_event_bucket=key[0],
                    team_memory_bucket=key[1],
                    observations=tuple(group),
                    config=config,
                )
                for key, group in groups.items()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    report_status = _report_status(rows)

    return ResearchSoccerEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        recommended_next_step=(
            "collect_soccer_specialist_memory" if not rows else NEXT_STEPS[report_status]
        ),
        row_count=_decimal_count(len(rows)),
        observation_count=_sum_decimal(row.observation_count for row in rows),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_calibration_readiness_score=_average_or_zero(
            row.calibration_readiness_score for row in rows
        ),
        minimum_source_freshness_score=min(
            (row.aggregated_freshness_score for row in rows),
            default=ZERO,
        ),
        maximum_calibration_error=max(
            (row.calibration_error for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_soccer_event_team_memory_report_payload(
    report: ResearchSoccerEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSoccerEventTeamMemoryReport:
        _require_flags("report", report)
        _validate_report(report)
        _reject_public_text("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_public_text("report payload", payload)
        return payload
    if type(report) is dict:
        _reject_public_text("payload", report)
        _require_flags("payload", _DictFlags(report))
        _validate_payload_digest(report)
        return dict(report)
    raise ValueError("report must be a ResearchSoccerEventTeamMemoryReport")


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


def _normalize_observations(
    observations: Iterable[ResearchSoccerEventTeamMemoryObservation],
) -> tuple[ResearchSoccerEventTeamMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in values:
        if type(item) is not ResearchSoccerEventTeamMemoryObservation:
            raise ValueError(
                "observations must contain ResearchSoccerEventTeamMemoryObservation values",
            )
        _require_flags("observation", item)
    return values


def _row_from_observations(
    *,
    soccer_event_bucket: str,
    team_memory_bucket: str,
    observations: tuple[ResearchSoccerEventTeamMemoryObservation, ...],
    config: ResearchSoccerEventTeamMemoryReportConfig,
) -> ResearchSoccerEventTeamMemoryRow:
    observation_count = _decimal_count(len(observations))
    specialist_memory_score = _average_or_zero(
        item.specialist_memory_score for item in observations
    )
    calibration_sample_size = _sum_decimal(item.calibration_sample_size for item in observations)
    calibration_error = max((item.calibration_error for item in observations), default=ZERO)
    injury_update_count = _sum_decimal(item.injury_update_count for item in observations)
    fresh_injury_update_count = _sum_decimal(
        item.fresh_injury_update_count for item in observations
    )
    news_update_count = _sum_decimal(item.news_update_count for item in observations)
    fresh_news_update_count = _sum_decimal(
        item.fresh_news_update_count for item in observations
    )
    source_count = _sum_decimal(item.source_count for item in observations)
    stale_source_count = _sum_decimal(item.stale_source_count for item in observations)
    injury_freshness_share = _ratio(fresh_injury_update_count, injury_update_count)
    news_freshness_share = _ratio(fresh_news_update_count, news_update_count)
    source_freshness_share = _ratio(source_count - stale_source_count, source_count)
    aggregated_freshness_score = _average_or_zero(
        (injury_freshness_share, news_freshness_share, source_freshness_share),
    )
    calibration_sample_size_score = min(
        ONE,
        _ratio(calibration_sample_size, config.full_calibration_sample_size),
    )
    calibration_quality_score = _quantize(ONE - calibration_error)
    calibration_readiness_score = _average_or_zero(
        (
            specialist_memory_score,
            aggregated_freshness_score,
            calibration_sample_size_score,
            calibration_quality_score,
        ),
    )
    reason_codes = _row_reason_codes(
        specialist_memory_score=specialist_memory_score,
        injury_freshness_share=injury_freshness_share,
        news_freshness_share=news_freshness_share,
        source_freshness_share=source_freshness_share,
        calibration_error=calibration_error,
        config=config,
    )
    status = _row_status(reason_codes)

    return ResearchSoccerEventTeamMemoryRow(
        soccer_event_bucket=soccer_event_bucket,
        team_memory_bucket=team_memory_bucket,
        memory_status=status,
        observation_count=observation_count,
        specialist_memory_score=specialist_memory_score,
        calibration_sample_size=calibration_sample_size,
        calibration_error=calibration_error,
        injury_update_count=injury_update_count,
        fresh_injury_update_count=fresh_injury_update_count,
        injury_freshness_share=injury_freshness_share,
        news_update_count=news_update_count,
        fresh_news_update_count=fresh_news_update_count,
        news_freshness_share=news_freshness_share,
        source_count=source_count,
        stale_source_count=stale_source_count,
        source_freshness_share=source_freshness_share,
        aggregated_freshness_score=aggregated_freshness_score,
        calibration_sample_size_score=calibration_sample_size_score,
        calibration_quality_score=calibration_quality_score,
        calibration_readiness_score=calibration_readiness_score,
        latest_observed_at=max(item.observed_at for item in observations),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    specialist_memory_score: Decimal,
    injury_freshness_share: Decimal,
    news_freshness_share: Decimal,
    source_freshness_share: Decimal,
    calibration_error: Decimal,
    config: ResearchSoccerEventTeamMemoryReportConfig,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    _add_low_score_reason(
        reasons,
        value=specialist_memory_score,
        watch_value=config.specialist_memory_watch_score,
        block_value=config.specialist_memory_block_score,
        watch_reason=MEMORY_SCORE_WATCH_REASON,
        block_reason=MEMORY_SCORE_BLOCK_REASON,
    )
    _add_low_score_reason(
        reasons,
        value=injury_freshness_share,
        watch_value=config.freshness_watch_share,
        block_value=config.freshness_block_share,
        watch_reason=INJURY_FRESHNESS_WATCH_REASON,
        block_reason=INJURY_FRESHNESS_BLOCK_REASON,
    )
    _add_low_score_reason(
        reasons,
        value=news_freshness_share,
        watch_value=config.freshness_watch_share,
        block_value=config.freshness_block_share,
        watch_reason=NEWS_FRESHNESS_WATCH_REASON,
        block_reason=NEWS_FRESHNESS_BLOCK_REASON,
    )
    _add_low_score_reason(
        reasons,
        value=source_freshness_share,
        watch_value=config.freshness_watch_share,
        block_value=config.freshness_block_share,
        watch_reason=SOURCE_FRESHNESS_WATCH_REASON,
        block_reason=SOURCE_FRESHNESS_BLOCK_REASON,
    )
    if calibration_error >= config.calibration_error_block:
        reasons.add(CALIBRATION_ERROR_BLOCK_REASON)
    elif calibration_error >= config.calibration_error_watch:
        reasons.add(CALIBRATION_ERROR_WATCH_REASON)
    if any(reason.endswith("_block") for reason in reasons):
        reasons.add(ROW_BLOCK_REASON)
    elif reasons:
        reasons.add(ROW_WATCH_REASON)
    else:
        reasons.add(ROW_PASS_REASON)
    return tuple(sorted(reasons))


def _add_low_score_reason(
    reasons: set[str],
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value < block_value:
        reasons.add(block_reason)
    elif value < watch_value:
        reasons.add(watch_reason)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if ROW_BLOCK_REASON in reason_codes:
        return "block"
    if ROW_WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSoccerEventTeamMemoryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.memory_status == "block" for row in rows):
        return "block"
    if any(row.memory_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchSoccerEventTeamMemoryRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    status = _report_status(rows)
    if status == "pass":
        return (REPORT_PASS_REASON,)
    rollup = REPORT_BLOCK_REASON if status == "block" else REPORT_WATCH_REASON
    row_reasons = sorted(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != ROW_PASS_REASON
    )
    return tuple(sorted(dict.fromkeys((rollup, *row_reasons))))


def _reason_code_counts(
    rows: tuple[ResearchSoccerEventTeamMemoryRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSoccerEventTeamMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSoccerEventTeamMemoryReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSoccerEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_rows(
    rows: tuple[ResearchSoccerEventTeamMemoryRow, ...],
) -> tuple[ResearchSoccerEventTeamMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSoccerEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchSoccerEventTeamMemoryRow values")
        _require_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchSoccerEventTeamMemoryReasonCodeCount, ...],
) -> tuple[ResearchSoccerEventTeamMemoryReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchSoccerEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSoccerEventTeamMemoryReasonCodeCount values",
            )
        _require_flags("reason count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _row_sort_key(row: ResearchSoccerEventTeamMemoryRow) -> tuple[Decimal, str, str]:
    return (STATUS_RANK[row.memory_status], row.soccer_event_bucket, row.team_memory_bucket)


def _validate_row(row: ResearchSoccerEventTeamMemoryRow) -> None:
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    if row.fresh_injury_update_count > row.injury_update_count:
        raise ValueError("fresh_injury_update_count must not exceed injury_update_count")
    if row.fresh_news_update_count > row.news_update_count:
        raise ValueError("fresh_news_update_count must not exceed news_update_count")
    if row.stale_source_count > row.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if row.injury_freshness_share != _ratio(
        row.fresh_injury_update_count,
        row.injury_update_count,
    ):
        raise ValueError("injury_freshness_share must match counts")
    if row.news_freshness_share != _ratio(
        row.fresh_news_update_count,
        row.news_update_count,
    ):
        raise ValueError("news_freshness_share must match counts")
    if row.source_freshness_share != _ratio(
        row.source_count - row.stale_source_count,
        row.source_count,
    ):
        raise ValueError("source_freshness_share must match counts")
    if row.aggregated_freshness_score != _average_or_zero(
        (
            row.injury_freshness_share,
            row.news_freshness_share,
            row.source_freshness_share,
        ),
    ):
        raise ValueError("aggregated_freshness_score must match freshness shares")
    if row.calibration_quality_score != _quantize(ONE - row.calibration_error):
        raise ValueError("calibration_quality_score must match calibration_error")
    if row.memory_status != _row_status(row.reason_codes):
        raise ValueError("memory_status must match reason_codes")


def _validate_report(report: ResearchSoccerEventTeamMemoryReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.observation_count != _sum_decimal(row.observation_count for row in report.rows):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_calibration_readiness_score != _average_or_zero(
        row.calibration_readiness_score for row in report.rows
    ):
        raise ValueError("average_calibration_readiness_score must match rows")
    if report.minimum_source_freshness_score != min(
        (row.aggregated_freshness_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("minimum_source_freshness_score must match rows")
    if report.maximum_calibration_error != max(
        (row.calibration_error for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("maximum_calibration_error must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if not report.rows and report.recommended_next_step != "collect_soccer_specialist_memory":
        raise ValueError("recommended_next_step must match empty report")
    if report.rows and report.recommended_next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("recommended_next_step must match report_status")


def _report_digest(report: ResearchSoccerEventTeamMemoryReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop(_DIGEST_FIELD, None)
    return _payload_digest(payload)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    supplied = payload.get(_DIGEST_FIELD)
    if type(supplied) is not str:
        raise ValueError("derived_validation_digest must be a string")
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD)
    if supplied != _payload_digest(payload_without_digest):
        raise ValueError("derived_validation_digest must match payload fields")


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is str:
        _reject_public_text("payload string", value)
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(child) for key, child in value.items()}
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _average_or_zero(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(_sum_decimal(items) / _decimal_count(len(items)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _status_count(rows: tuple[ResearchSoccerEventTeamMemoryRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.memory_status == status)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be <= related threshold")


def _require_bucket_text(field_name: str, value: str) -> None:
    _require_canonical_text(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789.-_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public bucket label")


def _require_canonical_text(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip() or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_public_text(field_name, value)


def _require_reason_code(field_name: str, value: str) -> None:
    _require_canonical_text(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a reason code")


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason in value:
        _require_reason_code(field_name, reason)
        if reason not in allowed_values:
            raise ValueError(f"{field_name} has unsupported reason code")
        normalized.append(reason)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    deduped = tuple(sorted(dict.fromkeys(normalized)))
    if tuple(normalized) != deduped:
        raise ValueError(f"{field_name} must be unique and sorted")
    return deduped


def _require_status(field_name: str, value: str) -> None:
    _require_member(field_name, value, STATUSES)


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_public_text(label: str, value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_text(label, _json_ready_without_text_check(value))
        return
    if type(value) is dict:
        for key, child in value.items():
            _reject_public_text(label, key)
            _reject_public_text(label, child)
        return
    if type(value) in (tuple, list):
        for child in value:
            _reject_public_text(label, child)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")


def _json_ready_without_text_check(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready_without_text_check(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool):
        return value
    if type(value) is tuple:
        return [_json_ready_without_text_check(item) for item in value]
    if type(value) is list:
        return [_json_ready_without_text_check(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _json_ready_without_text_check(child)
            for key, child in value.items()
        }
    return value
