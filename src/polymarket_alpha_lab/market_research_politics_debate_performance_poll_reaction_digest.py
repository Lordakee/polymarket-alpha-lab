"""Pure politics debate performance poll reaction digest reducer for market research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLITICS_DEBATE_PERFORMANCE_POLL_REACTION_DIGEST_CONFIG_VERSION",
    "MarketResearchPoliticsDebatePerformancePollReactionDigestConfig",
    "MarketResearchPoliticsDebatePerformancePollReactionDigestInput",
    "MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount",
    "MarketResearchPoliticsDebatePerformancePollReactionDigestReport",
    "MarketResearchPoliticsDebatePerformancePollReactionDigestRow",
    "build_market_research_politics_debate_performance_poll_reaction_digest_report",
    "market_research_politics_debate_performance_poll_reaction_digest_payload",
)


DEFAULT_MARKET_RESEARCH_POLITICS_DEBATE_PERFORMANCE_POLL_REACTION_DIGEST_CONFIG_VERSION = (
    "market-research-politics-debate-performance-poll-reaction-digest-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
SAMPLE_SHORTFALL_WEIGHT = Decimal("0.030000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = (
    "market_research_politics_debate_performance_poll_reaction_digest_no_inputs"
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class MarketResearchPoliticsDebatePerformancePollReactionDigestConfig(
    _FinalPublicDataclass,
):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_POLITICS_DEBATE_PERFORMANCE_POLL_REACTION_DIGEST_CONFIG_VERSION
    )
    performance_score_watch_floor: Decimal = Decimal("0.480000")
    performance_score_blocked_floor: Decimal = Decimal("0.400000")
    poll_reaction_drop_watch: Decimal = Decimal("0.010000")
    poll_reaction_drop_blocked: Decimal = Decimal("0.030000")
    favorability_drop_watch: Decimal = Decimal("0.010000")
    favorability_drop_blocked: Decimal = Decimal("0.030000")
    poll_sample_size_floor: Decimal = Decimal("600.000000")
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "performance_score_watch_floor",
            "performance_score_blocked_floor",
            "poll_reaction_drop_watch",
            "poll_reaction_drop_blocked",
            "favorability_drop_watch",
            "favorability_drop_blocked",
            "poll_sample_size_floor",
            "stale_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "performance_score_blocked_floor",
            self.performance_score_blocked_floor,
            self.performance_score_watch_floor,
        )
        _require_at_most(
            "poll_reaction_drop_watch",
            self.poll_reaction_drop_watch,
            self.poll_reaction_drop_blocked,
        )
        _require_at_most(
            "favorability_drop_watch",
            self.favorability_drop_watch,
            self.favorability_drop_blocked,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPoliticsDebatePerformancePollReactionDigestInput(
    _FinalPublicDataclass,
):
    candidate_id: str
    debate_id: str
    poll_source: str
    debate_performance_score: Decimal
    post_debate_poll_change: Decimal
    favorability_change: Decimal
    poll_sample_size: Decimal
    source_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
            "input",
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("debate_id", self.debate_id)
        _require_canonical_string("poll_source", self.poll_source)
        for field_name in (
            "debate_performance_score",
            "post_debate_poll_change",
            "favorability_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "poll_sample_size",
            _normalize_nonnegative_decimal("poll_sample_size", self.poll_sample_size),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class MarketResearchPoliticsDebatePerformancePollReactionDigestRow(
    _FinalPublicDataclass,
):
    candidate_id: str
    debate_id: str
    poll_source: str
    reaction_status: str
    debate_performance_score: Decimal
    post_debate_poll_change: Decimal
    favorability_change: Decimal
    poll_sample_size: Decimal
    poll_reaction_pressure_score: Decimal
    source_observed_at: datetime
    source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPoliticsDebatePerformancePollReactionDigestRow,
            "row",
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("debate_id", self.debate_id)
        _require_canonical_string("poll_source", self.poll_source)
        _require_status("reaction_status", self.reaction_status)
        for field_name in (
            "debate_performance_score",
            "post_debate_poll_change",
            "favorability_change",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "poll_sample_size",
            "poll_reaction_pressure_score",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.reaction_status != _row_status(self.reason_codes):
            raise ValueError("reaction_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchPoliticsDebatePerformancePollReactionDigestReport(
    _FinalPublicDataclass,
):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    negative_poll_reaction_count: Decimal
    low_performance_count: Decimal
    low_sample_size_count: Decimal
    stale_source_count: Decimal
    mean_poll_reaction_pressure_score: Decimal
    max_poll_reaction_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
        ...,
    ]
    candidate_rows: tuple[
        MarketResearchPoliticsDebatePerformancePollReactionDigestRow,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchPoliticsDebatePerformancePollReactionDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "negative_poll_reaction_count",
            "low_performance_count",
            "low_sample_size_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_poll_reaction_pressure_score",
            "max_poll_reaction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "candidate_rows", _normalize_rows(self.candidate_rows))
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
    MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
    MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
    MarketResearchPoliticsDebatePerformancePollReactionDigestReport,
    MarketResearchPoliticsDebatePerformancePollReactionDigestRow,
)


def build_market_research_politics_debate_performance_poll_reaction_digest_report(
    observations: Iterable[MarketResearchPoliticsDebatePerformancePollReactionDigestInput],
    *,
    config: MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
    generated_at: datetime,
) -> MarketResearchPoliticsDebatePerformancePollReactionDigestReport:
    if type(config) is not MarketResearchPoliticsDebatePerformancePollReactionDigestConfig:
        raise ValueError(
            "config must be a MarketResearchPoliticsDebatePerformancePollReactionDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(observations)
    rows = tuple(
        sorted(
            (
                _digest_row(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return MarketResearchPoliticsDebatePerformancePollReactionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        negative_poll_reaction_count=_count(
            sum(
                1
                for row in rows
                if any(code.startswith("poll_reaction_drop_") for code in row.reason_codes)
            ),
        ),
        low_performance_count=_count(
            sum(
                1
                for row in rows
                if any(
                    code.startswith("debate_performance_score_low_")
                    for code in row.reason_codes
                )
            ),
        ),
        low_sample_size_count=_count(
            sum(1 for row in rows if "poll_sample_size_low_watch" in row.reason_codes),
        ),
        stale_source_count=_count(
            sum(1 for row in rows if "source_stale_watch" in row.reason_codes),
        ),
        mean_poll_reaction_pressure_score=_mean(
            tuple(row.poll_reaction_pressure_score for row in rows),
        ),
        max_poll_reaction_pressure_score=_max_decimal(
            tuple(row.poll_reaction_pressure_score for row in rows),
        ),
        status=_rollup_status(tuple(row.reaction_status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        candidate_rows=rows,
    )


def market_research_politics_debate_performance_poll_reaction_digest_payload(
    report: MarketResearchPoliticsDebatePerformancePollReactionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPoliticsDebatePerformancePollReactionDigestReport:
        raise ValueError(
            "report must be a MarketResearchPoliticsDebatePerformancePollReactionDigestReport",
        )
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    output = _json_ready(report)
    if type(output) is not dict:
        raise ValueError("report output must be a JSON object")
    _require_hard_flags("output", _DictFlags(output))
    _reject_unsafe_public_payload("output", output)
    return output


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


def _revalidate_public_dataclass_for_payload(label: str, value: object) -> None:
    if type(value) is MarketResearchPoliticsDebatePerformancePollReactionDigestConfig:
        _revalidate_config_for_payload(value)
        return
    if type(value) is MarketResearchPoliticsDebatePerformancePollReactionDigestInput:
        _revalidate_input_for_payload(value)
        return
    if type(value) is MarketResearchPoliticsDebatePerformancePollReactionDigestRow:
        _revalidate_row_for_payload(value)
        return
    if type(value) is MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount:
        _revalidate_reason_code_count_for_payload(value)
        return
    if type(value) is MarketResearchPoliticsDebatePerformancePollReactionDigestReport:
        _revalidate_report_for_payload(value)
        return
    raise ValueError(f"{label} contains nonpublic dataclass")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains nonpublic dataclass")
        _revalidate_public_dataclass_for_payload(label, value)
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains nonpublic value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _revalidate_config_for_payload(
    config: MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
) -> None:
    _require_exact_type(
        config,
        MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
        "config",
    )
    _require_canonical_string("config_version", config.config_version)
    for field_name in (
        "performance_score_watch_floor",
        "performance_score_blocked_floor",
        "poll_reaction_drop_watch",
        "poll_reaction_drop_blocked",
        "favorability_drop_watch",
        "favorability_drop_blocked",
        "poll_sample_size_floor",
        "stale_source_age_seconds",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(config, field_name))
    _require_at_most(
        "performance_score_blocked_floor",
        config.performance_score_blocked_floor,
        config.performance_score_watch_floor,
    )
    _require_at_most(
        "poll_reaction_drop_watch",
        config.poll_reaction_drop_watch,
        config.poll_reaction_drop_blocked,
    )
    _require_at_most(
        "favorability_drop_watch",
        config.favorability_drop_watch,
        config.favorability_drop_blocked,
    )
    _require_hard_flags("config", config)


def _revalidate_input_for_payload(
    row: MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
) -> None:
    _require_exact_type(
        row,
        MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
        "input",
    )
    _require_canonical_string("candidate_id", row.candidate_id)
    _require_canonical_string("debate_id", row.debate_id)
    _require_canonical_string("poll_source", row.poll_source)
    for field_name in (
        "debate_performance_score",
        "post_debate_poll_change",
        "favorability_change",
    ):
        _require_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_nonnegative_six_decimal_decimal("poll_sample_size", row.poll_sample_size)
    _require_utc_datetime("source_observed_at", row.source_observed_at)
    _require_reason_codes_tuple(row.reason_codes)
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    _require_hard_flags("input", row)


def _revalidate_row_for_payload(
    row: MarketResearchPoliticsDebatePerformancePollReactionDigestRow,
) -> None:
    _require_exact_type(
        row,
        MarketResearchPoliticsDebatePerformancePollReactionDigestRow,
        "row",
    )
    _require_canonical_string("candidate_id", row.candidate_id)
    _require_canonical_string("debate_id", row.debate_id)
    _require_canonical_string("poll_source", row.poll_source)
    _require_status("reaction_status", row.reaction_status)
    for field_name in (
        "debate_performance_score",
        "post_debate_poll_change",
        "favorability_change",
    ):
        _require_six_decimal_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "poll_sample_size",
        "poll_reaction_pressure_score",
        "source_age_seconds",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_utc_datetime("source_observed_at", row.source_observed_at)
    _require_reason_codes_tuple(row.reason_codes)
    if row.reason_codes != _normalize_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.reaction_status != _row_status(row.reason_codes):
        raise ValueError("reaction_status must match reason_codes")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(
    row: MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
) -> None:
    _require_exact_type(
        row,
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
        "reason_code_count",
    )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_whole_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _revalidate_report_for_payload(
    report: MarketResearchPoliticsDebatePerformancePollReactionDigestReport,
) -> None:
    _require_exact_type(
        report,
        MarketResearchPoliticsDebatePerformancePollReactionDigestReport,
        "report",
    )
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "negative_poll_reaction_count",
        "low_performance_count",
        "low_sample_size_count",
        "stale_source_count",
    ):
        _require_nonnegative_whole_six_decimal_decimal(
            field_name,
            getattr(report, field_name),
        )
    for field_name in (
        "mean_poll_reaction_pressure_score",
        "max_poll_reaction_pressure_score",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _require_reason_codes_tuple(report.reason_codes)
    _normalize_report_reason_codes(report.reason_codes)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in report.reason_code_counts:
        if type(row) is not MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount values",
            )
        _revalidate_reason_code_count_for_payload(row)
    if type(report.candidate_rows) is not tuple:
        raise ValueError("candidate_rows must be a tuple")
    for row in report.candidate_rows:
        if type(row) is not MarketResearchPoliticsDebatePerformancePollReactionDigestRow:
            raise ValueError(
                "candidate_rows must contain MarketResearchPoliticsDebatePerformancePollReactionDigestRow values",
            )
        _revalidate_row_for_payload(row)
    _validate_report(report)
    _require_hard_flags("report", report)


def _digest_row(
    row: MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
    *,
    config: MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
    generated_at: datetime,
) -> MarketResearchPoliticsDebatePerformancePollReactionDigestRow:
    source_age_seconds = _source_age_seconds(row.source_observed_at, generated_at)
    reason_codes = _row_reason_codes(
        row,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    return MarketResearchPoliticsDebatePerformancePollReactionDigestRow(
        candidate_id=row.candidate_id,
        debate_id=row.debate_id,
        poll_source=row.poll_source,
        reaction_status=_row_status(reason_codes),
        debate_performance_score=row.debate_performance_score,
        post_debate_poll_change=row.post_debate_poll_change,
        favorability_change=row.favorability_change,
        poll_sample_size=row.poll_sample_size,
        poll_reaction_pressure_score=_poll_reaction_pressure_score(row, config=config),
        source_observed_at=row.source_observed_at,
        source_age_seconds=source_age_seconds,
        reason_codes=reason_codes,
    )


def _poll_reaction_pressure_score(
    row: MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
    *,
    config: MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
) -> Decimal:
    performance_pressure = (
        _quantize(config.performance_score_watch_floor - row.debate_performance_score)
        if row.debate_performance_score < config.performance_score_watch_floor
        else ZERO
    )
    poll_pressure = (
        _quantize(-row.post_debate_poll_change)
        if row.post_debate_poll_change <= -config.poll_reaction_drop_watch
        else ZERO
    )
    favorability_pressure = (
        _quantize(-row.favorability_change)
        if row.favorability_change <= -config.favorability_drop_watch
        else ZERO
    )
    sample_pressure = _sample_shortfall_pressure(row.poll_sample_size, config)
    return _quantize(
        performance_pressure
        + poll_pressure
        + favorability_pressure
        + sample_pressure,
    )


def _sample_shortfall_pressure(
    poll_sample_size: Decimal,
    config: MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
) -> Decimal:
    if poll_sample_size >= config.poll_sample_size_floor:
        return ZERO
    if config.poll_sample_size_floor == ZERO:
        return ZERO
    return _quantize(
        (config.poll_sample_size_floor - poll_sample_size)
        / config.poll_sample_size_floor
        * SAMPLE_SHORTFALL_WEIGHT,
    )


def _row_reason_codes(
    row: MarketResearchPoliticsDebatePerformancePollReactionDigestInput,
    *,
    source_age_seconds: Decimal,
    config: MarketResearchPoliticsDebatePerformancePollReactionDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    if row.debate_performance_score <= config.performance_score_blocked_floor:
        reason_codes.append("debate_performance_score_low_blocked")
    elif row.debate_performance_score < config.performance_score_watch_floor:
        reason_codes.append("debate_performance_score_low_watch")
    if row.post_debate_poll_change <= -config.poll_reaction_drop_blocked:
        reason_codes.append("poll_reaction_drop_blocked")
    elif row.post_debate_poll_change <= -config.poll_reaction_drop_watch:
        reason_codes.append("poll_reaction_drop_watch")
    if row.favorability_change <= -config.favorability_drop_blocked:
        reason_codes.append("favorability_drop_blocked")
    elif row.favorability_change <= -config.favorability_drop_watch:
        reason_codes.append("favorability_drop_watch")
    if row.poll_sample_size < config.poll_sample_size_floor:
        reason_codes.append("poll_sample_size_low_watch")
    if source_age_seconds > config.stale_source_age_seconds:
        reason_codes.append("source_stale_watch")
    if not _has_reaction_reason(reason_codes):
        reason_codes.append("debate_poll_reaction_clear")
    return tuple(sorted(set(reason_codes)))


def _has_reaction_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code.endswith("_watch") or reason_code.endswith("_blocked")
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "blocked"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[MarketResearchPoliticsDebatePerformancePollReactionDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.reaction_status for row in rows))
    reason_codes = [
        f"politics_debate_performance_poll_reaction_digest_{'clear' if status == 'pass' else status}",
    ]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "debate_performance_score_low_blocked",
        "debate_performance_score_low_watch",
        "favorability_drop_blocked",
        "favorability_drop_watch",
        "poll_reaction_drop_blocked",
        "poll_reaction_drop_watch",
        "poll_sample_size_low_watch",
        "source_stale_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[MarketResearchPoliticsDebatePerformancePollReactionDigestRow, ...],
) -> tuple[MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _source_age_seconds(source_observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(
        str(
            (
                generated_at - _as_utc("source_observed_at", source_observed_at)
            ).total_seconds(),
        ),
    )
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("source_observed_at must not be after generated_at")
    return age_seconds


def _normalize_inputs(
    observations: Iterable[MarketResearchPoliticsDebatePerformancePollReactionDigestInput],
) -> tuple[MarketResearchPoliticsDebatePerformancePollReactionDigestInput, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchPoliticsDebatePerformancePollReactionDigestInput:
            raise ValueError(
                "observations must contain MarketResearchPoliticsDebatePerformancePollReactionDigestInput values",
            )
        _require_hard_flags("input", row)
        if row.candidate_id in seen_ids:
            raise ValueError("observations must not contain duplicate candidate_id values")
        seen_ids.add(row.candidate_id)
    return rows


def _normalize_rows(
    rows: Iterable[MarketResearchPoliticsDebatePerformancePollReactionDigestRow],
) -> tuple[MarketResearchPoliticsDebatePerformancePollReactionDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("candidate_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("candidate_rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in values:
        if type(row) is not MarketResearchPoliticsDebatePerformancePollReactionDigestRow:
            raise ValueError(
                "candidate_rows must contain MarketResearchPoliticsDebatePerformancePollReactionDigestRow values",
            )
        _require_hard_flags("row", row)
        if row.candidate_id in seen_ids:
            raise ValueError("candidate_rows must not contain duplicate candidate_id values")
        seen_ids.add(row.candidate_id)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("candidate_rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[
        MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount,
    ],
) -> tuple[MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketResearchPoliticsDebatePerformancePollReactionDigestReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(
    row: MarketResearchPoliticsDebatePerformancePollReactionDigestRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.reaction_status],
        -row.poll_reaction_pressure_score,
        row.candidate_id,
        row.debate_id,
        row.poll_source,
    )


def _status_count(
    rows: tuple[MarketResearchPoliticsDebatePerformancePollReactionDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.reaction_status == status))


def _validate_report(
    report: MarketResearchPoliticsDebatePerformancePollReactionDigestReport,
) -> None:
    rows = report.candidate_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match candidate_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match candidate_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match candidate_rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match candidate_rows")
    if report.negative_poll_reaction_count != _count(
        sum(
            1
            for row in rows
            if any(code.startswith("poll_reaction_drop_") for code in row.reason_codes)
        ),
    ):
        raise ValueError("negative_poll_reaction_count must match candidate_rows")
    if report.low_performance_count != _count(
        sum(
            1
            for row in rows
            if any(
                code.startswith("debate_performance_score_low_")
                for code in row.reason_codes
            )
        ),
    ):
        raise ValueError("low_performance_count must match candidate_rows")
    if report.low_sample_size_count != _count(
        sum(1 for row in rows if "poll_sample_size_low_watch" in row.reason_codes),
    ):
        raise ValueError("low_sample_size_count must match candidate_rows")
    if report.stale_source_count != _count(
        sum(1 for row in rows if "source_stale_watch" in row.reason_codes),
    ):
        raise ValueError("stale_source_count must match candidate_rows")
    if report.mean_poll_reaction_pressure_score != _mean(
        tuple(row.poll_reaction_pressure_score for row in rows),
    ):
        raise ValueError("mean_poll_reaction_pressure_score must match candidate_rows")
    if report.max_poll_reaction_pressure_score != _max_decimal(
        tuple(row.poll_reaction_pressure_score for row in rows),
    ):
        raise ValueError("max_poll_reaction_pressure_score must match candidate_rows")
    if report.status != _rollup_status(tuple(row.reaction_status for row in rows)):
        raise ValueError("status must match candidate_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match candidate_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match candidate_rows")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains nonpublic dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        _require_six_decimal_decimal(path or label, value)
        return
    if isinstance(value, datetime):
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_whole_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    _require_whole_count(field_name, normalized)
    return normalized


def _normalize_positive_whole_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_whole_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_nonnegative_six_decimal_decimal(field_name: str, value: Decimal) -> None:
    _require_six_decimal_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_whole_six_decimal_decimal(
    field_name: str,
    value: Decimal,
) -> None:
    _require_nonnegative_six_decimal_decimal(field_name, value)
    _require_whole_count(field_name, value)


def _require_positive_whole_six_decimal_decimal(
    field_name: str,
    value: Decimal,
) -> None:
    _require_nonnegative_whole_six_decimal_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_whole_count(field_name: str, value: Decimal) -> None:
    if value != _count(int(value)):
        raise ValueError(f"{field_name} must be a whole count")


def _require_reason_codes_tuple(reason_codes: object) -> None:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple(reason_codes)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    normalized = tuple(sorted(reason_codes))
    if reason_codes != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple(reason_codes)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    return reason_codes


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
