"""Pure Phase 1 market source-family divergence health report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_HEALTH_REPORT_CONFIG_VERSION = (
    "market-source-family-divergence-health-report-v0"
)

HEALTH_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

PROBABILITY_DELTA_BLOCKED_REASON = "market_source_family_probability_delta_blocked"
PROBABILITY_DELTA_WATCH_REASON = "market_source_family_probability_delta_watch"
STALE_FAMILY_COVERAGE_REASON = "market_source_family_stale_family_coverage"
DOMINANT_FAMILY_BLOCKED_REASON = (
    "market_source_family_dominant_family_concentration_blocked"
)
DOMINANT_FAMILY_WATCH_REASON = (
    "market_source_family_dominant_family_concentration_watch"
)
CLEAR_REASON = "market_source_family_divergence_health_clear"
REASON_CODES = (
    PROBABILITY_DELTA_BLOCKED_REASON,
    PROBABILITY_DELTA_WATCH_REASON,
    STALE_FAMILY_COVERAGE_REASON,
    DOMINANT_FAMILY_BLOCKED_REASON,
    DOMINANT_FAMILY_WATCH_REASON,
    CLEAR_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("cred", "ential"),
        _join_parts("priv", "ate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ex", "change"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceHealthConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_HEALTH_REPORT_CONFIG_VERSION
    )
    watch_probability_delta: Decimal = Decimal("0.050000")
    blocked_probability_delta: Decimal = Decimal("0.150000")
    stale_family_after_seconds: Decimal = Decimal("7200.000000")
    dominant_family_watch_ratio: Decimal = Decimal("0.600000")
    dominant_family_blocked_ratio: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_probability_delta",
            _require_probability_delta(
                "watch_probability_delta",
                self.watch_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "blocked_probability_delta",
            _require_probability_delta(
                "blocked_probability_delta",
                self.blocked_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "stale_family_after_seconds",
            _require_positive_decimal(
                "stale_family_after_seconds",
                self.stale_family_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "dominant_family_watch_ratio",
            _require_ratio_decimal(
                "dominant_family_watch_ratio",
                self.dominant_family_watch_ratio,
            ),
        )
        object.__setattr__(
            self,
            "dominant_family_blocked_ratio",
            _require_ratio_decimal(
                "dominant_family_blocked_ratio",
                self.dominant_family_blocked_ratio,
            ),
        )
        if self.watch_probability_delta > self.blocked_probability_delta:
            raise ValueError(
                "watch_probability_delta must not exceed blocked_probability_delta",
            )
        if self.dominant_family_watch_ratio > self.dominant_family_blocked_ratio:
            raise ValueError(
                "dominant_family_watch_ratio must not exceed "
                "dominant_family_blocked_ratio",
            )
        require_paper_only_flags("market source family divergence health config", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceHealthInputRow:
    market_id: str
    research_input_id: str
    source_family: str
    probability: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("research_input_id", self.research_input_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "probability",
            _require_probability("probability", self.probability),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        reject_unsafe_surface_fields(
            "market source family divergence health input row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence health input row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceHealthMarketRow:
    market_id: str
    health_status: str
    reason_codes: tuple[str, ...]
    source_family_count: Decimal
    research_input_count: Decimal
    stale_family_count: Decimal
    disagreeing_family_count: Decimal
    dominant_source_family: str | None
    dominant_family_input_count: Decimal
    dominant_family_ratio: Decimal
    max_probability_delta: Decimal
    max_family_age_seconds: Decimal
    latest_observed_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_health_status("health_status", self.health_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "source_family_count",
            "research_input_count",
            "stale_family_count",
            "disagreeing_family_count",
            "dominant_family_input_count",
            "max_family_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dominant_family_ratio",
            _require_ratio_decimal(
                "dominant_family_ratio",
                self.dominant_family_ratio,
            ),
        )
        object.__setattr__(
            self,
            "max_probability_delta",
            _require_probability_delta(
                "max_probability_delta",
                self.max_probability_delta,
            ),
        )
        object.__setattr__(
            self,
            "dominant_source_family",
            _normalize_optional_public_string(
                "dominant_source_family",
                self.dominant_source_family,
            ),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        _validate_market_row(self)
        reject_unsafe_surface_fields(
            "market source family divergence health market row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence health market row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceHealthReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    source_family_count: Decimal
    research_input_count: Decimal
    clear_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    disagreement_market_count: Decimal
    stale_family_count: Decimal
    dominant_family_market_count: Decimal
    disagreement_market_ratio: Decimal
    stale_family_ratio: Decimal
    dominant_family_market_ratio: Decimal
    max_probability_delta: Decimal
    max_family_age_seconds: Decimal
    max_dominant_family_ratio: Decimal
    rows: tuple[MarketSourceFamilyDivergenceHealthMarketRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_health_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "source_family_count",
            "research_input_count",
            "clear_market_count",
            "watch_market_count",
            "blocked_market_count",
            "disagreement_market_count",
            "stale_family_count",
            "dominant_family_market_count",
            "max_family_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "disagreement_market_ratio",
            "stale_family_ratio",
            "dominant_family_market_ratio",
            "max_dominant_family_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_probability_delta",
            _require_probability_delta(
                "max_probability_delta",
                self.max_probability_delta,
            ),
        )
        object.__setattr__(self, "rows", _normalize_market_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market source family divergence health report",
            self,
        )
        require_paper_only_flags(
            "market source family divergence health report",
            self,
        )


def build_market_source_family_divergence_health_report(
    input_rows: list[MarketSourceFamilyDivergenceHealthInputRow]
    | tuple[MarketSourceFamilyDivergenceHealthInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceHealthConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceHealthReport:
    if type(config) is not MarketSourceFamilyDivergenceHealthConfig:
        raise ValueError("config must be a MarketSourceFamilyDivergenceHealthConfig")
    require_paper_only_flags("market source family divergence health config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)

    by_market: dict[str, list[MarketSourceFamilyDivergenceHealthInputRow]] = {}
    for row in rows:
        by_market.setdefault(row.market_id, []).append(row)

    market_rows = _sort_market_rows(
        tuple(
            _market_row(
                market_id,
                tuple(market_rows),
                config=config,
                generated_at=generated_at_utc,
            )
            for market_id, market_rows in sorted(by_market.items())
        ),
    )
    market_count = _count(len(market_rows))
    source_family_count = _sum_decimal(
        row.source_family_count for row in market_rows
    )
    research_input_count = _sum_decimal(
        row.research_input_count for row in market_rows
    )
    stale_family_count = _sum_decimal(row.stale_family_count for row in market_rows)
    dominant_family_market_count = _count(
        sum(
            1
            for row in market_rows
            if row.dominant_family_ratio >= config.dominant_family_watch_ratio
        ),
    )
    reason_codes = _report_reason_codes(market_rows)

    return MarketSourceFamilyDivergenceHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        market_count=market_count,
        source_family_count=source_family_count,
        research_input_count=research_input_count,
        clear_market_count=_status_count(market_rows, "clear"),
        watch_market_count=_status_count(market_rows, "watch"),
        blocked_market_count=_status_count(market_rows, "blocked"),
        disagreement_market_count=_disagreement_market_count(market_rows),
        stale_family_count=stale_family_count,
        dominant_family_market_count=dominant_family_market_count,
        disagreement_market_ratio=_ratio(
            _disagreement_market_count(market_rows),
            market_count,
        ),
        stale_family_ratio=_ratio(stale_family_count, source_family_count),
        dominant_family_market_ratio=_ratio(
            dominant_family_market_count,
            market_count,
        ),
        max_probability_delta=_max_decimal(
            tuple(row.max_probability_delta for row in market_rows),
        ),
        max_family_age_seconds=_max_decimal(
            tuple(row.max_family_age_seconds for row in market_rows),
        ),
        max_dominant_family_ratio=_max_decimal(
            tuple(row.dominant_family_ratio for row in market_rows),
        ),
        rows=market_rows,
    )


def market_source_family_divergence_health_report_payload(
    report: MarketSourceFamilyDivergenceHealthReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergenceHealthReport:
        raise ValueError("report must be a MarketSourceFamilyDivergenceHealthReport")
    require_paper_only_flags("market source family divergence health report", report)
    reject_unsafe_surface_fields(
        "market source family divergence health report",
        report,
    )
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report payload must be an object")
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketSourceFamilyDivergenceHealthInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen_input_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceHealthInputRow:
            raise ValueError(
                "input rows must contain MarketSourceFamilyDivergenceHealthInputRow "
                "values",
            )
        require_paper_only_flags(
            "market source family divergence health input row",
            row,
        )
        if row.research_input_id in seen_input_ids:
            raise ValueError("research_input_id values must be unique")
        seen_input_ids.add(row.research_input_id)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_id,
                row.source_family,
                row.observed_at,
                row.research_input_id,
            ),
        ),
    )


def _market_row(
    market_id: str,
    rows: tuple[MarketSourceFamilyDivergenceHealthInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceHealthConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceHealthMarketRow:
    latest_by_family = _latest_by_family(rows)
    family_count = _count(len(latest_by_family))
    input_count = _count(len(rows))
    latest_probabilities = tuple(row.probability for row in latest_by_family.values())
    max_probability_delta = _probability_delta(latest_probabilities)
    stale_family_count = _count(
        sum(
            1
            for row in latest_by_family.values()
            if _seconds_between(row.observed_at, generated_at)
            > config.stale_family_after_seconds
        ),
    )
    family_ages = tuple(
        _seconds_between(row.observed_at, generated_at)
        for row in latest_by_family.values()
    )
    dominant_family, dominant_family_input_count = _dominant_family(rows)
    dominant_family_ratio = _ratio(_count(dominant_family_input_count), input_count)
    reason_codes = _market_reason_codes(
        max_probability_delta=max_probability_delta,
        stale_family_count=stale_family_count,
        dominant_family_ratio=dominant_family_ratio,
        config=config,
    )

    return MarketSourceFamilyDivergenceHealthMarketRow(
        market_id=market_id,
        health_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        source_family_count=family_count,
        research_input_count=input_count,
        stale_family_count=stale_family_count,
        disagreeing_family_count=_disagreeing_family_count(
            latest_probabilities,
            max_probability_delta=max_probability_delta,
            config=config,
        ),
        dominant_source_family=dominant_family,
        dominant_family_input_count=_count(dominant_family_input_count),
        dominant_family_ratio=dominant_family_ratio,
        max_probability_delta=max_probability_delta,
        max_family_age_seconds=_max_decimal(family_ages),
        latest_observed_at=_latest_observed_at(rows),
    )


def _latest_by_family(
    rows: tuple[MarketSourceFamilyDivergenceHealthInputRow, ...],
) -> dict[str, MarketSourceFamilyDivergenceHealthInputRow]:
    latest: dict[str, MarketSourceFamilyDivergenceHealthInputRow] = {}
    for row in rows:
        current = latest[row.source_family] if row.source_family in latest else None
        if current is None or (row.observed_at, row.research_input_id) > (
            current.observed_at,
            current.research_input_id,
        ):
            latest[row.source_family] = row
    return dict(sorted(latest.items()))


def _dominant_family(
    rows: tuple[MarketSourceFamilyDivergenceHealthInputRow, ...],
) -> tuple[str | None, int]:
    if not rows:
        return None, 0
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.source_family] = (
            counts[row.source_family] + 1 if row.source_family in counts else 1
        )
    family, count = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0]
    return family, count


def _latest_observed_at(
    rows: tuple[MarketSourceFamilyDivergenceHealthInputRow, ...],
) -> datetime | None:
    if not rows:
        return None
    return max(row.observed_at for row in rows)


def _probability_delta(values: tuple[Decimal, ...]) -> Decimal:
    if len(values) < 2:
        return ZERO
    return (max(values) - min(values)).quantize(QUANT)


def _market_reason_codes(
    *,
    max_probability_delta: Decimal,
    stale_family_count: Decimal,
    dominant_family_ratio: Decimal,
    config: MarketSourceFamilyDivergenceHealthConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if max_probability_delta > config.blocked_probability_delta:
        codes.append(PROBABILITY_DELTA_BLOCKED_REASON)
    elif max_probability_delta > config.watch_probability_delta:
        codes.append(PROBABILITY_DELTA_WATCH_REASON)
    if stale_family_count > ZERO:
        codes.append(STALE_FAMILY_COVERAGE_REASON)
    if dominant_family_ratio >= config.dominant_family_blocked_ratio:
        codes.append(DOMINANT_FAMILY_BLOCKED_REASON)
    elif dominant_family_ratio >= config.dominant_family_watch_ratio:
        codes.append(DOMINANT_FAMILY_WATCH_REASON)
    if not codes:
        codes.append(CLEAR_REASON)
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergenceHealthMarketRow, ...],
) -> tuple[str, ...]:
    codes: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            codes.append(reason_code)
    if not codes:
        codes.append(CLEAR_REASON)
    return tuple(codes)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        PROBABILITY_DELTA_BLOCKED_REASON in reason_codes
        or DOMINANT_FAMILY_BLOCKED_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (CLEAR_REASON,):
        return "clear"
    return "watch"


def _disagreeing_family_count(
    latest_probabilities: tuple[Decimal, ...],
    *,
    max_probability_delta: Decimal,
    config: MarketSourceFamilyDivergenceHealthConfig,
) -> Decimal:
    if max_probability_delta <= config.watch_probability_delta:
        return ZERO
    return _count(len(latest_probabilities))


def _sort_market_rows(
    rows: tuple[MarketSourceFamilyDivergenceHealthMarketRow, ...],
) -> tuple[MarketSourceFamilyDivergenceHealthMarketRow, ...]:
    return tuple(sorted(rows, key=_market_row_sort_key))


def _market_row_sort_key(
    row: MarketSourceFamilyDivergenceHealthMarketRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.health_status],
        -row.max_probability_delta,
        -row.dominant_family_ratio,
        -row.stale_family_count,
        row.market_id,
    )


def _normalize_market_rows(
    value: object,
) -> tuple[MarketSourceFamilyDivergenceHealthMarketRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceHealthMarketRow:
            raise ValueError(
                "rows must contain MarketSourceFamilyDivergenceHealthMarketRow values",
            )
        require_paper_only_flags(
            "market source family divergence health market row",
            row,
        )
        if row.market_id in seen_market_ids:
            raise ValueError("rows must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
    if rows != _sort_market_rows(rows):
        raise ValueError("rows must use deterministic sort")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _validate_market_row(row: MarketSourceFamilyDivergenceHealthMarketRow) -> None:
    if row.source_family_count > row.research_input_count:
        raise ValueError("source_family_count must not exceed research_input_count")
    if row.stale_family_count > row.source_family_count:
        raise ValueError("stale_family_count must not exceed source_family_count")
    if row.disagreeing_family_count > row.source_family_count:
        raise ValueError(
            "disagreeing_family_count must not exceed source_family_count",
        )
    if row.dominant_family_input_count > row.research_input_count:
        raise ValueError(
            "dominant_family_input_count must not exceed research_input_count",
        )
    if row.research_input_count == ZERO:
        if row.dominant_source_family is not None:
            raise ValueError("dominant_source_family must be empty without inputs")
        if row.latest_observed_at is not None:
            raise ValueError("latest_observed_at must be empty without inputs")
    else:
        if row.dominant_source_family is None:
            raise ValueError("dominant_source_family is required with inputs")
        if row.latest_observed_at is None:
            raise ValueError("latest_observed_at is required with inputs")
    if row.health_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("health_status must match reason_codes")


def _validate_report(report: MarketSourceFamilyDivergenceHealthReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.source_family_count != _sum_decimal(
        row.source_family_count for row in report.rows
    ):
        raise ValueError("source_family_count must match rows")
    if report.research_input_count != _sum_decimal(
        row.research_input_count for row in report.rows
    ):
        raise ValueError("research_input_count must match rows")
    if report.clear_market_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_market_count must match rows")
    if report.watch_market_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.blocked_market_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    if (
        report.clear_market_count
        + report.watch_market_count
        + report.blocked_market_count
        != report.market_count
    ):
        raise ValueError("status counts must sum to market_count")
    if report.disagreement_market_count != _disagreement_market_count(report.rows):
        raise ValueError("disagreement_market_count must match rows")
    if report.stale_family_count != _sum_decimal(
        row.stale_family_count for row in report.rows
    ):
        raise ValueError("stale_family_count must match rows")
    if report.dominant_family_market_count != _count(
        sum(
            1
            for row in report.rows
            if (
                DOMINANT_FAMILY_BLOCKED_REASON in row.reason_codes
                or DOMINANT_FAMILY_WATCH_REASON in row.reason_codes
            )
        ),
    ):
        raise ValueError("dominant_family_market_count must match rows")
    if report.disagreement_market_ratio != _ratio(
        report.disagreement_market_count,
        report.market_count,
    ):
        raise ValueError("disagreement_market_ratio must match rows")
    if report.stale_family_ratio != _ratio(
        report.stale_family_count,
        report.source_family_count,
    ):
        raise ValueError("stale_family_ratio must match rows")
    if report.dominant_family_market_ratio != _ratio(
        report.dominant_family_market_count,
        report.market_count,
    ):
        raise ValueError("dominant_family_market_ratio must match rows")
    if report.max_probability_delta != _max_decimal(
        tuple(row.max_probability_delta for row in report.rows),
    ):
        raise ValueError("max_probability_delta must match rows")
    if report.max_family_age_seconds != _max_decimal(
        tuple(row.max_family_age_seconds for row in report.rows),
    ):
        raise ValueError("max_family_age_seconds must match rows")
    if report.max_dominant_family_ratio != _max_decimal(
        tuple(row.dominant_family_ratio for row in report.rows),
    ):
        raise ValueError("max_dominant_family_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _status_count(
    rows: tuple[MarketSourceFamilyDivergenceHealthMarketRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.health_status == status))


def _disagreement_market_count(
    rows: tuple[MarketSourceFamilyDivergenceHealthMarketRow, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if (
                PROBABILITY_DELTA_BLOCKED_REASON in row.reason_codes
                or PROBABILITY_DELTA_WATCH_REASON in row.reason_codes
            )
        ),
    )


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return total.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("observed_at must not be after generated_at")
    delta = end - start
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return age_seconds.quantize(QUANT)


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_HEALTH_REPORT_CONFIG_VERSION",
    "HEALTH_STATUSES",
    "REASON_CODES",
    "MarketSourceFamilyDivergenceHealthConfig",
    "MarketSourceFamilyDivergenceHealthInputRow",
    "MarketSourceFamilyDivergenceHealthMarketRow",
    "MarketSourceFamilyDivergenceHealthReport",
    "build_market_source_family_divergence_health_report",
    "market_source_family_divergence_health_report_payload",
)
