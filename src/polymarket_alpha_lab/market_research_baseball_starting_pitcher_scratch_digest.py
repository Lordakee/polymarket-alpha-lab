"""Pure in-memory reducer for baseball starting pitcher scratch reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN


DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_SCRATCH_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-starting-pitcher-scratch-digest-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
CLEAR_STATUS = "clear"

HIGH_PROBABILITY_REASON = "baseball_starting_pitcher_scratch_high_probability"
UNCONFIRMED_LINEUP_REASON = "baseball_starting_pitcher_scratch_unconfirmed_lineup"
REPLACEMENT_NAMED_REASON = "baseball_starting_pitcher_scratch_replacement_named"
THIN_SOURCES_REASON = "baseball_starting_pitcher_scratch_thin_sources"
CLEAR_REASON = "baseball_starting_pitcher_scratch_clear"
PASSED_REASON = "baseball_starting_pitcher_scratch_passed"
EMPTY_REASON = "baseball_starting_pitcher_scratch_empty"

ROW_REASON_CODES = (
    HIGH_PROBABILITY_REASON,
    REPLACEMENT_NAMED_REASON,
    THIN_SOURCES_REASON,
    UNCONFIRMED_LINEUP_REASON,
    CLEAR_REASON,
)
DIGEST_REASON_CODES = (
    HIGH_PROBABILITY_REASON,
    REPLACEMENT_NAMED_REASON,
    THIN_SOURCES_REASON,
    UNCONFIRMED_LINEUP_REASON,
    PASSED_REASON,
    EMPTY_REASON,
)
NEXT_STEP_BY_STATUS = {
    PASS_STATUS: "continue_report_only_baseball_starting_pitcher_scratch_digest",
    WATCH_STATUS: "review_report_only_baseball_starting_pitcher_scratch_digest",
}

ZERO = Decimal("0")
ONE = Decimal("1")
SIXTY = Decimal("60")
MICROSECONDS_PER_SECOND = Decimal("1000000")
QUANTUM = Decimal("0.000001")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_SCRATCH_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballStartingPitcherScratchDigestConfig",
    "MarketResearchBaseballStartingPitcherScratchDigestInput",
    "MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount",
    "MarketResearchBaseballStartingPitcherScratchDigestRow",
    "MarketResearchBaseballStartingPitcherScratchDigestReport",
    "build_market_research_baseball_starting_pitcher_scratch_digest",
    "market_research_baseball_starting_pitcher_scratch_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherScratchDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_SCRATCH_DIGEST_CONFIG_VERSION
    )
    scratch_probability_watch_threshold: Decimal = Decimal("0.350000")
    lineup_confirmation_minute_threshold: Decimal = Decimal("90.000000")
    min_source_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "scratch_probability_watch_threshold",
            "lineup_confirmation_minute_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "scratch_probability_watch_threshold",
            _normalize_ratio_decimal(
                "scratch_probability_watch_threshold",
                self.scratch_probability_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "min_source_count",
            _normalize_positive_whole_decimal("min_source_count", self.min_source_count),
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherScratchDigestInput(_NoSubclass):
    pitcher_key: str
    pitcher_name: str
    team_key: str
    game_key: str
    observed_at: datetime
    scheduled_start_at: datetime
    scratch_probability: Decimal
    source_count: Decimal
    lineup_confirmed_at: datetime | None = None
    replacement_pitcher_key: str | None = None
    source_config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_STARTING_PITCHER_SCRATCH_DIGEST_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "pitcher_key",
            "pitcher_name",
            "team_key",
            "game_key",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        if self.lineup_confirmed_at is not None:
            object.__setattr__(
                self,
                "lineup_confirmed_at",
                _as_utc("lineup_confirmed_at", self.lineup_confirmed_at),
            )
        if self.replacement_pitcher_key is not None:
            _require_canonical_string(
                "replacement_pitcher_key",
                self.replacement_pitcher_key,
            )
        object.__setattr__(
            self,
            "scratch_probability",
            _normalize_ratio_decimal("scratch_probability", self.scratch_probability),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        _validate_input(self)
        _require_flags("input", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    pitcher_count: Decimal
    pitcher_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code, DIGEST_REASON_CODES)
        object.__setattr__(
            self,
            "pitcher_count",
            _normalize_nonnegative_whole_decimal("pitcher_count", self.pitcher_count),
        )
        object.__setattr__(
            self,
            "pitcher_ratio",
            _normalize_ratio_decimal("pitcher_ratio", self.pitcher_ratio),
        )
        _require_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherScratchDigestRow(_NoSubclass):
    pitcher_key: str
    pitcher_name: str
    team_key: str
    game_key: str
    observed_at: datetime
    scheduled_start_at: datetime
    minutes_until_start: Decimal
    scratch_probability: Decimal
    source_count: Decimal
    lineup_confirmed_at: datetime | None
    replacement_pitcher_key: str | None
    digest_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("pitcher_key", "pitcher_name", "team_key", "game_key"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "scheduled_start_at",
            _as_utc("scheduled_start_at", self.scheduled_start_at),
        )
        object.__setattr__(
            self,
            "minutes_until_start",
            _normalize_nonnegative_decimal(
                "minutes_until_start",
                self.minutes_until_start,
            ),
        )
        object.__setattr__(
            self,
            "scratch_probability",
            _normalize_ratio_decimal("scratch_probability", self.scratch_probability),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_nonnegative_whole_decimal("source_count", self.source_count),
        )
        if self.lineup_confirmed_at is not None:
            object.__setattr__(
                self,
                "lineup_confirmed_at",
                _as_utc("lineup_confirmed_at", self.lineup_confirmed_at),
            )
        if self.replacement_pitcher_key is not None:
            _require_canonical_string(
                "replacement_pitcher_key",
                self.replacement_pitcher_key,
            )
        _require_member("digest_status", self.digest_status, (CLEAR_STATUS, WATCH_STATUS))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballStartingPitcherScratchDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    pitcher_count: Decimal
    clear_pitcher_count: Decimal
    watch_pitcher_count: Decimal
    unconfirmed_pitcher_count: Decimal
    replacement_pitcher_count: Decimal
    thin_source_pitcher_count: Decimal
    high_scratch_probability_pitcher_count: Decimal
    scratch_probability_watch_threshold: Decimal
    lineup_confirmation_minute_threshold: Decimal
    min_source_count: Decimal
    max_scratch_probability: Decimal | None
    rows: tuple[MarketResearchBaseballStartingPitcherScratchDigestRow, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("digest_status", self.digest_status, (PASS_STATUS, WATCH_STATUS))
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "pitcher_count",
            "clear_pitcher_count",
            "watch_pitcher_count",
            "unconfirmed_pitcher_count",
            "replacement_pitcher_count",
            "thin_source_pitcher_count",
            "high_scratch_probability_pitcher_count",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "scratch_probability_watch_threshold",
            _normalize_ratio_decimal(
                "scratch_probability_watch_threshold",
                self.scratch_probability_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "lineup_confirmation_minute_threshold",
            _normalize_nonnegative_decimal(
                "lineup_confirmation_minute_threshold",
                self.lineup_confirmation_minute_threshold,
            ),
        )
        if self.max_scratch_probability is not None:
            object.__setattr__(
                self,
                "max_scratch_probability",
                _normalize_ratio_decimal(
                    "max_scratch_probability",
                    self.max_scratch_probability,
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                DIGEST_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_flags("report", self)


def build_market_research_baseball_starting_pitcher_scratch_digest(
    inputs: list[MarketResearchBaseballStartingPitcherScratchDigestInput]
    | tuple[MarketResearchBaseballStartingPitcherScratchDigestInput, ...],
    *,
    config: MarketResearchBaseballStartingPitcherScratchDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballStartingPitcherScratchDigestReport:
    if type(config) is not MarketResearchBaseballStartingPitcherScratchDigestConfig:
        raise ValueError(
            "config must be a MarketResearchBaseballStartingPitcherScratchDigestConfig",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    _reject_future_inputs(normalized, generated_at_utc)
    rows = _rows(normalized, config, generated_at_utc)
    pitcher_count = _decimal_count(len(rows))
    watch_count = _decimal_count(sum(1 for row in rows if row.digest_status == WATCH_STATUS))
    digest_status = WATCH_STATUS if watch_count > ZERO else PASS_STATUS
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                pitcher_count=ONE,
                pitcher_ratio=ZERO,
            ),
        )
        reason_codes = (EMPTY_REASON,)
    elif digest_status == PASS_STATUS:
        reason_codes = (PASSED_REASON,)

    return MarketResearchBaseballStartingPitcherScratchDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        pitcher_count=pitcher_count,
        clear_pitcher_count=_decimal_count(
            sum(1 for row in rows if row.digest_status == CLEAR_STATUS),
        ),
        watch_pitcher_count=watch_count,
        unconfirmed_pitcher_count=_reason_pitcher_count(rows, UNCONFIRMED_LINEUP_REASON),
        replacement_pitcher_count=_reason_pitcher_count(rows, REPLACEMENT_NAMED_REASON),
        thin_source_pitcher_count=_reason_pitcher_count(rows, THIN_SOURCES_REASON),
        high_scratch_probability_pitcher_count=_reason_pitcher_count(
            rows,
            HIGH_PROBABILITY_REASON,
        ),
        scratch_probability_watch_threshold=config.scratch_probability_watch_threshold,
        lineup_confirmation_minute_threshold=config.lineup_confirmation_minute_threshold,
        min_source_count=config.min_source_count,
        max_scratch_probability=_max_or_none(row.scratch_probability for row in rows),
        rows=rows,
        source_config_versions=_source_config_versions(normalized),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_baseball_starting_pitcher_scratch_digest_payload(
    report: MarketResearchBaseballStartingPitcherScratchDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchBaseballStartingPitcherScratchDigestReport:
        raise ValueError(
            "report must be a MarketResearchBaseballStartingPitcherScratchDigestReport",
        )
    _require_flags("report", report)
    return _payload_value(asdict(report))  # type: ignore[return-value]


def _normalize_inputs(
    inputs: list[MarketResearchBaseballStartingPitcherScratchDigestInput]
    | tuple[MarketResearchBaseballStartingPitcherScratchDigestInput, ...],
) -> tuple[MarketResearchBaseballStartingPitcherScratchDigestInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not MarketResearchBaseballStartingPitcherScratchDigestInput:
            raise ValueError(
                "inputs must contain MarketResearchBaseballStartingPitcherScratchDigestInput",
            )
        _require_flags("input", item)
        key = (item.pitcher_key, item.game_key)
        if key in seen:
            raise ValueError("inputs must not contain duplicate pitcher game values")
        seen.add(key)
    return normalized


def _reject_future_inputs(
    inputs: tuple[MarketResearchBaseballStartingPitcherScratchDigestInput, ...],
    generated_at: datetime,
) -> None:
    for item in inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows(
    inputs: tuple[MarketResearchBaseballStartingPitcherScratchDigestInput, ...],
    config: MarketResearchBaseballStartingPitcherScratchDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBaseballStartingPitcherScratchDigestRow, ...]:
    rows = tuple(_row_for_input(item, config, generated_at) for item in inputs)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_status_rank(row.digest_status),
                row.pitcher_key,
                row.team_key,
                row.game_key,
            ),
        )
    )


def _row_for_input(
    item: MarketResearchBaseballStartingPitcherScratchDigestInput,
    config: MarketResearchBaseballStartingPitcherScratchDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballStartingPitcherScratchDigestRow:
    minutes_until_start = _minutes_until_start(item.scheduled_start_at, generated_at)
    reason_codes = _row_reason_codes(
        scratch_probability=item.scratch_probability,
        source_count=item.source_count,
        lineup_confirmed_at=item.lineup_confirmed_at,
        replacement_pitcher_key=item.replacement_pitcher_key,
        minutes_until_start=minutes_until_start,
        config=config,
    )
    return MarketResearchBaseballStartingPitcherScratchDigestRow(
        pitcher_key=item.pitcher_key,
        pitcher_name=item.pitcher_name,
        team_key=item.team_key,
        game_key=item.game_key,
        observed_at=item.observed_at,
        scheduled_start_at=item.scheduled_start_at,
        minutes_until_start=minutes_until_start,
        scratch_probability=item.scratch_probability,
        source_count=item.source_count,
        lineup_confirmed_at=item.lineup_confirmed_at,
        replacement_pitcher_key=item.replacement_pitcher_key,
        digest_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    scratch_probability: Decimal,
    source_count: Decimal,
    lineup_confirmed_at: datetime | None,
    replacement_pitcher_key: str | None,
    minutes_until_start: Decimal,
    config: MarketResearchBaseballStartingPitcherScratchDigestConfig,
) -> tuple[str, ...]:
    reason_codes = []
    if scratch_probability >= config.scratch_probability_watch_threshold:
        reason_codes.append(HIGH_PROBABILITY_REASON)
    if lineup_confirmed_at is None:
        reason_codes.append(UNCONFIRMED_LINEUP_REASON)
    if replacement_pitcher_key is not None:
        reason_codes.append(REPLACEMENT_NAMED_REASON)
    if source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        return (CLEAR_REASON,)
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return CLEAR_STATUS
    return WATCH_STATUS


def _row_status_rank(status: str) -> int:
    if status == WATCH_STATUS:
        return 0
    return 1


def _reason_code_counts(
    rows: tuple[MarketResearchBaseballStartingPitcherScratchDigestRow, ...],
) -> tuple[MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code != CLEAR_REASON:
                counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(
            reason_code=reason_code,
            pitcher_count=_decimal_count(count),
            pitcher_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _reason_pitcher_count(
    rows: tuple[MarketResearchBaseballStartingPitcherScratchDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _source_config_versions(
    inputs: tuple[MarketResearchBaseballStartingPitcherScratchDigestInput, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            {
                (item.pitcher_key, item.source_config_version)
                for item in inputs
            }
        )
    )


def _minutes_until_start(scheduled_start_at: datetime, generated_at: datetime) -> Decimal:
    seconds = _seconds_between(generated_at, scheduled_start_at)
    if seconds <= ZERO:
        return ZERO
    return _six(seconds / SIXTY)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return _six(
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )


def _max_or_none(values: object) -> Decimal | None:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return None
    return _six(max(normalized))


def _validate_input(item: MarketResearchBaseballStartingPitcherScratchDigestInput) -> None:
    if item.scheduled_start_at < item.observed_at:
        raise ValueError("scheduled_start_at must not precede observed_at")
    if item.lineup_confirmed_at is not None and item.lineup_confirmed_at > item.scheduled_start_at:
        raise ValueError("lineup_confirmed_at must not exceed scheduled_start_at")


def _validate_row(row: MarketResearchBaseballStartingPitcherScratchDigestRow) -> None:
    if row.scheduled_start_at < row.observed_at:
        raise ValueError("scheduled_start_at must not precede observed_at")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchBaseballStartingPitcherScratchDigestReport) -> None:
    if report.pitcher_count != _decimal_count(len(report.rows)):
        raise ValueError("pitcher_count must match rows")
    if report.clear_pitcher_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_pitcher_count must match rows")
    if report.watch_pitcher_count != _decimal_count(
        sum(1 for row in report.rows if row.digest_status == WATCH_STATUS),
    ):
        raise ValueError("watch_pitcher_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    expected_reason_codes = tuple(item.reason_code for item in expected_reason_counts)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                pitcher_count=ONE,
                pitcher_ratio=ZERO,
            ),
        )
        expected_reason_codes = (EMPTY_REASON,)
    elif report.watch_pitcher_count == ZERO:
        expected_reason_codes = (PASSED_REASON,)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must summarize rows")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.digest_status != (WATCH_STATUS if report.watch_pitcher_count > ZERO else PASS_STATUS):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.unconfirmed_pitcher_count != _reason_pitcher_count(
        report.rows,
        UNCONFIRMED_LINEUP_REASON,
    ):
        raise ValueError("unconfirmed_pitcher_count must match rows")
    if report.replacement_pitcher_count != _reason_pitcher_count(
        report.rows,
        REPLACEMENT_NAMED_REASON,
    ):
        raise ValueError("replacement_pitcher_count must match rows")
    if report.thin_source_pitcher_count != _reason_pitcher_count(
        report.rows,
        THIN_SOURCES_REASON,
    ):
        raise ValueError("thin_source_pitcher_count must match rows")
    if report.high_scratch_probability_pitcher_count != _reason_pitcher_count(
        report.rows,
        HIGH_PROBABILITY_REASON,
    ):
        raise ValueError("high_scratch_probability_pitcher_count must match rows")
    if report.max_scratch_probability != _max_or_none(row.scratch_probability for row in report.rows):
        raise ValueError("max_scratch_probability must match rows")


def _normalize_rows(
    rows: tuple[MarketResearchBaseballStartingPitcherScratchDigestRow, ...],
) -> tuple[MarketResearchBaseballStartingPitcherScratchDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballStartingPitcherScratchDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBaseballStartingPitcherScratchDigestRow",
            )
        _require_flags("row", row)
        key = (row.pitcher_key, row.game_key)
        if key in seen:
            raise ValueError("rows must contain unique pitcher game values")
        seen.add(key)
    return rows


def _normalize_source_config_versions(
    versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(versions) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized = []
    seen: set[tuple[str, str]] = set()
    for item in versions:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions must contain pairs")
        pitcher_key, config_version = item
        _require_canonical_string("source_config_versions pitcher_key", pitcher_key)
        _require_canonical_string("source_config_versions config_version", config_version)
        pair = (pitcher_key, config_version)
        if pair in seen:
            raise ValueError("source_config_versions must contain unique pairs")
        seen.add(pair)
        normalized.append(pair)
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for count in counts:
        if type(count) is not MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballStartingPitcherScratchDigestReasonCodeCount",
            )
        _require_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen.add(count.reason_code)
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, known_reason_codes)
        if reason_code in seen:
            raise ValueError(f"{field_name} must contain unique reason codes")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _payload_value(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_reason_code(
    field_name: str,
    value: object,
    known_reason_codes: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in known_reason_codes:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = value.quantize(QUANTUM, rounding=ROUND_DOWN)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must have at most six decimal places") from exc
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return Decimal(int(normalized))


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _six(value: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal("value", value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_DOWN)


def _require_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
