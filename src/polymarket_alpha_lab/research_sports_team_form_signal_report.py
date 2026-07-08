"""Pure sports form signal reporting for caller-supplied team and player rows."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchSportsTeamFormSignalConfig",
    "ResearchSportsTeamFormSignalInputRow",
    "ResearchSportsTeamFormSignalReasonCodeCount",
    "ResearchSportsTeamFormSignalReport",
    "ResearchSportsTeamFormSignalRow",
    "build_research_sports_team_form_signal_report",
    "research_sports_team_form_signal_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-sports-team-form-signal-report-v0"
STATUSES = ("pass", "watch", "block")
PARTICIPANT_KINDS = ("team", "player")
SIDES = ("home", "away", "neutral")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
RATIO_QUANTUM = Decimal("0.000001")
HALF = Decimal("0.500000")
RECENT_FORM_WEIGHT = Decimal("0.300000")
AVAILABILITY_WEIGHT = Decimal("0.200000")
SCHEDULE_DENSITY_WEIGHT = Decimal("0.150000")
VENUE_SUPPORT_WEIGHT = Decimal("0.125000")
FRESHNESS_WEIGHT = Decimal("0.067500")
CONTRADICTION_WEIGHT = Decimal("0.157500")
POINT_DIFFERENTIAL_RANGE = Decimal("20")
POINT_DIFFERENTIAL_MIDPOINT = Decimal("10")


@dataclass(frozen=True)
class ResearchSportsTeamFormSignalConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_recent_games: Decimal = Decimal("3")
    recent_form_pass_score: Decimal = Decimal("0.600000")
    recent_form_block_score: Decimal = Decimal("0.300000")
    availability_watch_threshold: Decimal = Decimal("0.700000")
    availability_block_threshold: Decimal = Decimal("0.400000")
    key_absence_watch_count: Decimal = Decimal("1")
    key_absence_block_count: Decimal = Decimal("3")
    schedule_watch_games_last_7_days: Decimal = Decimal("3")
    schedule_block_games_last_7_days: Decimal = Decimal("4")
    rest_days_watch_threshold: Decimal = Decimal("2")
    rest_days_block_threshold: Decimal = Decimal("1")
    venue_watch_threshold: Decimal = Decimal("0.450000")
    venue_block_threshold: Decimal = Decimal("0.250000")
    fresh_information_max_age_seconds: Decimal = Decimal("3600")
    stale_information_block_age_seconds: Decimal = Decimal("21600")
    contradiction_watch_ratio: Decimal = Decimal("0.250000")
    contradiction_block_ratio: Decimal = Decimal("0.500000")
    overall_pass_score: Decimal = Decimal("0.700000")
    overall_watch_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsTeamFormSignalConfig:
            raise TypeError(
                "ResearchSportsTeamFormSignalConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsTeamFormSignalConfig:
            raise ValueError(
                "config must be exactly ResearchSportsTeamFormSignalConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_recent_games",
            "key_absence_watch_count",
            "key_absence_block_count",
            "schedule_watch_games_last_7_days",
            "schedule_block_games_last_7_days",
            "rest_days_watch_threshold",
            "rest_days_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_form_pass_score",
            "recent_form_block_score",
            "availability_watch_threshold",
            "availability_block_threshold",
            "venue_watch_threshold",
            "venue_block_threshold",
            "contradiction_watch_ratio",
            "contradiction_block_ratio",
            "overall_pass_score",
            "overall_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_information_max_age_seconds",
            "stale_information_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_recent_games == ZERO:
            raise ValueError("min_recent_games must be positive")
        if self.recent_form_pass_score <= self.recent_form_block_score:
            raise ValueError(
                "recent_form_pass_score must exceed recent_form_block_score",
            )
        if self.availability_watch_threshold <= self.availability_block_threshold:
            raise ValueError(
                "availability_watch_threshold must exceed "
                "availability_block_threshold",
            )
        if self.key_absence_watch_count > self.key_absence_block_count:
            raise ValueError(
                "key_absence_watch_count must not exceed key_absence_block_count",
            )
        if self.schedule_watch_games_last_7_days > self.schedule_block_games_last_7_days:
            raise ValueError(
                "schedule_watch_games_last_7_days must not exceed "
                "schedule_block_games_last_7_days",
            )
        if self.rest_days_block_threshold > self.rest_days_watch_threshold:
            raise ValueError(
                "rest_days_block_threshold must not exceed rest_days_watch_threshold",
            )
        if self.venue_watch_threshold <= self.venue_block_threshold:
            raise ValueError("venue_watch_threshold must exceed venue_block_threshold")
        if self.fresh_information_max_age_seconds >= self.stale_information_block_age_seconds:
            raise ValueError(
                "stale_information_block_age_seconds must exceed "
                "fresh_information_max_age_seconds",
            )
        if self.contradiction_watch_ratio > self.contradiction_block_ratio:
            raise ValueError(
                "contradiction_watch_ratio must not exceed contradiction_block_ratio",
            )
        if self.overall_pass_score <= self.overall_watch_score:
            raise ValueError("overall_pass_score must exceed overall_watch_score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSportsTeamFormSignalInputRow:
    research_key: str
    participant_label: str
    participant_kind: str
    side: str
    latest_information_observed_at: datetime
    recent_games_played: Decimal
    recent_win_count: Decimal
    recent_draw_count: Decimal
    recent_loss_count: Decimal
    recent_point_differential: Decimal
    availability_score: Decimal
    key_absence_count: Decimal
    schedule_games_last_7_days: Decimal
    rest_days: Decimal
    venue_support_score: Decimal
    corroborating_signal_count: Decimal
    contradiction_signal_count: Decimal
    public_context_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsTeamFormSignalInputRow:
            raise TypeError(
                "ResearchSportsTeamFormSignalInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsTeamFormSignalInputRow:
            raise ValueError(
                "input row must be exactly ResearchSportsTeamFormSignalInputRow",
            )
        for field_name in ("research_key", "participant_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_enum("participant_kind", self.participant_kind, PARTICIPANT_KINDS)
        _require_enum("side", self.side, SIDES)
        object.__setattr__(
            self,
            "latest_information_observed_at",
            _as_utc(
                "latest_information_observed_at",
                self.latest_information_observed_at,
            ),
        )
        for field_name in (
            "recent_games_played",
            "recent_win_count",
            "recent_draw_count",
            "recent_loss_count",
            "key_absence_count",
            "schedule_games_last_7_days",
            "rest_days",
            "corroborating_signal_count",
            "contradiction_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_point_differential",
            _require_decimal("recent_point_differential", self.recent_point_differential),
        )
        for field_name in ("availability_score", "venue_support_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.recent_win_count
            + self.recent_draw_count
            + self.recent_loss_count
            != self.recent_games_played
        ):
            raise ValueError(
                "recent game counts must sum to recent_games_played",
            )
        object.__setattr__(
            self,
            "public_context_note",
            _normalize_optional_public_note(
                "public_context_note",
                self.public_context_note,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchSportsTeamFormSignalRow:
    research_key: str
    participant_label: str
    participant_kind: str
    side: str
    latest_information_observed_at: datetime
    information_age_seconds: Decimal
    recent_games_played: Decimal
    recent_win_count: Decimal
    recent_draw_count: Decimal
    recent_loss_count: Decimal
    recent_point_differential: Decimal
    recent_form_score: Decimal
    availability_score: Decimal
    key_absence_count: Decimal
    schedule_games_last_7_days: Decimal
    rest_days: Decimal
    schedule_density_score: Decimal
    venue_support_score: Decimal
    freshness_score: Decimal
    corroborating_signal_count: Decimal
    contradiction_signal_count: Decimal
    contradiction_ratio: Decimal
    contradiction_score: Decimal
    team_form_signal_score: Decimal
    team_form_signal_status: str
    redacted_context_note: str | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsTeamFormSignalRow:
            raise TypeError(
                "ResearchSportsTeamFormSignalRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsTeamFormSignalRow:
            raise ValueError("row must be exactly ResearchSportsTeamFormSignalRow")
        for field_name in ("research_key", "participant_label"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_enum("participant_kind", self.participant_kind, PARTICIPANT_KINDS)
        _require_enum("side", self.side, SIDES)
        object.__setattr__(
            self,
            "latest_information_observed_at",
            _as_utc(
                "latest_information_observed_at",
                self.latest_information_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "information_age_seconds",
            _require_nonnegative_decimal(
                "information_age_seconds",
                self.information_age_seconds,
            ),
        )
        for field_name in (
            "recent_games_played",
            "recent_win_count",
            "recent_draw_count",
            "recent_loss_count",
            "key_absence_count",
            "schedule_games_last_7_days",
            "rest_days",
            "corroborating_signal_count",
            "contradiction_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recent_point_differential",
            _require_decimal("recent_point_differential", self.recent_point_differential),
        )
        for field_name in (
            "recent_form_score",
            "availability_score",
            "schedule_density_score",
            "venue_support_score",
            "freshness_score",
            "contradiction_ratio",
            "contradiction_score",
            "team_form_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("team_form_signal_status", self.team_form_signal_status)
        object.__setattr__(
            self,
            "redacted_context_note",
            _normalize_redacted_note("redacted_context_note", self.redacted_context_note),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSportsTeamFormSignalReasonCodeCount:
    reason_code: str
    count: Decimal
    subject_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsTeamFormSignalReasonCodeCount:
            raise TypeError(
                "ResearchSportsTeamFormSignalReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsTeamFormSignalReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSportsTeamFormSignalReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "subject_ratio",
            _require_ratio_decimal("subject_ratio", self.subject_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchSportsTeamFormSignalReport:
    generated_at: datetime
    config_version: str
    status: str
    subject_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_information_count: Decimal
    injury_concern_count: Decimal
    dense_schedule_count: Decimal
    contradiction_count: Decimal
    average_signal_score: Decimal
    average_information_age_seconds: Decimal
    min_rest_days: Decimal
    rows: tuple[ResearchSportsTeamFormSignalRow, ...]
    reason_code_counts: tuple[ResearchSportsTeamFormSignalReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSportsTeamFormSignalReport:
            raise TypeError(
                "ResearchSportsTeamFormSignalReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSportsTeamFormSignalReport:
            raise ValueError("report must be exactly ResearchSportsTeamFormSignalReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "subject_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_information_count",
            "injury_concern_count",
            "dense_schedule_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_signal_score",
            "average_information_age_seconds",
            "min_rest_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_sports_team_form_signal_report(
    input_rows: list[ResearchSportsTeamFormSignalInputRow]
    | tuple[ResearchSportsTeamFormSignalInputRow, ...],
    *,
    config: ResearchSportsTeamFormSignalConfig | None = None,
    generated_at: datetime,
) -> ResearchSportsTeamFormSignalReport:
    cfg = config or ResearchSportsTeamFormSignalConfig()
    if type(cfg) is not ResearchSportsTeamFormSignalConfig:
        raise ValueError("config must be a ResearchSportsTeamFormSignalConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows)
    for row in rows:
        if row.latest_information_observed_at > report_time:
            raise ValueError("latest_information_observed_at must not be in the future")
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = tuple(sorted(built_rows, key=lambda row: row.research_key))
    subject_count = _count(len(ranked_rows))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = _summary_reason_codes(ranked_rows)
    if not ranked_rows:
        reason_code_counts = (
            ResearchSportsTeamFormSignalReasonCodeCount(
                reason_code="no_sports_subjects",
                count=ONE,
                subject_ratio=ONE,
            ),
        )
        reason_codes = ("no_sports_subjects",)
    return ResearchSportsTeamFormSignalReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_summary_status(ranked_rows),
        subject_count=subject_count,
        pass_count=_status_count(ranked_rows, "pass"),
        watch_count=_status_count(ranked_rows, "watch"),
        block_count=_status_count(ranked_rows, "block"),
        stale_information_count=_count(
            sum(
                1
                for row in ranked_rows
                if "information_stale_watch" in row.reason_codes
                or "information_stale_block" in row.reason_codes
            ),
        ),
        injury_concern_count=_count(
            sum(
                1
                for row in ranked_rows
                if "availability_watch" in row.reason_codes
                or "availability_block" in row.reason_codes
                or "key_absence_watch" in row.reason_codes
                or "key_absence_block" in row.reason_codes
            ),
        ),
        dense_schedule_count=_count(
            sum(
                1
                for row in ranked_rows
                if "schedule_density_watch" in row.reason_codes
                or "schedule_density_block" in row.reason_codes
                or "low_rest_watch" in row.reason_codes
                or "low_rest_block" in row.reason_codes
            ),
        ),
        contradiction_count=_count(
            sum(
                1
                for row in ranked_rows
                if "contradiction_watch" in row.reason_codes
                or "contradiction_block" in row.reason_codes
            ),
        ),
        average_signal_score=_ratio(
            _sum_decimal(row.team_form_signal_score for row in ranked_rows),
            subject_count,
        ),
        average_information_age_seconds=_ratio(
            _sum_decimal(row.information_age_seconds for row in ranked_rows),
            subject_count,
        ),
        min_rest_days=min((row.rest_days for row in ranked_rows), default=ZERO),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_sports_team_form_signal_report_payload(
    report: ResearchSportsTeamFormSignalReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSportsTeamFormSignalReport:
        raise ValueError("report must be a ResearchSportsTeamFormSignalReport")
    _require_hard_flags("report", report)
    _reject_unsafe_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _build_row(
    input_row: ResearchSportsTeamFormSignalInputRow,
    *,
    config: ResearchSportsTeamFormSignalConfig,
    generated_at: datetime,
) -> ResearchSportsTeamFormSignalRow:
    information_age_seconds = _age_seconds(
        generated_at,
        input_row.latest_information_observed_at,
    )
    recent_form_score = _recent_form_score(input_row)
    schedule_density_score = _schedule_density_score(input_row, config=config)
    freshness_score = _freshness_score(
        information_age_seconds,
        fresh_information_max_age_seconds=config.fresh_information_max_age_seconds,
        stale_information_block_age_seconds=config.stale_information_block_age_seconds,
    )
    contradiction_ratio = _contradiction_ratio(input_row)
    contradiction_score = _quantize(ONE - contradiction_ratio)
    signal_score = _signal_score(
        recent_form_score=recent_form_score,
        availability_score=input_row.availability_score,
        schedule_density_score=schedule_density_score,
        venue_support_score=input_row.venue_support_score,
        freshness_score=freshness_score,
        contradiction_score=contradiction_score,
    )
    reason_codes = _row_reason_codes(
        input_row,
        config=config,
        information_age_seconds=information_age_seconds,
        recent_form_score=recent_form_score,
        contradiction_ratio=contradiction_ratio,
        signal_score=signal_score,
    )
    return ResearchSportsTeamFormSignalRow(
        research_key=input_row.research_key,
        participant_label=input_row.participant_label,
        participant_kind=input_row.participant_kind,
        side=input_row.side,
        latest_information_observed_at=input_row.latest_information_observed_at,
        information_age_seconds=information_age_seconds,
        recent_games_played=input_row.recent_games_played,
        recent_win_count=input_row.recent_win_count,
        recent_draw_count=input_row.recent_draw_count,
        recent_loss_count=input_row.recent_loss_count,
        recent_point_differential=input_row.recent_point_differential,
        recent_form_score=recent_form_score,
        availability_score=input_row.availability_score,
        key_absence_count=input_row.key_absence_count,
        schedule_games_last_7_days=input_row.schedule_games_last_7_days,
        rest_days=input_row.rest_days,
        schedule_density_score=schedule_density_score,
        venue_support_score=input_row.venue_support_score,
        freshness_score=freshness_score,
        corroborating_signal_count=input_row.corroborating_signal_count,
        contradiction_signal_count=input_row.contradiction_signal_count,
        contradiction_ratio=contradiction_ratio,
        contradiction_score=contradiction_score,
        team_form_signal_score=signal_score,
        team_form_signal_status=_row_status(reason_codes),
        redacted_context_note=_redacted_note(input_row.public_context_note),
        reason_codes=reason_codes,
    )


def _recent_form_score(input_row: ResearchSportsTeamFormSignalInputRow) -> Decimal:
    if input_row.recent_games_played == ZERO:
        return ZERO
    outcome_score = _ratio(
        input_row.recent_win_count + (input_row.recent_draw_count * HALF),
        input_row.recent_games_played,
    )
    point_differential_per_game = _ratio(
        input_row.recent_point_differential,
        input_row.recent_games_played,
    )
    point_differential_score = _bounded_ratio(
        (point_differential_per_game + POINT_DIFFERENTIAL_MIDPOINT)
        / POINT_DIFFERENTIAL_RANGE,
    )
    return _quantize((outcome_score * Decimal("0.700000")) + (point_differential_score * Decimal("0.300000")))


def _schedule_density_score(
    input_row: ResearchSportsTeamFormSignalInputRow,
    *,
    config: ResearchSportsTeamFormSignalConfig,
) -> Decimal:
    if (
        input_row.schedule_games_last_7_days >= config.schedule_block_games_last_7_days
        or input_row.rest_days <= config.rest_days_block_threshold
    ):
        return ZERO
    denominator = config.schedule_block_games_last_7_days * TWO
    if denominator == ZERO:
        return ZERO
    return _bounded_ratio(ONE - (input_row.schedule_games_last_7_days / denominator))


def _freshness_score(
    information_age_seconds: Decimal,
    *,
    fresh_information_max_age_seconds: Decimal,
    stale_information_block_age_seconds: Decimal,
) -> Decimal:
    if information_age_seconds <= fresh_information_max_age_seconds:
        return ONE
    if information_age_seconds >= stale_information_block_age_seconds:
        return ZERO
    remaining = stale_information_block_age_seconds - information_age_seconds
    window = stale_information_block_age_seconds - fresh_information_max_age_seconds
    return _bounded_ratio(remaining / window)


def _contradiction_ratio(input_row: ResearchSportsTeamFormSignalInputRow) -> Decimal:
    total = input_row.corroborating_signal_count + input_row.contradiction_signal_count
    if total == ZERO:
        return ZERO
    return _ratio(input_row.contradiction_signal_count, total)


def _signal_score(
    *,
    recent_form_score: Decimal,
    availability_score: Decimal,
    schedule_density_score: Decimal,
    venue_support_score: Decimal,
    freshness_score: Decimal,
    contradiction_score: Decimal,
) -> Decimal:
    return _quantize(
        (recent_form_score * RECENT_FORM_WEIGHT)
        + (availability_score * AVAILABILITY_WEIGHT)
        + (schedule_density_score * SCHEDULE_DENSITY_WEIGHT)
        + (venue_support_score * VENUE_SUPPORT_WEIGHT)
        + (freshness_score * FRESHNESS_WEIGHT)
        + (contradiction_score * CONTRADICTION_WEIGHT),
    )


def _row_reason_codes(
    input_row: ResearchSportsTeamFormSignalInputRow,
    *,
    config: ResearchSportsTeamFormSignalConfig,
    information_age_seconds: Decimal,
    recent_form_score: Decimal,
    contradiction_ratio: Decimal,
    signal_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if input_row.recent_games_played < config.min_recent_games:
        reason_codes.append("recent_form_watch")
    elif recent_form_score <= config.recent_form_block_score:
        reason_codes.append("recent_form_block")
    elif recent_form_score < config.recent_form_pass_score:
        reason_codes.append("recent_form_watch")
    else:
        reason_codes.append("recent_form_clear")

    if input_row.availability_score <= config.availability_block_threshold:
        reason_codes.append("availability_block")
    elif input_row.availability_score < config.availability_watch_threshold:
        reason_codes.append("availability_watch")
    else:
        reason_codes.append("availability_clear")

    if input_row.key_absence_count >= config.key_absence_block_count:
        reason_codes.append("key_absence_block")
    elif input_row.key_absence_count >= config.key_absence_watch_count:
        reason_codes.append("key_absence_watch")

    if input_row.schedule_games_last_7_days >= config.schedule_block_games_last_7_days:
        reason_codes.append("schedule_density_block")
    elif input_row.schedule_games_last_7_days >= config.schedule_watch_games_last_7_days:
        reason_codes.append("schedule_density_watch")
    else:
        reason_codes.append("schedule_density_clear")

    if input_row.rest_days <= config.rest_days_block_threshold:
        reason_codes.append("low_rest_block")
    elif input_row.rest_days <= config.rest_days_watch_threshold:
        reason_codes.append("low_rest_watch")

    if input_row.venue_support_score <= config.venue_block_threshold:
        reason_codes.append("venue_support_block")
    elif input_row.venue_support_score < config.venue_watch_threshold:
        reason_codes.append("venue_support_watch")
    else:
        reason_codes.append("venue_support_clear")

    if information_age_seconds >= config.stale_information_block_age_seconds:
        reason_codes.append("information_stale_block")
    elif information_age_seconds > config.fresh_information_max_age_seconds:
        reason_codes.append("information_stale_watch")
    else:
        reason_codes.append("fresh_information")

    if contradiction_ratio >= config.contradiction_block_ratio:
        reason_codes.append("contradiction_block")
    elif contradiction_ratio >= config.contradiction_watch_ratio:
        reason_codes.append("contradiction_watch")
    else:
        reason_codes.append("contradiction_clear")

    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        reason_codes.append("sports_form_signal_block")
    elif (
        any(reason_code.endswith("_watch") for reason_code in reason_codes)
        or signal_score < config.overall_pass_score
    ):
        reason_codes.append("sports_form_signal_watch")
    elif signal_score < config.overall_watch_score:
        reason_codes.append("sports_form_signal_block")
    else:
        reason_codes.append("sports_form_signal_pass")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "sports_form_signal_block" in reason_codes:
        return "block"
    if "sports_form_signal_watch" in reason_codes:
        return "watch"
    return "pass"


def _summary_status(rows: tuple[ResearchSportsTeamFormSignalRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.team_form_signal_status == "block" for row in rows):
        return "block"
    if any(row.team_form_signal_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchSportsTeamFormSignalRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_sports_subjects",)
    summary_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if not reason_code.endswith("_clear")
        and reason_code != "fresh_information"
        and reason_code != "sports_form_signal_pass"
    }
    if not summary_codes:
        summary_codes.add("sports_form_signal_pass")
    return tuple(sorted(summary_codes))


def _reason_code_counts(
    rows: tuple[ResearchSportsTeamFormSignalRow, ...],
) -> tuple[ResearchSportsTeamFormSignalReasonCodeCount, ...]:
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    subject_count = _count(len(rows))
    return tuple(
        ResearchSportsTeamFormSignalReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            subject_ratio=_ratio(_count(count), subject_count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _status_count(
    rows: tuple[ResearchSportsTeamFormSignalRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.team_form_signal_status == status))


def _normalize_input_rows(
    input_rows: list[ResearchSportsTeamFormSignalInputRow]
    | tuple[ResearchSportsTeamFormSignalInputRow, ...],
) -> tuple[ResearchSportsTeamFormSignalInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    rows = tuple(input_rows)
    for row in rows:
        if type(row) is not ResearchSportsTeamFormSignalInputRow:
            raise ValueError(
                "input_rows must contain ResearchSportsTeamFormSignalInputRow values",
            )
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSportsTeamFormSignalRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSportsTeamFormSignalRow:
            raise ValueError(
                "rows must contain ResearchSportsTeamFormSignalRow values",
            )
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchSportsTeamFormSignalReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchSportsTeamFormSignalReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSportsTeamFormSignalReasonCodeCount values",
            )
    return rows


def _validate_row(row: ResearchSportsTeamFormSignalRow) -> None:
    if row.recent_win_count + row.recent_draw_count + row.recent_loss_count != row.recent_games_played:
        raise ValueError("recent game counts must sum to recent_games_played")
    if row.contradiction_signal_count > row.corroborating_signal_count + row.contradiction_signal_count:
        raise ValueError("contradiction_signal_count is inconsistent")
    expected_status = _row_status(row.reason_codes)
    if row.team_form_signal_status != expected_status:
        raise ValueError("team_form_signal_status does not match reason_codes")


def _validate_report(report: ResearchSportsTeamFormSignalReport) -> None:
    row_count = _count(len(report.rows))
    if report.subject_count != row_count:
        raise ValueError("subject_count does not match rows")
    if report.pass_count + report.watch_count + report.block_count != row_count:
        raise ValueError("status counts do not match rows")
    expected_status = _summary_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status does not match row statuses")
    if report.rows:
        expected_reason_codes = _summary_reason_codes(report.rows)
    else:
        expected_reason_codes = ("no_sports_subjects",)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match rows")


def _redacted_note(value: str | None) -> str | None:
    if value is None:
        return None
    return "note_provided"


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_payload(label: str, value: object) -> None:
    unsafe_key_tokens = (
        "raw_source",
        "raw_sources",
        "raw_market",
        "raw_markets",
        "raw_event",
        "raw_events",
        "raw_condition",
        "raw_conditions",
        "source_id",
        "source_label",
        "market_id",
        "market_slug",
        "event_id",
        "event_slug",
        "condition_id",
    )
    if is_dataclass(value):
        _reject_unsafe_payload(label, _json_ready(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = str(key).lower()
            if lowered_key in unsafe_key_tokens:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(token in lowered_value for token in unsafe_key_tokens):
            raise ValueError(f"{label} contains unsafe public value")


def _payload_contains_safe_flags(value: object) -> bool:
    if not hasattr(value, "paper_only"):
        return False
    if not hasattr(value, "report_only"):
        return False
    return hasattr(value, "readonly")


def _require_hard_flags(label: str, value: object) -> None:
    if not _payload_contains_safe_flags(value):
        raise ValueError(f"{label} must expose hard report flags")
    if value.paper_only is not True:
        raise ValueError(f"{label} paper_only must be True")
    if value.report_only is not True:
        raise ValueError(f"{label} report_only must be True")
    if value.readonly is not True:
        raise ValueError(f"{label} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    seconds = (generated_at - observed_at).total_seconds()
    if seconds < 0:
        raise ValueError("observed_at must not be in the future")
    return Decimal(str(int(seconds)))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must not be negative")
    return Decimal(str(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimal values")
        total += value
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if type(numerator) is not Decimal or type(denominator) is not Decimal:
        raise ValueError("ratio values must be Decimal values")
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _bounded_ratio(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("ratio value must be a Decimal")
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    return value.quantize(RATIO_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    try:
        normalized = +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must not be negative")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(Decimal("1"))


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_optional_public_note(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    lowered = value.lower()
    unsafe_fragments = (
        "raw source",
        "raw market",
        "raw event",
        "source id",
        "market id",
        "event id",
        "condition id",
        "://",
    )
    if any(fragment in lowered for fragment in unsafe_fragments):
        raise ValueError(f"{field_name} contains unsafe text")
    return value


def _normalize_redacted_note(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if value != "note_provided":
        raise ValueError(f"{field_name} must be note_provided when present")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    _require_enum(field_name, value, STATUSES)


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
