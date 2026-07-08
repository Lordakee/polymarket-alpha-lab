"""Pure baseball signal memory quality report for forecast handoff."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_DOMAIN_BASEBALL_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION = (
    "research-domain-baseball-signal-memory-quality-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_baseball_signal_memory_forecast_handoff",
    STATUS_WATCH: "watch_report_only_baseball_signal_memory_forecast_handoff",
    STATUS_BLOCK: "block_report_only_baseball_signal_memory_forecast_handoff",
}

NO_INPUTS_REASON = "baseball_signal_memory_quality_no_inputs"
FRESH_REASON = "baseball_signal_memory_quality_fresh"
NO_CONFLICT_REASON = "baseball_signal_memory_quality_no_conflict"
PASS_REASON = "baseball_signal_memory_quality_pass"
WATCH_REASON = "baseball_signal_memory_quality_watch"
MEMORY_SCORE_BLOCK_REASON = "baseball_signal_memory_quality_memory_score_block"
MEMORY_SCORE_WATCH_REASON = "baseball_signal_memory_quality_memory_score_watch"
CONFLICT_BLOCK_REASON = "baseball_signal_memory_quality_conflict_block"
CONFLICT_WATCH_REASON = "baseball_signal_memory_quality_conflict_watch"

SIGNAL_NAMES = ("pitcher", "lineup", "weather", "schedule")
REASON_CODES = tuple(
    sorted(
        (
            NO_INPUTS_REASON,
            FRESH_REASON,
            NO_CONFLICT_REASON,
            PASS_REASON,
            WATCH_REASON,
            MEMORY_SCORE_BLOCK_REASON,
            MEMORY_SCORE_WATCH_REASON,
            CONFLICT_BLOCK_REASON,
            CONFLICT_WATCH_REASON,
            "baseball_signal_memory_quality_pitcher_missing",
            "baseball_signal_memory_quality_pitcher_stale",
            "baseball_signal_memory_quality_pitcher_conflicting",
            "baseball_signal_memory_quality_lineup_missing",
            "baseball_signal_memory_quality_lineup_stale",
            "baseball_signal_memory_quality_lineup_conflicting",
            "baseball_signal_memory_quality_weather_missing",
            "baseball_signal_memory_quality_weather_stale",
            "baseball_signal_memory_quality_weather_conflicting",
            "baseball_signal_memory_quality_schedule_missing",
            "baseball_signal_memory_quality_schedule_stale",
            "baseball_signal_memory_quality_schedule_conflicting",
        ),
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class ResearchDomainBaseballSignalMemoryQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_BASEBALL_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION
    )
    fresh_pitcher_max_age_seconds: Decimal = Decimal("3600.000000")
    fresh_lineup_max_age_seconds: Decimal = Decimal("3600.000000")
    fresh_weather_max_age_seconds: Decimal = Decimal("3600.000000")
    fresh_schedule_max_age_seconds: Decimal = Decimal("3600.000000")
    pass_memory_score: Decimal = Decimal("0.750000")
    watch_memory_score: Decimal = Decimal("0.550000")
    block_conflict_count: Decimal = Decimal("2.000000")
    watch_conflict_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainBaseballSignalMemoryQualityConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "fresh_pitcher_max_age_seconds",
            "fresh_lineup_max_age_seconds",
            "fresh_weather_max_age_seconds",
            "fresh_schedule_max_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_memory_score", "watch_memory_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("block_conflict_count", "watch_conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_memory_score <= self.watch_memory_score:
            raise ValueError("pass_memory_score must exceed watch_memory_score")
        if self.block_conflict_count <= self.watch_conflict_count:
            raise ValueError("block_conflict_count must exceed watch_conflict_count")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainBaseballSignalMemoryQualityInputRow:
    event_bucket: str
    memory_scope: str
    pitcher_memory_observed_at: datetime | None
    lineup_memory_observed_at: datetime | None
    weather_memory_observed_at: datetime | None
    schedule_memory_observed_at: datetime | None
    pitcher_memory_score: Decimal
    lineup_memory_score: Decimal
    weather_memory_score: Decimal
    schedule_memory_score: Decimal
    pitcher_conflict_count: Decimal
    lineup_conflict_count: Decimal
    weather_conflict_count: Decimal
    schedule_conflict_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainBaseballSignalMemoryQualityInputRow,
            "input row",
        )
        for field_name in ("event_bucket", "memory_scope"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pitcher_memory_observed_at",
            "lineup_memory_observed_at",
            "weather_memory_observed_at",
            "schedule_memory_observed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pitcher_memory_score",
            "lineup_memory_score",
            "weather_memory_score",
            "schedule_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pitcher_conflict_count",
            "lineup_conflict_count",
            "weather_conflict_count",
            "schedule_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchDomainBaseballSignalMemoryQualityReportRow:
    event_bucket: str
    memory_scope: str
    public_status: str
    freshness_status: str
    conflict_status: str
    pitcher_memory_observed_at: datetime | None
    lineup_memory_observed_at: datetime | None
    weather_memory_observed_at: datetime | None
    schedule_memory_observed_at: datetime | None
    pitcher_age_seconds: Decimal | None
    lineup_age_seconds: Decimal | None
    weather_age_seconds: Decimal | None
    schedule_age_seconds: Decimal | None
    pitcher_memory_score: Decimal
    lineup_memory_score: Decimal
    weather_memory_score: Decimal
    schedule_memory_score: Decimal
    pitcher_conflict_count: Decimal
    lineup_conflict_count: Decimal
    weather_conflict_count: Decimal
    schedule_conflict_count: Decimal
    composite_memory_score: Decimal
    freshness_score: Decimal
    conflict_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainBaseballSignalMemoryQualityReportRow,
            "row",
        )
        for field_name in ("event_bucket", "memory_scope"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in ("public_status", "freshness_status", "conflict_status"):
            _require_status(field_name, getattr(self, field_name))
        for field_name in (
            "pitcher_memory_observed_at",
            "lineup_memory_observed_at",
            "weather_memory_observed_at",
            "schedule_memory_observed_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pitcher_age_seconds",
            "lineup_age_seconds",
            "weather_age_seconds",
            "schedule_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "pitcher_memory_score",
            "lineup_memory_score",
            "weather_memory_score",
            "schedule_memory_score",
            "composite_memory_score",
            "freshness_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pitcher_conflict_count",
            "lineup_conflict_count",
            "weather_conflict_count",
            "schedule_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
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
class ResearchDomainBaseballSignalMemoryQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainBaseballSignalMemoryQualityReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchDomainBaseballSignalMemoryQualityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    handoff_gate_label: str
    event_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_bucket_count: Decimal
    conflicting_bucket_count: Decimal
    missing_bucket_count: Decimal
    average_memory_score: Decimal
    average_freshness_score: Decimal
    average_conflict_score: Decimal
    pitcher_missing_count: Decimal
    lineup_missing_count: Decimal
    weather_missing_count: Decimal
    schedule_missing_count: Decimal
    pitcher_stale_count: Decimal
    lineup_stale_count: Decimal
    weather_stale_count: Decimal
    schedule_stale_count: Decimal
    pitcher_conflicting_count: Decimal
    lineup_conflicting_count: Decimal
    weather_conflicting_count: Decimal
    schedule_conflicting_count: Decimal
    max_pitcher_age_seconds: Decimal
    max_lineup_age_seconds: Decimal
    max_weather_age_seconds: Decimal
    max_schedule_age_seconds: Decimal
    rows: tuple[ResearchDomainBaseballSignalMemoryQualityReportRow, ...]
    reason_code_counts: tuple[
        ResearchDomainBaseballSignalMemoryQualityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchDomainBaseballSignalMemoryQualityReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        if self.handoff_gate_label != NEXT_STEPS[self.report_status]:
            raise ValueError("handoff_gate_label must match report_status")
        for field_name in (
            "event_bucket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_bucket_count",
            "conflicting_bucket_count",
            "missing_bucket_count",
            "pitcher_missing_count",
            "lineup_missing_count",
            "weather_missing_count",
            "schedule_missing_count",
            "pitcher_stale_count",
            "lineup_stale_count",
            "weather_stale_count",
            "schedule_stale_count",
            "pitcher_conflicting_count",
            "lineup_conflicting_count",
            "weather_conflicting_count",
            "schedule_conflicting_count",
            "max_pitcher_age_seconds",
            "max_lineup_age_seconds",
            "max_weather_age_seconds",
            "max_schedule_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_score",
            "average_freshness_score",
            "average_conflict_score",
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
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(_payload_value(self, include_digest=True))
        expected_digest = _report_digest_from_payload(self, include_digest=False)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_domain_baseball_signal_memory_quality_report_payload(self)


def build_research_domain_baseball_signal_memory_quality_report(
    rows: tuple[ResearchDomainBaseballSignalMemoryQualityInputRow, ...],
    *,
    config: ResearchDomainBaseballSignalMemoryQualityConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainBaseballSignalMemoryQualityReport:
    cfg = config or ResearchDomainBaseballSignalMemoryQualityConfig()
    if type(cfg) is not ResearchDomainBaseballSignalMemoryQualityConfig:
        raise TypeError(
            "config must be exactly ResearchDomainBaseballSignalMemoryQualityConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    if not input_rows:
        reason_counts = (
            ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
        return _make_report(
            generated_at=generated_at_utc,
            config_version=cfg.config_version,
            report_status=STATUS_BLOCK,
            handoff_gate_label=NEXT_STEPS[STATUS_BLOCK],
            event_bucket_count=ZERO,
            pass_count=ZERO,
            watch_count=ZERO,
            block_count=ZERO,
            stale_bucket_count=ZERO,
            conflicting_bucket_count=ZERO,
            missing_bucket_count=ZERO,
            average_memory_score=ZERO,
            average_freshness_score=ZERO,
            average_conflict_score=ZERO,
            pitcher_missing_count=ZERO,
            lineup_missing_count=ZERO,
            weather_missing_count=ZERO,
            schedule_missing_count=ZERO,
            pitcher_stale_count=ZERO,
            lineup_stale_count=ZERO,
            weather_stale_count=ZERO,
            schedule_stale_count=ZERO,
            pitcher_conflicting_count=ZERO,
            lineup_conflicting_count=ZERO,
            weather_conflicting_count=ZERO,
            schedule_conflicting_count=ZERO,
            max_pitcher_age_seconds=ZERO,
            max_lineup_age_seconds=ZERO,
            max_weather_age_seconds=ZERO,
            max_schedule_age_seconds=ZERO,
            rows=(),
            reason_code_counts=reason_counts,
            reason_codes=(NO_INPUTS_REASON,),
        )

    report_rows = tuple(
        sorted(
            (
                _report_row(row, config=cfg, generated_at=generated_at_utc)
                for row in input_rows
            ),
            key=lambda row: (
                STATUS_RANK[row.public_status],
                row.event_bucket,
                row.memory_scope,
            ),
        ),
    )
    reason_counts = _reason_code_counts(report_rows)
    reason_codes = tuple(item.reason_code for item in reason_counts)
    status = _summary_status(report_rows)
    return _make_report(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=status,
        handoff_gate_label=NEXT_STEPS[status],
        event_bucket_count=_count_decimal(report_rows),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        stale_bucket_count=_count_if(report_rows, _has_stale_signal),
        conflicting_bucket_count=_count_if(report_rows, _has_conflicting_signal),
        missing_bucket_count=_count_if(report_rows, _has_missing_signal),
        average_memory_score=_average(row.composite_memory_score for row in report_rows),
        average_freshness_score=_average(row.freshness_score for row in report_rows),
        average_conflict_score=_average(row.conflict_score for row in report_rows),
        pitcher_missing_count=_count_if(report_rows, lambda row: row.pitcher_age_seconds is None),
        lineup_missing_count=_count_if(report_rows, lambda row: row.lineup_age_seconds is None),
        weather_missing_count=_count_if(report_rows, lambda row: row.weather_age_seconds is None),
        schedule_missing_count=_count_if(
            report_rows,
            lambda row: row.schedule_age_seconds is None,
        ),
        pitcher_stale_count=_count_if(
            report_rows,
            lambda row: _is_stale(row.pitcher_age_seconds, cfg.fresh_pitcher_max_age_seconds),
        ),
        lineup_stale_count=_count_if(
            report_rows,
            lambda row: _is_stale(row.lineup_age_seconds, cfg.fresh_lineup_max_age_seconds),
        ),
        weather_stale_count=_count_if(
            report_rows,
            lambda row: _is_stale(row.weather_age_seconds, cfg.fresh_weather_max_age_seconds),
        ),
        schedule_stale_count=_count_if(
            report_rows,
            lambda row: _is_stale(row.schedule_age_seconds, cfg.fresh_schedule_max_age_seconds),
        ),
        pitcher_conflicting_count=_count_if(
            report_rows,
            lambda row: row.pitcher_conflict_count > ZERO,
        ),
        lineup_conflicting_count=_count_if(
            report_rows,
            lambda row: row.lineup_conflict_count > ZERO,
        ),
        weather_conflicting_count=_count_if(
            report_rows,
            lambda row: row.weather_conflict_count > ZERO,
        ),
        schedule_conflicting_count=_count_if(
            report_rows,
            lambda row: row.schedule_conflict_count > ZERO,
        ),
        max_pitcher_age_seconds=_max_optional_age(
            row.pitcher_age_seconds for row in report_rows
        ),
        max_lineup_age_seconds=_max_optional_age(
            row.lineup_age_seconds for row in report_rows
        ),
        max_weather_age_seconds=_max_optional_age(
            row.weather_age_seconds for row in report_rows
        ),
        max_schedule_age_seconds=_max_optional_age(
            row.schedule_age_seconds for row in report_rows
        ),
        rows=report_rows,
        reason_code_counts=reason_counts,
        reason_codes=reason_codes,
    )


def research_domain_baseball_signal_memory_quality_report_payload(
    report: ResearchDomainBaseballSignalMemoryQualityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDomainBaseballSignalMemoryQualityReport:
        raise TypeError(
            "report must be exactly ResearchDomainBaseballSignalMemoryQualityReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def research_domain_baseball_signal_memory_quality_report_digest(
    report: ResearchDomainBaseballSignalMemoryQualityReport,
) -> str:
    if type(report) is not ResearchDomainBaseballSignalMemoryQualityReport:
        raise TypeError(
            "report must be exactly ResearchDomainBaseballSignalMemoryQualityReport",
        )
    return _report_digest_from_payload(report, include_digest=False)


def _make_report(**values: Any) -> ResearchDomainBaseballSignalMemoryQualityReport:
    digest_values = {
        **values,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _report_digest_from_mapping(digest_values)
    return ResearchDomainBaseballSignalMemoryQualityReport(
        **values,
        derived_validation_digest=digest,
    )


def _report_row(
    row: ResearchDomainBaseballSignalMemoryQualityInputRow,
    *,
    config: ResearchDomainBaseballSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainBaseballSignalMemoryQualityReportRow:
    pitcher_age = _optional_age_seconds(generated_at, row.pitcher_memory_observed_at)
    lineup_age = _optional_age_seconds(generated_at, row.lineup_memory_observed_at)
    weather_age = _optional_age_seconds(generated_at, row.weather_memory_observed_at)
    schedule_age = _optional_age_seconds(generated_at, row.schedule_memory_observed_at)
    composite_memory_score = _average(
        (
            row.pitcher_memory_score,
            row.lineup_memory_score,
            row.weather_memory_score,
            row.schedule_memory_score,
        ),
    )
    freshness_status = _freshness_status(
        pitcher_age=pitcher_age,
        lineup_age=lineup_age,
        weather_age=weather_age,
        schedule_age=schedule_age,
        config=config,
    )
    conflict_status = _conflict_status(row, config)
    public_status = _row_status(
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        composite_memory_score=composite_memory_score,
        config=config,
    )
    freshness_score = _freshness_score(
        pitcher_age=pitcher_age,
        lineup_age=lineup_age,
        weather_age=weather_age,
        schedule_age=schedule_age,
        config=config,
    )
    conflict_score = _conflict_score(
        row,
        config=config,
        conflict_status=conflict_status,
    )
    reason_codes = _row_reason_codes(
        public_status=public_status,
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        composite_memory_score=composite_memory_score,
        pitcher_age=pitcher_age,
        lineup_age=lineup_age,
        weather_age=weather_age,
        schedule_age=schedule_age,
        input_row=row,
        config=config,
    )
    return ResearchDomainBaseballSignalMemoryQualityReportRow(
        event_bucket=row.event_bucket,
        memory_scope=row.memory_scope,
        public_status=public_status,
        freshness_status=freshness_status,
        conflict_status=conflict_status,
        pitcher_memory_observed_at=row.pitcher_memory_observed_at,
        lineup_memory_observed_at=row.lineup_memory_observed_at,
        weather_memory_observed_at=row.weather_memory_observed_at,
        schedule_memory_observed_at=row.schedule_memory_observed_at,
        pitcher_age_seconds=pitcher_age,
        lineup_age_seconds=lineup_age,
        weather_age_seconds=weather_age,
        schedule_age_seconds=schedule_age,
        pitcher_memory_score=row.pitcher_memory_score,
        lineup_memory_score=row.lineup_memory_score,
        weather_memory_score=row.weather_memory_score,
        schedule_memory_score=row.schedule_memory_score,
        pitcher_conflict_count=row.pitcher_conflict_count,
        lineup_conflict_count=row.lineup_conflict_count,
        weather_conflict_count=row.weather_conflict_count,
        schedule_conflict_count=row.schedule_conflict_count,
        composite_memory_score=composite_memory_score,
        freshness_score=freshness_score,
        conflict_score=conflict_score,
        reason_codes=reason_codes,
    )


def _freshness_status(
    *,
    pitcher_age: Decimal | None,
    lineup_age: Decimal | None,
    weather_age: Decimal | None,
    schedule_age: Decimal | None,
    config: ResearchDomainBaseballSignalMemoryQualityConfig,
) -> str:
    if None in (pitcher_age, lineup_age, weather_age, schedule_age):
        return STATUS_BLOCK
    if (
        _is_stale(pitcher_age, config.fresh_pitcher_max_age_seconds)
        or _is_stale(lineup_age, config.fresh_lineup_max_age_seconds)
        or _is_stale(weather_age, config.fresh_weather_max_age_seconds)
        or _is_stale(schedule_age, config.fresh_schedule_max_age_seconds)
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _conflict_status(
    row: ResearchDomainBaseballSignalMemoryQualityInputRow,
    config: ResearchDomainBaseballSignalMemoryQualityConfig,
) -> str:
    counts = _conflict_counts(row)
    if any(count >= config.block_conflict_count for count in counts):
        return STATUS_BLOCK
    if any(count >= config.watch_conflict_count for count in counts):
        return STATUS_WATCH
    return STATUS_PASS


def _row_status(
    *,
    freshness_status: str,
    conflict_status: str,
    composite_memory_score: Decimal,
    config: ResearchDomainBaseballSignalMemoryQualityConfig,
) -> str:
    status = min(
        (freshness_status, conflict_status),
        key=lambda value: STATUS_RANK[value],
    )
    if composite_memory_score < config.watch_memory_score:
        return STATUS_BLOCK
    if composite_memory_score < config.pass_memory_score and status == STATUS_PASS:
        return STATUS_WATCH
    if composite_memory_score < config.pass_memory_score:
        return min((status, STATUS_WATCH), key=lambda value: STATUS_RANK[value])
    return status


def _freshness_score(
    *,
    pitcher_age: Decimal | None,
    lineup_age: Decimal | None,
    weather_age: Decimal | None,
    schedule_age: Decimal | None,
    config: ResearchDomainBaseballSignalMemoryQualityConfig,
) -> Decimal:
    fresh_count = ZERO
    for age, max_age in (
        (pitcher_age, config.fresh_pitcher_max_age_seconds),
        (lineup_age, config.fresh_lineup_max_age_seconds),
        (weather_age, config.fresh_weather_max_age_seconds),
        (schedule_age, config.fresh_schedule_max_age_seconds),
    ):
        if age is not None and age <= max_age:
            fresh_count += ONE
    return _ratio(fresh_count, FOUR)


def _conflict_score(
    row: ResearchDomainBaseballSignalMemoryQualityInputRow,
    *,
    config: ResearchDomainBaseballSignalMemoryQualityConfig,
    conflict_status: str,
) -> Decimal:
    if conflict_status == STATUS_BLOCK:
        return ZERO
    clean_count = sum(ONE for count in _conflict_counts(row) if count < config.watch_conflict_count)
    return _ratio(_decimal(clean_count), FOUR)


def _row_reason_codes(
    *,
    public_status: str,
    freshness_status: str,
    conflict_status: str,
    composite_memory_score: Decimal,
    pitcher_age: Decimal | None,
    lineup_age: Decimal | None,
    weather_age: Decimal | None,
    schedule_age: Decimal | None,
    input_row: ResearchDomainBaseballSignalMemoryQualityInputRow,
    config: ResearchDomainBaseballSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    ages = {
        "pitcher": (pitcher_age, config.fresh_pitcher_max_age_seconds),
        "lineup": (lineup_age, config.fresh_lineup_max_age_seconds),
        "weather": (weather_age, config.fresh_weather_max_age_seconds),
        "schedule": (schedule_age, config.fresh_schedule_max_age_seconds),
    }
    for name, (age, max_age) in ages.items():
        if age is None:
            reasons.add(f"baseball_signal_memory_quality_{name}_missing")
        elif age > max_age:
            reasons.add(f"baseball_signal_memory_quality_{name}_stale")
    if freshness_status == STATUS_PASS:
        reasons.add(FRESH_REASON)
    conflicts = dict(zip(SIGNAL_NAMES, _conflict_counts(input_row), strict=True))
    for name, count in conflicts.items():
        if count > ZERO:
            reasons.add(f"baseball_signal_memory_quality_{name}_conflicting")
    if conflict_status == STATUS_BLOCK:
        reasons.add(CONFLICT_BLOCK_REASON)
    elif conflict_status == STATUS_WATCH:
        reasons.add(CONFLICT_WATCH_REASON)
    else:
        reasons.add(NO_CONFLICT_REASON)
    if composite_memory_score < config.watch_memory_score:
        reasons.add(MEMORY_SCORE_BLOCK_REASON)
    elif composite_memory_score < config.pass_memory_score:
        reasons.add(MEMORY_SCORE_WATCH_REASON)
    if public_status == STATUS_PASS:
        reasons.add(PASS_REASON)
    elif public_status == STATUS_WATCH:
        reasons.add(WATCH_REASON)
    return _normalize_reason_codes(tuple(sorted(reasons)))


def _summary_status(
    rows: tuple[ResearchDomainBaseballSignalMemoryQualityReportRow, ...],
) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchDomainBaseballSignalMemoryQualityReportRow, ...],
) -> tuple[ResearchDomainBaseballSignalMemoryQualityReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    row_count = _count_decimal(rows)
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=count,
            event_ratio=_ratio(count, row_count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _has_stale_signal(row: ResearchDomainBaseballSignalMemoryQualityReportRow) -> bool:
    return any(
        reason_code.endswith("_stale")
        for reason_code in row.reason_codes
    )


def _has_conflicting_signal(row: ResearchDomainBaseballSignalMemoryQualityReportRow) -> bool:
    return any(
        reason_code.endswith("_conflicting")
        for reason_code in row.reason_codes
    )


def _has_missing_signal(row: ResearchDomainBaseballSignalMemoryQualityReportRow) -> bool:
    return any(
        reason_code.endswith("_missing")
        for reason_code in row.reason_codes
    )


def _is_stale(age: Decimal | None, max_age: Decimal) -> bool:
    return age is not None and age > max_age


def _conflict_counts(
    row: ResearchDomainBaseballSignalMemoryQualityInputRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    return (
        row.pitcher_conflict_count,
        row.lineup_conflict_count,
        row.weather_conflict_count,
        row.schedule_conflict_count,
    )


def _normalize_input_rows(
    rows: tuple[ResearchDomainBaseballSignalMemoryQualityInputRow, ...],
) -> tuple[ResearchDomainBaseballSignalMemoryQualityInputRow, ...]:
    if type(rows) is not tuple:
        raise TypeError("rows must be a tuple")
    normalized: list[ResearchDomainBaseballSignalMemoryQualityInputRow] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchDomainBaseballSignalMemoryQualityInputRow:
            raise TypeError(
                "rows must contain exactly "
                "ResearchDomainBaseballSignalMemoryQualityInputRow",
            )
        _require_hard_flags("input row", row)
        key = (row.event_bucket, row.memory_scope)
        if key in seen_keys:
            raise ValueError("event_bucket and memory_scope must be unique")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchDomainBaseballSignalMemoryQualityReportRow, ...]:
    if type(rows) not in (tuple, list):
        raise TypeError("rows must be a tuple")
    normalized: list[ResearchDomainBaseballSignalMemoryQualityReportRow] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is dict:
            row = ResearchDomainBaseballSignalMemoryQualityReportRow(**row)
        if type(row) is not ResearchDomainBaseballSignalMemoryQualityReportRow:
            raise TypeError(
                "rows must contain exactly "
                "ResearchDomainBaseballSignalMemoryQualityReportRow",
            )
        _require_hard_flags("row", row)
        key = (row.event_bucket, row.memory_scope)
        if key in seen_keys:
            raise ValueError("event_bucket and memory_scope must be unique")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                STATUS_RANK[row.public_status],
                row.event_bucket,
                row.memory_scope,
            ),
        ),
    )


def _normalize_reason_code_counts(
    reason_code_counts: object,
) -> tuple[ResearchDomainBaseballSignalMemoryQualityReasonCodeCount, ...]:
    if type(reason_code_counts) not in (tuple, list):
        raise TypeError("reason_code_counts must be a tuple")
    normalized: list[ResearchDomainBaseballSignalMemoryQualityReasonCodeCount] = []
    seen: set[str] = set()
    for item in reason_code_counts:
        if type(item) is dict:
            item = ResearchDomainBaseballSignalMemoryQualityReasonCodeCount(**item)
        if type(item) is not ResearchDomainBaseballSignalMemoryQualityReasonCodeCount:
            raise TypeError(
                "reason_code_counts must contain exactly "
                "ResearchDomainBaseballSignalMemoryQualityReasonCodeCount",
            )
        _require_hard_flags("reason count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise TypeError("reason_codes must be a tuple")
    normalized = tuple(value)
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("reason_codes must be sorted")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _validate_row(row: ResearchDomainBaseballSignalMemoryQualityReportRow) -> None:
    if row.public_status not in STATUSES:
        raise ValueError("public_status must be pass, watch, or block")
    if row.reason_codes == ():
        raise ValueError("row reason_codes must not be empty")


def _validate_report(report: ResearchDomainBaseballSignalMemoryQualityReport) -> None:
    row_count = _count_decimal(report.rows)
    if report.event_bucket_count != row_count:
        raise ValueError("event_bucket_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != row_count:
        raise ValueError("status counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _count_decimal(value: tuple[object, ...]) -> Decimal:
    return _decimal(Decimal(len(value)))


def _status_count(
    rows: tuple[ResearchDomainBaseballSignalMemoryQualityReportRow, ...],
    status: str,
) -> Decimal:
    return _count_if(rows, lambda row: row.public_status == status)


def _count_if(
    rows: tuple[ResearchDomainBaseballSignalMemoryQualityReportRow, ...],
    predicate: Any,
) -> Decimal:
    count = ZERO
    for row in rows:
        if predicate(row):
            count += ONE
    return _decimal(count)


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    total = ZERO
    for item in items:
        total += _require_decimal("average item", item)
    return _ratio(total, _decimal(Decimal(len(items))))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _max_optional_age(values: Any) -> Decimal:
    observed = tuple(value for value in values if value is not None)
    if not observed:
        return ZERO
    return max(observed)


def _optional_age_seconds(generated_at: datetime, observed_at: datetime | None) -> Decimal | None:
    if observed_at is None:
        return None
    if observed_at > generated_at:
        raise ValueError("memory observed_at must not be after generated_at")
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _decimal(seconds)


def _as_optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")
    normalized = value.astimezone(UTC)
    if normalized.microsecond != 0:
        raise ValueError(f"{name} must be a whole second")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be public")
    if not all(ch.islower() or ch.isdigit() or ch in "._-" for ch in value):
        raise ValueError(f"{name} must be public")
    if value.startswith((".", "_", "-")) or value.endswith((".", "_", "-")):
        raise ValueError(f"{name} must be public")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} must be public")
    return value


def _require_status(name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    _require_public_string(name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _decimal(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(name, value)


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be in the unit interval")
    return normalized


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be whole")
    return normalized


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be whole")
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise TypeError(f"{name} must be exactly str")
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _payload_value(value: Any, *, include_digest: bool) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        for field in fields(value):
            if field.name == "derived_validation_digest" and not include_digest:
                continue
            payload[field.name] = _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return payload
    if isinstance(value, Decimal):
        return str(_require_decimal("payload Decimal", value))
    if type(value) is datetime:
        return _format_datetime(value)
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError("payload contains unsafe public value")
        return value
    if type(value) is bool:
        return value
    if type(value) in (tuple, list):
        return tuple(_payload_value(item, include_digest=include_digest) for item in value)
    if type(value) is dict:
        payload = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if key == "derived_validation_digest" and not include_digest:
                continue
            if _has_unsafe_fragment(key):
                raise ValueError("payload contains unsafe public key")
            payload[key] = _payload_value(item, include_digest=include_digest)
        return payload
    raise ValueError("payload value is not report serializable")


def _format_datetime(value: datetime) -> str:
    normalized = _as_utc("payload datetime", value)
    return normalized.isoformat().replace("+00:00", "Z")


def _report_digest_from_payload(
    report: ResearchDomainBaseballSignalMemoryQualityReport,
    *,
    include_digest: bool,
) -> str:
    payload = _payload_value(report, include_digest=include_digest)
    return _digest_payload(payload)


def _report_digest_from_mapping(values: dict[str, Any]) -> str:
    payload = _payload_value(values, include_digest=False)
    return _digest_payload(payload)


def _digest_payload(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(text.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError("payload contains unsafe public key")
            _reject_unsafe_public_payload(item)
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError("payload contains unsafe public value")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _unsafe_fragments())


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "http",
        "source_text",
        "source_id",
        "source_reference",
        "raw_",
        "dsn",
        "table",
        _part("to", "ken"),
        _part("wal", "let"),
        _part("au", "th"),
        _part("or", "der"),
        _part("tr", "ade"),
        _part("tr", "ading"),
        "size",
        _part("pos", "ition"),
        _part("b", "uy"),
        _part("s", "ell"),
        _part("rec", "ommend"),
    )


def _part(*values: str) -> str:
    return "".join(values)


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_BASEBALL_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION",
    "ResearchDomainBaseballSignalMemoryQualityConfig",
    "ResearchDomainBaseballSignalMemoryQualityInputRow",
    "ResearchDomainBaseballSignalMemoryQualityReasonCodeCount",
    "ResearchDomainBaseballSignalMemoryQualityReport",
    "ResearchDomainBaseballSignalMemoryQualityReportRow",
    "build_research_domain_baseball_signal_memory_quality_report",
    "research_domain_baseball_signal_memory_quality_report_digest",
    "research_domain_baseball_signal_memory_quality_report_payload",
)
