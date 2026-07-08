"""Pure report for baseball event specialist memory readiness."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_BASEBALL_EVENT_TEAM_MEMORY_CONFIG_VERSION = (
    "research-baseball-event-team-memory-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_baseball_event_team_memory",
    STATUS_WATCH: "watch_report_only_baseball_event_team_memory",
    STATUS_BLOCK: "block_report_only_baseball_event_team_memory",
}

NO_INPUTS_REASON = "baseball_event_team_memory_no_inputs"
CALIBRATION_BLOCK_REASON = "baseball_event_team_memory_calibration_block"
CALIBRATION_PASS_REASON = "baseball_event_team_memory_calibration_pass"
CALIBRATION_WATCH_REASON = "baseball_event_team_memory_calibration_watch"
FRESH_REASON = "baseball_event_team_memory_fresh"
INJURY_STALE_REASON = "baseball_event_team_memory_injury_stale"
LINEUP_MISSING_REASON = "baseball_event_team_memory_lineup_missing"
LINEUP_STALE_REASON = "baseball_event_team_memory_lineup_stale"
MEMORY_SCORE_BLOCK_REASON = "baseball_event_team_memory_memory_score_block"
MEMORY_SCORE_WATCH_REASON = "baseball_event_team_memory_memory_score_watch"
NEWS_STALE_REASON = "baseball_event_team_memory_news_stale"
PASS_REASON = "baseball_event_team_memory_pass"
WATCH_REASON = "baseball_event_team_memory_watch"

REASON_CODES = tuple(
    sorted(
        (
            NO_INPUTS_REASON,
            CALIBRATION_BLOCK_REASON,
            CALIBRATION_PASS_REASON,
            CALIBRATION_WATCH_REASON,
            FRESH_REASON,
            INJURY_STALE_REASON,
            LINEUP_MISSING_REASON,
            LINEUP_STALE_REASON,
            MEMORY_SCORE_BLOCK_REASON,
            MEMORY_SCORE_WATCH_REASON,
            NEWS_STALE_REASON,
            PASS_REASON,
            WATCH_REASON,
        ),
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class ResearchBaseballEventTeamMemoryConfig:
    config_version: str = DEFAULT_RESEARCH_BASEBALL_EVENT_TEAM_MEMORY_CONFIG_VERSION
    fresh_lineup_max_age_seconds: Decimal = Decimal("3600.000000")
    fresh_injury_max_age_seconds: Decimal = Decimal("3600.000000")
    fresh_news_max_age_seconds: Decimal = Decimal("3600.000000")
    pass_memory_score: Decimal = Decimal("0.750000")
    watch_memory_score: Decimal = Decimal("0.550000")
    pass_calibration_sample_count: Decimal = Decimal("30.000000")
    watch_calibration_sample_count: Decimal = Decimal("10.000000")
    pass_calibration_hit_rate: Decimal = Decimal("0.600000")
    watch_calibration_hit_rate: Decimal = Decimal("0.500000")
    pass_calibration_error: Decimal = Decimal("0.100000")
    watch_calibration_error: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchBaseballEventTeamMemoryConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_lineup_max_age_seconds",
            "fresh_injury_max_age_seconds",
            "fresh_news_max_age_seconds",
            "pass_calibration_sample_count",
            "watch_calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_memory_score",
            "watch_memory_score",
            "pass_calibration_hit_rate",
            "watch_calibration_hit_rate",
            "pass_calibration_error",
            "watch_calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_memory_score <= self.watch_memory_score:
            raise ValueError("pass_memory_score must exceed watch_memory_score")
        if self.pass_calibration_sample_count <= self.watch_calibration_sample_count:
            raise ValueError(
                "pass_calibration_sample_count must exceed watch_calibration_sample_count",
            )
        if self.pass_calibration_hit_rate <= self.watch_calibration_hit_rate:
            raise ValueError(
                "pass_calibration_hit_rate must exceed watch_calibration_hit_rate",
            )
        if self.pass_calibration_error >= self.watch_calibration_error:
            raise ValueError(
                "pass_calibration_error must be less than watch_calibration_error",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchBaseballEventTeamMemoryInputRow:
    research_slug: str
    specialist_id: str
    market_category: str
    event_bucket: str
    lineup_observed_at: datetime | None
    injury_observed_at: datetime | None
    news_observed_at: datetime | None
    lineup_memory_score: Decimal
    injury_memory_score: Decimal
    news_memory_score: Decimal
    calibration_sample_count: Decimal
    calibration_hit_rate: Decimal
    calibration_error: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchBaseballEventTeamMemoryInputRow, "input row")
        for field_name in ("research_slug", "specialist_id", "event_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        if self.market_category != "baseball":
            raise ValueError("market_category must be baseball")
        for field_name in (
            "lineup_observed_at",
            "injury_observed_at",
            "news_observed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lineup_memory_score",
            "injury_memory_score",
            "news_memory_score",
            "calibration_hit_rate",
            "calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchBaseballEventTeamMemoryReportRow:
    research_slug: str
    specialist_id: str
    market_category: str
    event_bucket: str
    status: str
    freshness_status: str
    calibration_status: str
    lineup_observed_at: datetime | None
    injury_observed_at: datetime | None
    news_observed_at: datetime | None
    lineup_age_seconds: Decimal | None
    injury_age_seconds: Decimal | None
    news_age_seconds: Decimal | None
    lineup_memory_score: Decimal
    injury_memory_score: Decimal
    news_memory_score: Decimal
    specialist_memory_score: Decimal
    calibration_sample_count: Decimal
    calibration_hit_rate: Decimal
    calibration_error: Decimal
    freshness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchBaseballEventTeamMemoryReportRow, "row")
        for field_name in ("research_slug", "specialist_id", "event_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        if self.market_category != "baseball":
            raise ValueError("market_category must be baseball")
        for field_name in ("status", "freshness_status", "calibration_status"):
            _require_status(field_name, getattr(self, field_name))
        for field_name in (
            "lineup_observed_at",
            "injury_observed_at",
            "news_observed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lineup_age_seconds",
            "injury_age_seconds",
            "news_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "lineup_memory_score",
            "injury_memory_score",
            "news_memory_score",
            "specialist_memory_score",
            "calibration_hit_rate",
            "calibration_error",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchBaseballEventTeamMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchBaseballEventTeamMemoryReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_decimal("count", self.count))
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchBaseballEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    recommended_next_step: str
    event_memory_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    lineup_fresh_count: Decimal
    injury_fresh_count: Decimal
    news_fresh_count: Decimal
    lineup_missing_count: Decimal
    injury_missing_count: Decimal
    news_missing_count: Decimal
    freshness_pass_count: Decimal
    freshness_watch_count: Decimal
    freshness_block_count: Decimal
    calibration_pass_count: Decimal
    calibration_watch_count: Decimal
    calibration_block_count: Decimal
    average_specialist_memory_score: Decimal
    average_calibration_error: Decimal
    average_freshness_score: Decimal
    max_lineup_age_seconds: Decimal
    max_injury_age_seconds: Decimal
    max_news_age_seconds: Decimal
    rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...]
    reason_code_counts: tuple[ResearchBaseballEventTeamMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchBaseballEventTeamMemoryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        if self.recommended_next_step != NEXT_STEPS[self.status]:
            raise ValueError("recommended_next_step must match status")
        for field_name in (
            "event_memory_count",
            "pass_count",
            "watch_count",
            "block_count",
            "lineup_fresh_count",
            "injury_fresh_count",
            "news_fresh_count",
            "lineup_missing_count",
            "injury_missing_count",
            "news_missing_count",
            "freshness_pass_count",
            "freshness_watch_count",
            "freshness_block_count",
            "calibration_pass_count",
            "calibration_watch_count",
            "calibration_block_count",
            "max_lineup_age_seconds",
            "max_injury_age_seconds",
            "max_news_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_specialist_memory_score",
            "average_calibration_error",
            "average_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_baseball_event_team_memory_report_payload(self)

    @property
    def digest(self) -> str:
        return research_baseball_event_team_memory_report_digest(self)


def build_research_baseball_event_team_memory_report(
    rows: tuple[ResearchBaseballEventTeamMemoryInputRow, ...],
    *,
    config: ResearchBaseballEventTeamMemoryConfig | None = None,
    generated_at: datetime,
) -> ResearchBaseballEventTeamMemoryReport:
    cfg = config or ResearchBaseballEventTeamMemoryConfig()
    if type(cfg) is not ResearchBaseballEventTeamMemoryConfig:
        raise TypeError("config must be exactly ResearchBaseballEventTeamMemoryConfig")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows, generated_at=generated_at_utc)
    if not input_rows:
        reason_counts = (
            ResearchBaseballEventTeamMemoryReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        return ResearchBaseballEventTeamMemoryReport(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            status=STATUS_BLOCK,
            recommended_next_step=NEXT_STEPS[STATUS_BLOCK],
            event_memory_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            lineup_fresh_count=ZERO,
            injury_fresh_count=ZERO,
            news_fresh_count=ZERO,
            lineup_missing_count=ZERO,
            injury_missing_count=ZERO,
            news_missing_count=ZERO,
            freshness_pass_count=ZERO,
            freshness_watch_count=ZERO,
            freshness_block_count=ZERO,
            calibration_pass_count=ZERO,
            calibration_watch_count=ZERO,
            calibration_block_count=ZERO,
            average_specialist_memory_score=ZERO,
            average_calibration_error=ZERO,
            average_freshness_score=ZERO,
            max_lineup_age_seconds=ZERO,
            max_injury_age_seconds=ZERO,
            max_news_age_seconds=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(
        sorted(
            (_report_row(row, config=cfg, generated_at=generated_at_utc) for row in input_rows),
            key=lambda row: (STATUS_RANK[row.status], row.research_slug, row.specialist_id),
        ),
    )
    reason_counts = _reason_code_counts(report_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    status = _summary_status(report_rows)
    observed_signal_count = _observed_signal_count(report_rows)
    fresh_signal_count = (
        _count_if(report_rows, lambda row: _is_fresh(row.lineup_age_seconds, cfg.fresh_lineup_max_age_seconds))
        + _count_if(report_rows, lambda row: _is_fresh(row.injury_age_seconds, cfg.fresh_injury_max_age_seconds))
        + _count_if(report_rows, lambda row: _is_fresh(row.news_age_seconds, cfg.fresh_news_max_age_seconds))
    )
    return ResearchBaseballEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        recommended_next_step=NEXT_STEPS[status],
        event_memory_count=_count_decimal(report_rows),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        lineup_fresh_count=_count_if(
            report_rows,
            lambda row: _is_fresh(row.lineup_age_seconds, cfg.fresh_lineup_max_age_seconds),
        ),
        injury_fresh_count=_count_if(
            report_rows,
            lambda row: _is_fresh(row.injury_age_seconds, cfg.fresh_injury_max_age_seconds),
        ),
        news_fresh_count=_count_if(
            report_rows,
            lambda row: _is_fresh(row.news_age_seconds, cfg.fresh_news_max_age_seconds),
        ),
        lineup_missing_count=_count_if(report_rows, lambda row: row.lineup_age_seconds is None),
        injury_missing_count=_count_if(report_rows, lambda row: row.injury_age_seconds is None),
        news_missing_count=_count_if(report_rows, lambda row: row.news_age_seconds is None),
        freshness_pass_count=_freshness_status_count(report_rows, STATUS_PASS),
        freshness_watch_count=_freshness_status_count(report_rows, STATUS_WATCH),
        freshness_block_count=_freshness_status_count(report_rows, STATUS_BLOCK),
        calibration_pass_count=_calibration_status_count(report_rows, STATUS_PASS),
        calibration_watch_count=_calibration_status_count(report_rows, STATUS_WATCH),
        calibration_block_count=_calibration_status_count(report_rows, STATUS_BLOCK),
        average_specialist_memory_score=_average(
            row.specialist_memory_score for row in report_rows
        ),
        average_calibration_error=_average(row.calibration_error for row in report_rows),
        average_freshness_score=_ratio(fresh_signal_count, observed_signal_count),
        max_lineup_age_seconds=_max_optional_age(row.lineup_age_seconds for row in report_rows),
        max_injury_age_seconds=_max_optional_age(row.injury_age_seconds for row in report_rows),
        max_news_age_seconds=_max_optional_age(row.news_age_seconds for row in report_rows),
        rows=report_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_baseball_event_team_memory_report_payload(
    report: ResearchBaseballEventTeamMemoryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchBaseballEventTeamMemoryReport:
        raise TypeError("report must be exactly ResearchBaseballEventTeamMemoryReport")
    _require_hard_flags("report", report)
    value = _payload_value(report)
    if type(value) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_raw_surface(value)
    return value


def research_baseball_event_team_memory_report_digest(
    report: ResearchBaseballEventTeamMemoryReport,
) -> str:
    payload = research_baseball_event_team_memory_report_payload(report)
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(text.encode()).hexdigest()


def _report_row(
    row: ResearchBaseballEventTeamMemoryInputRow,
    *,
    config: ResearchBaseballEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchBaseballEventTeamMemoryReportRow:
    lineup_age = _optional_age_seconds(generated_at, row.lineup_observed_at)
    injury_age = _optional_age_seconds(generated_at, row.injury_observed_at)
    news_age = _optional_age_seconds(generated_at, row.news_observed_at)
    specialist_memory_score = _average(
        (row.lineup_memory_score, row.injury_memory_score, row.news_memory_score),
    )
    freshness_status = _freshness_status(
        lineup_age=lineup_age,
        injury_age=injury_age,
        news_age=news_age,
        config=config,
    )
    calibration_status = _calibration_status(row, config)
    status = _row_status(
        freshness_status=freshness_status,
        calibration_status=calibration_status,
        specialist_memory_score=specialist_memory_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        freshness_status=freshness_status,
        calibration_status=calibration_status,
        specialist_memory_score=specialist_memory_score,
        lineup_age=lineup_age,
        injury_age=injury_age,
        news_age=news_age,
        config=config,
    )
    return ResearchBaseballEventTeamMemoryReportRow(
        research_slug=row.research_slug,
        specialist_id=row.specialist_id,
        market_category=row.market_category,
        event_bucket=row.event_bucket,
        status=status,
        freshness_status=freshness_status,
        calibration_status=calibration_status,
        lineup_observed_at=row.lineup_observed_at,
        injury_observed_at=row.injury_observed_at,
        news_observed_at=row.news_observed_at,
        lineup_age_seconds=lineup_age,
        injury_age_seconds=injury_age,
        news_age_seconds=news_age,
        lineup_memory_score=row.lineup_memory_score,
        injury_memory_score=row.injury_memory_score,
        news_memory_score=row.news_memory_score,
        specialist_memory_score=specialist_memory_score,
        calibration_sample_count=row.calibration_sample_count,
        calibration_hit_rate=row.calibration_hit_rate,
        calibration_error=row.calibration_error,
        freshness_score=_freshness_score(
            lineup_age=lineup_age,
            injury_age=injury_age,
            news_age=news_age,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _freshness_status(
    *,
    lineup_age: Decimal | None,
    injury_age: Decimal | None,
    news_age: Decimal | None,
    config: ResearchBaseballEventTeamMemoryConfig,
) -> str:
    if lineup_age is None:
        return STATUS_BLOCK
    if (
        lineup_age <= config.fresh_lineup_max_age_seconds
        and injury_age is not None
        and injury_age <= config.fresh_injury_max_age_seconds
        and news_age is not None
        and news_age <= config.fresh_news_max_age_seconds
    ):
        return STATUS_PASS
    return STATUS_WATCH


def _calibration_status(
    row: ResearchBaseballEventTeamMemoryInputRow,
    config: ResearchBaseballEventTeamMemoryConfig,
) -> str:
    if (
        row.calibration_sample_count >= config.pass_calibration_sample_count
        and row.calibration_hit_rate >= config.pass_calibration_hit_rate
        and row.calibration_error <= config.pass_calibration_error
    ):
        return STATUS_PASS
    if (
        row.calibration_sample_count >= config.watch_calibration_sample_count
        and row.calibration_hit_rate >= config.watch_calibration_hit_rate
        and row.calibration_error <= config.watch_calibration_error
    ):
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_status(
    *,
    freshness_status: str,
    calibration_status: str,
    specialist_memory_score: Decimal,
    config: ResearchBaseballEventTeamMemoryConfig,
) -> str:
    if (
        freshness_status == STATUS_BLOCK
        or calibration_status == STATUS_BLOCK
        or specialist_memory_score < config.watch_memory_score
    ):
        return STATUS_BLOCK
    if (
        freshness_status == STATUS_WATCH
        or calibration_status == STATUS_WATCH
        or specialist_memory_score < config.pass_memory_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    freshness_status: str,
    calibration_status: str,
    specialist_memory_score: Decimal,
    lineup_age: Decimal | None,
    injury_age: Decimal | None,
    news_age: Decimal | None,
    config: ResearchBaseballEventTeamMemoryConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if calibration_status == STATUS_PASS:
        reasons.append(CALIBRATION_PASS_REASON)
    elif calibration_status == STATUS_WATCH:
        reasons.append(CALIBRATION_WATCH_REASON)
    else:
        reasons.append(CALIBRATION_BLOCK_REASON)
    if freshness_status == STATUS_PASS:
        reasons.append(FRESH_REASON)
    if lineup_age is None:
        reasons.append(LINEUP_MISSING_REASON)
    elif lineup_age > config.fresh_lineup_max_age_seconds:
        reasons.append(LINEUP_STALE_REASON)
    if injury_age is None or injury_age > config.fresh_injury_max_age_seconds:
        reasons.append(INJURY_STALE_REASON)
    if news_age is None or news_age > config.fresh_news_max_age_seconds:
        reasons.append(NEWS_STALE_REASON)
    if specialist_memory_score < config.watch_memory_score:
        reasons.append(MEMORY_SCORE_BLOCK_REASON)
    if status == STATUS_PASS:
        reasons.append(PASS_REASON)
    elif status == STATUS_WATCH:
        reasons.append(WATCH_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _freshness_score(
    *,
    lineup_age: Decimal | None,
    injury_age: Decimal | None,
    news_age: Decimal | None,
    config: ResearchBaseballEventTeamMemoryConfig,
) -> Decimal:
    fresh_count = sum(
        (
            _is_fresh(lineup_age, config.fresh_lineup_max_age_seconds),
            _is_fresh(injury_age, config.fresh_injury_max_age_seconds),
            _is_fresh(news_age, config.fresh_news_max_age_seconds),
        ),
    )
    return _ratio(_count_decimal(fresh_count), THREE)


def _is_fresh(value: Decimal | None, max_age: Decimal) -> bool:
    return value is not None and value <= max_age


def _normalize_input_rows(
    rows: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchBaseballEventTeamMemoryInputRow, ...]:
    if not isinstance(rows, tuple):
        raise TypeError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchBaseballEventTeamMemoryInputRow:
            raise ValueError("rows must contain ResearchBaseballEventTeamMemoryInputRow")
        _require_hard_flags("input row", row)
        for field_name in (
            "lineup_observed_at",
            "injury_observed_at",
            "news_observed_at",
        ):
            value = getattr(row, field_name)
            if value is not None and value > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
    return tuple(sorted(rows, key=lambda row: (row.research_slug, row.specialist_id)))


def _reason_code_counts(
    rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...],
) -> tuple[ResearchBaseballEventTeamMemoryReasonCodeCount, ...]:
    row_count = _count_decimal(rows)
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=count,
            event_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _summary_status(rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(row.status == status for row in rows))


def _freshness_status_count(
    rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(row.freshness_status == status for row in rows))


def _calibration_status_count(
    rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(row.calibration_status == status for row in rows))


def _count_if(
    rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...],
    predicate: Any,
) -> Decimal:
    return _count_decimal(sum(predicate(row) for row in rows))


def _observed_signal_count(
    rows: tuple[ResearchBaseballEventTeamMemoryReportRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            value is not None
            for row in rows
            for value in (
                row.lineup_age_seconds,
                row.injury_age_seconds,
                row.news_age_seconds,
            )
        ),
    )


def _max_optional_age(values: Any) -> Decimal:
    decimal_values = tuple(value for value in values if value is not None)
    return max(decimal_values, default=ZERO)


def _average(values: Any) -> Decimal:
    decimals = tuple(values)
    if not decimals:
        return ZERO
    return _ratio(sum(decimals, ZERO), _count_decimal(len(decimals)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count_decimal(value: object) -> Decimal:
    if isinstance(value, tuple):
        return _quantize(Decimal(len(value)))
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _optional_age_seconds(later: datetime, earlier: datetime | None) -> Decimal | None:
    if earlier is None:
        return None
    return _age_seconds(later, earlier)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _reject_raw_surface(value: object) -> None:
    raw_keys = frozenset(
        (
            "raw_team",
            "raw_game",
            "raw_source",
            "home_team",
            "away_team",
            "team_name",
            "game_slug",
            "source_url",
            "source_reference",
        ),
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in raw_keys:
                raise ValueError("payload contains raw public surface")
            _reject_raw_surface(item)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_surface(item)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchBaseballEventTeamMemoryReportRow, ...]:
    if not isinstance(rows, tuple):
        raise TypeError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchBaseballEventTeamMemoryReportRow:
            raise ValueError("rows must contain ResearchBaseballEventTeamMemoryReportRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchBaseballEventTeamMemoryReasonCodeCount, ...]:
    if not isinstance(values, tuple):
        raise TypeError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchBaseballEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchBaseballEventTeamMemoryReasonCodeCount",
            )
        _require_hard_flags("reason count", value)
    return values


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    unique_values = frozenset(values)
    if len(unique_values) != len(values):
        raise ValueError("reason_codes contains duplicate reason_code values")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in unique_values)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value != value.strip() or any(char.isspace() for char in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason_code")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return decimal_value


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be a whole second")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must keep {flag_name}=True")


def _validate_row(row: ResearchBaseballEventTeamMemoryReportRow) -> None:
    if row.status != _row_status(
        freshness_status=row.freshness_status,
        calibration_status=row.calibration_status,
        specialist_memory_score=row.specialist_memory_score,
        config=ResearchBaseballEventTeamMemoryConfig(),
    ):
        raise ValueError("status must match row inputs")
    if row.reason_codes != _row_reason_codes(
        status=row.status,
        freshness_status=row.freshness_status,
        calibration_status=row.calibration_status,
        specialist_memory_score=row.specialist_memory_score,
        lineup_age=row.lineup_age_seconds,
        injury_age=row.injury_age_seconds,
        news_age=row.news_age_seconds,
        config=ResearchBaseballEventTeamMemoryConfig(),
    ):
        raise ValueError("reason_codes must match row inputs")


def _validate_report(report: ResearchBaseballEventTeamMemoryReport) -> None:
    if report.event_memory_count != _count_decimal(report.rows):
        raise ValueError("event_memory_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")


__all__ = (
    "DEFAULT_RESEARCH_BASEBALL_EVENT_TEAM_MEMORY_CONFIG_VERSION",
    "ResearchBaseballEventTeamMemoryConfig",
    "ResearchBaseballEventTeamMemoryInputRow",
    "ResearchBaseballEventTeamMemoryReasonCodeCount",
    "ResearchBaseballEventTeamMemoryReport",
    "ResearchBaseballEventTeamMemoryReportRow",
    "build_research_baseball_event_team_memory_report",
    "research_baseball_event_team_memory_report_digest",
    "research_baseball_event_team_memory_report_payload",
)
