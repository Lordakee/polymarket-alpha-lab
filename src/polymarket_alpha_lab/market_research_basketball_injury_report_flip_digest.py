"""Pure Phase 1 reducer for basketball injury report flip research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


DEFAULT_MARKET_RESEARCH_BASKETBALL_INJURY_REPORT_FLIP_DIGEST_CONFIG_VERSION = (
    "market-research-basketball-injury-report-flip-digest-v0"
)
BASKETBALL_INJURY_REPORT_FLIP_RESEARCH_SCOPE = (
    "basketball injury report flip research digest only"
)

SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REPORT_STATUSES = (
    "available",
    "probable",
    "questionable",
    "doubtful",
    "out",
)
REPORT_STATUS_RANKS = {
    "available": Decimal("0.000000"),
    "probable": Decimal("1.000000"),
    "questionable": Decimal("2.000000"),
    "doubtful": Decimal("3.000000"),
    "out": Decimal("4.000000"),
}

STATUS_DOWNGRADE_REASON = (
    "market_research_basketball_injury_report_flip_digest_status_downgrade"
)
MATERIAL_FLIP_REASON = (
    "market_research_basketball_injury_report_flip_digest_material_probability_flip"
)
HIGH_PLAYER_IMPACT_REASON = (
    "market_research_basketball_injury_report_flip_digest_high_player_impact"
)
LIQUIDITY_GAP_REASON = (
    "market_research_basketball_injury_report_flip_digest_liquidity_gap"
)
READY_REASON = "market_research_basketball_injury_report_flip_digest_ready"
SOURCE_GAP_REASON = "market_research_basketball_injury_report_flip_digest_source_gap"
STALE_REPORT_REASON = "market_research_basketball_injury_report_flip_digest_stale_report"
NO_INPUTS_REASON = "market_research_basketball_injury_report_flip_digest_no_inputs"

REASON_CODES = (
    STATUS_DOWNGRADE_REASON,
    MATERIAL_FLIP_REASON,
    HIGH_PLAYER_IMPACT_REASON,
    LIQUIDITY_GAP_REASON,
    READY_REASON,
    SOURCE_GAP_REASON,
    STALE_REPORT_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEP_BY_STATUS = {
    STATUS_READY: "allow_report_only_basketball_injury_report_flip_research",
    STATUS_WATCH: "watch_report_only_basketball_injury_report_flip_research",
    STATUS_BLOCKED: "block_report_only_basketball_injury_report_flip_research",
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("or", "der"),
        _join_parts("rep", "lace"),
        _join_parts("ex", "change"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "-", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("api", "key"),
        _join_parts("ke", "y="),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASKETBALL_INJURY_REPORT_FLIP_DIGEST_CONFIG_VERSION",
    "BASKETBALL_INJURY_REPORT_FLIP_RESEARCH_SCOPE",
    "MarketResearchBasketballInjuryReportFlipDigestConfig",
    "MarketResearchBasketballInjuryReportFlipDigestItem",
    "MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount",
    "MarketResearchBasketballInjuryReportFlipDigestRow",
    "MarketResearchBasketballInjuryReportFlipDigestReport",
    "build_market_research_basketball_injury_report_flip_digest",
    "market_research_basketball_injury_report_flip_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchBasketballInjuryReportFlipDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_INJURY_REPORT_FLIP_DIGEST_CONFIG_VERSION
    )
    max_report_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    material_flip_threshold: Decimal = Decimal("0.250000")
    high_player_impact_threshold: Decimal = Decimal("0.750000")
    min_market_liquidity_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_report_age_seconds",
            "min_source_count",
            "min_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_flip_threshold",
            "high_player_impact_threshold",
            "min_market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_report_age_seconds <= ZERO:
            raise ValueError("max_report_age_seconds must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBasketballInjuryReportFlipDigestItem(_NoSubclass):
    condition_id: str
    basketball_event_key: str
    league_key: str
    team_key: str
    opponent_key: str
    player_key: str
    injury_key: str
    previous_report_status: str
    current_report_status: str
    public_report_reference: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    previous_availability_probability: Decimal
    current_availability_probability: Decimal
    player_impact_score: Decimal
    market_liquidity_score: Decimal
    item_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "basketball_event_key",
            "league_key",
            "team_key",
            "opponent_key",
            "player_key",
            "injury_key",
            "item_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_report_status("previous_report_status", self.previous_report_status)
        _require_report_status("current_report_status", self.current_report_status)
        _require_public_reference("public_report_reference", self.public_report_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("source_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "previous_availability_probability",
            "current_availability_probability",
            "player_impact_score",
            "market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    item_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "item_ratio",
            _require_ratio_decimal("item_ratio", self.item_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchBasketballInjuryReportFlipDigestRow(_NoSubclass):
    condition_id: str
    basketball_event_key: str
    league_key: str
    team_key: str
    opponent_key: str
    player_key: str
    injury_key: str
    previous_report_status: str
    current_report_status: str
    digest_status: str
    observed_at: datetime
    report_age_seconds: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    source_diversity_ratio: Decimal
    previous_availability_probability: Decimal
    current_availability_probability: Decimal
    availability_probability_delta: Decimal
    status_rank_delta: Decimal
    player_impact_score: Decimal
    market_liquidity_score: Decimal
    redacted_public_report_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "basketball_event_key",
            "league_key",
            "team_key",
            "opponent_key",
            "player_key",
            "injury_key",
            "redacted_public_report_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_report_status("previous_report_status", self.previous_report_status)
        _require_report_status("current_report_status", self.current_report_status)
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "report_age_seconds",
            "source_count",
            "independent_source_count",
            "availability_probability_delta",
            "status_rank_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_diversity_ratio",
            "previous_availability_probability",
            "current_availability_probability",
            "player_impact_score",
            "market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketResearchBasketballInjuryReportFlipDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    research_scope: str
    digest_status: str
    recommended_next_step: str
    item_count: Decimal
    ready_item_count: Decimal
    watch_item_count: Decimal
    blocked_item_count: Decimal
    status_downgrade_item_count: Decimal
    material_flip_item_count: Decimal
    high_player_impact_item_count: Decimal
    liquidity_gap_item_count: Decimal
    source_gap_item_count: Decimal
    stale_report_item_count: Decimal
    max_report_age_seconds: Decimal
    min_source_count: Decimal
    min_independent_source_count: Decimal
    material_flip_threshold: Decimal
    high_player_impact_threshold: Decimal
    min_market_liquidity_score: Decimal
    max_report_age_seconds_observed: Decimal
    max_availability_probability_delta: Decimal
    average_availability_probability_delta: Decimal
    rows: tuple[MarketResearchBasketballInjuryReportFlipDigestRow, ...]
    item_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.research_scope != BASKETBALL_INJURY_REPORT_FLIP_RESEARCH_SCOPE:
            raise ValueError("research_scope must match basketball injury report flip scope")
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "item_count",
            "ready_item_count",
            "watch_item_count",
            "blocked_item_count",
            "status_downgrade_item_count",
            "material_flip_item_count",
            "high_player_impact_item_count",
            "liquidity_gap_item_count",
            "source_gap_item_count",
            "stale_report_item_count",
            "max_report_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "max_report_age_seconds_observed",
            "max_availability_probability_delta",
            "average_availability_probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_flip_threshold",
            "high_player_impact_threshold",
            "min_market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "item_config_versions",
            _normalize_item_config_versions(self.item_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_market_research_basketball_injury_report_flip_digest(
    items: Iterable[MarketResearchBasketballInjuryReportFlipDigestItem],
    *,
    config: MarketResearchBasketballInjuryReportFlipDigestConfig,
    generated_at: datetime,
) -> MarketResearchBasketballInjuryReportFlipDigestReport:
    if type(config) is not MarketResearchBasketballInjuryReportFlipDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchBasketballInjuryReportFlipDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = _rows(normalized_items, config=config, generated_at=generated_at_utc)
    item_count = _decimal_count(len(rows))
    ready_item_count = _item_count_with_status(rows, STATUS_READY)
    watch_item_count = _item_count_with_status(rows, STATUS_WATCH)
    blocked_item_count = _item_count_with_status(rows, STATUS_BLOCKED)
    digest_status = _report_status(
        item_count=item_count,
        watch_item_count=watch_item_count,
        blocked_item_count=blocked_item_count,
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    return MarketResearchBasketballInjuryReportFlipDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        research_scope=BASKETBALL_INJURY_REPORT_FLIP_RESEARCH_SCOPE,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[digest_status],
        item_count=item_count,
        ready_item_count=ready_item_count,
        watch_item_count=watch_item_count,
        blocked_item_count=blocked_item_count,
        status_downgrade_item_count=_item_count_with_reason(
            rows,
            STATUS_DOWNGRADE_REASON,
        ),
        material_flip_item_count=_item_count_with_reason(rows, MATERIAL_FLIP_REASON),
        high_player_impact_item_count=_item_count_with_reason(
            rows,
            HIGH_PLAYER_IMPACT_REASON,
        ),
        liquidity_gap_item_count=_item_count_with_reason(rows, LIQUIDITY_GAP_REASON),
        source_gap_item_count=_item_count_with_reason(rows, SOURCE_GAP_REASON),
        stale_report_item_count=_item_count_with_reason(rows, STALE_REPORT_REASON),
        max_report_age_seconds=_six(config.max_report_age_seconds),
        min_source_count=_six(config.min_source_count),
        min_independent_source_count=_six(config.min_independent_source_count),
        material_flip_threshold=_six(config.material_flip_threshold),
        high_player_impact_threshold=_six(config.high_player_impact_threshold),
        min_market_liquidity_score=_six(config.min_market_liquidity_score),
        max_report_age_seconds_observed=_max_decimal(
            row.report_age_seconds for row in rows
        ),
        max_availability_probability_delta=_max_decimal(
            row.availability_probability_delta for row in rows
        ),
        average_availability_probability_delta=_ratio(
            _sum_decimal(row.availability_probability_delta for row in rows),
            item_count,
        ),
        rows=rows,
        item_config_versions=_item_config_versions(normalized_items),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_basketball_injury_report_flip_digest_payload(
    report: MarketResearchBasketballInjuryReportFlipDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBasketballInjuryReportFlipDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchBasketballInjuryReportFlipDigestReport",
        )
    _require_hard_flags("report", report)
    value = _to_plain(report)
    if type(value) is not dict:
        raise ValueError("report output must be a dict")
    return value


def _normalize_items(
    items: Iterable[MarketResearchBasketballInjuryReportFlipDigestItem],
) -> tuple[MarketResearchBasketballInjuryReportFlipDigestItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must contain basketball injury report flip records")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must contain basketball injury report flip records") from exc
    seen_event_keys: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchBasketballInjuryReportFlipDigestItem:
            raise ValueError(
                "items must contain MarketResearchBasketballInjuryReportFlipDigestItem",
            )
        _require_hard_flags("item", item)
        if item.basketball_event_key in seen_event_keys:
            raise ValueError("basketball_event_key values must be unique")
        seen_event_keys.add(item.basketball_event_key)
    return normalized


def _rows(
    items: tuple[MarketResearchBasketballInjuryReportFlipDigestItem, ...],
    *,
    config: MarketResearchBasketballInjuryReportFlipDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchBasketballInjuryReportFlipDigestRow, ...]:
    built_rows = []
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        report_age_seconds = _age_seconds(generated_at, item.observed_at)
        availability_probability_delta = _absolute_decimal(
            item.current_availability_probability
            - item.previous_availability_probability,
        )
        status_rank_delta = _absolute_decimal(
            REPORT_STATUS_RANKS[item.current_report_status]
            - REPORT_STATUS_RANKS[item.previous_report_status],
        )
        reason_codes = _row_reason_codes(
            item=item,
            config=config,
            report_age_seconds=report_age_seconds,
            availability_probability_delta=availability_probability_delta,
        )
        built_rows.append(
            MarketResearchBasketballInjuryReportFlipDigestRow(
                condition_id=item.condition_id,
                basketball_event_key=item.basketball_event_key,
                league_key=item.league_key,
                team_key=item.team_key,
                opponent_key=item.opponent_key,
                player_key=item.player_key,
                injury_key=item.injury_key,
                previous_report_status=item.previous_report_status,
                current_report_status=item.current_report_status,
                digest_status=_row_status(reason_codes),
                observed_at=item.observed_at,
                report_age_seconds=report_age_seconds,
                source_count=_six(item.source_count),
                independent_source_count=_six(item.independent_source_count),
                source_diversity_ratio=_ratio(
                    item.independent_source_count,
                    item.source_count,
                ),
                previous_availability_probability=_six(
                    item.previous_availability_probability,
                ),
                current_availability_probability=_six(
                    item.current_availability_probability,
                ),
                availability_probability_delta=availability_probability_delta,
                status_rank_delta=status_rank_delta,
                player_impact_score=_six(item.player_impact_score),
                market_liquidity_score=_six(item.market_liquidity_score),
                redacted_public_report_reference=item.public_report_reference,
                reason_codes=reason_codes,
            )
        )
    return tuple(sorted(built_rows, key=_row_sort_key))


def _row_reason_codes(
    *,
    item: MarketResearchBasketballInjuryReportFlipDigestItem,
    config: MarketResearchBasketballInjuryReportFlipDigestConfig,
    report_age_seconds: Decimal,
    availability_probability_delta: Decimal,
) -> tuple[str, ...]:
    reason_codes = []
    if REPORT_STATUS_RANKS[item.current_report_status] > REPORT_STATUS_RANKS[
        item.previous_report_status
    ]:
        reason_codes.append(STATUS_DOWNGRADE_REASON)
    if availability_probability_delta >= config.material_flip_threshold:
        reason_codes.append(MATERIAL_FLIP_REASON)
    if item.player_impact_score >= config.high_player_impact_threshold:
        reason_codes.append(HIGH_PLAYER_IMPACT_REASON)
    if item.market_liquidity_score < config.min_market_liquidity_score:
        reason_codes.append(LIQUIDITY_GAP_REASON)
    if (
        item.source_count < config.min_source_count
        or item.independent_source_count < config.min_independent_source_count
    ):
        reason_codes.append(SOURCE_GAP_REASON)
    if report_age_seconds > config.max_report_age_seconds:
        reason_codes.append(STALE_REPORT_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if SOURCE_GAP_REASON in reason_codes or STALE_REPORT_REASON in reason_codes:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(
    *,
    item_count: Decimal,
    watch_item_count: Decimal,
    blocked_item_count: Decimal,
) -> str:
    if item_count == ZERO:
        return STATUS_BLOCKED
    if blocked_item_count > ZERO:
        return STATUS_BLOCKED
    if watch_item_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _reason_code_counts(
    rows: tuple[MarketResearchBasketballInjuryReportFlipDigestRow, ...],
) -> tuple[MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    item_count = _decimal_count(len(rows))
    return tuple(
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            item_ratio=_ratio(_decimal_count(counts[reason_code]), item_count),
        )
        for reason_code in REASON_CODES
        if reason_code in counts
    )


def _item_config_versions(
    items: tuple[MarketResearchBasketballInjuryReportFlipDigestItem, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (item.basketball_event_key, item.item_config_version)
            for item in items
        )
    )


def _item_count_with_status(
    rows: tuple[MarketResearchBasketballInjuryReportFlipDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.digest_status == status))


def _item_count_with_reason(
    rows: tuple[MarketResearchBasketballInjuryReportFlipDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_rows(
    rows: tuple[MarketResearchBasketballInjuryReportFlipDigestRow, ...],
) -> tuple[MarketResearchBasketballInjuryReportFlipDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchBasketballInjuryReportFlipDigestRow:
            raise ValueError(
                "rows must contain MarketResearchBasketballInjuryReportFlipDigestRow",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_item_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("item_config_versions must be a tuple")
    normalized = []
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("item_config_versions must contain pairs")
        basketball_event_key, item_config_version = value
        _require_canonical_string("basketball_event_key", basketball_event_key)
        _require_canonical_string("item_config_version", item_config_version)
        normalized.append((basketball_event_key, item_config_version))
    if tuple(normalized) != tuple(sorted(normalized)):
        raise ValueError("item_config_versions must be sorted")
    return tuple(normalized)


def _normalize_reason_code_counts(
    values: tuple[MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount, ...],
) -> tuple[MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
    if values != tuple(sorted(values, key=lambda value: REASON_CODES.index(value.reason_code))):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return values


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)


def _row_sort_key(
    row: MarketResearchBasketballInjuryReportFlipDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        _status_rank(row.digest_status),
        -row.availability_probability_delta,
        -row.status_rank_delta,
        row.basketball_event_key,
        row.condition_id,
    )


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCKED:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _validate_row_consistency(
    row: MarketResearchBasketballInjuryReportFlipDigestRow,
) -> None:
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    expected_status_rank_delta = _absolute_decimal(
        REPORT_STATUS_RANKS[row.current_report_status]
        - REPORT_STATUS_RANKS[row.previous_report_status],
    )
    if row.status_rank_delta != expected_status_rank_delta:
        raise ValueError("status_rank_delta must match statuses")
    expected_probability_delta = _absolute_decimal(
        row.current_availability_probability - row.previous_availability_probability,
    )
    if row.availability_probability_delta != expected_probability_delta:
        raise ValueError("availability_probability_delta must match probabilities")
    if row.source_diversity_ratio != _ratio(
        row.independent_source_count,
        row.source_count,
    ):
        raise ValueError("source_diversity_ratio must match sources")
    if row.reason_codes == (NO_INPUTS_REASON,):
        raise ValueError("reason_codes cannot contain no inputs for a row")


def _validate_report_consistency(
    report: MarketResearchBasketballInjuryReportFlipDigestReport,
) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.ready_item_count != _item_count_with_status(report.rows, STATUS_READY):
        raise ValueError("ready_item_count must match rows")
    if report.watch_item_count != _item_count_with_status(report.rows, STATUS_WATCH):
        raise ValueError("watch_item_count must match rows")
    if report.blocked_item_count != _item_count_with_status(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_item_count must match rows")
    reason_fields = (
        (
            report.status_downgrade_item_count,
            STATUS_DOWNGRADE_REASON,
            "status_downgrade_item_count",
        ),
        (
            report.material_flip_item_count,
            MATERIAL_FLIP_REASON,
            "material_flip_item_count",
        ),
        (
            report.high_player_impact_item_count,
            HIGH_PLAYER_IMPACT_REASON,
            "high_player_impact_item_count",
        ),
        (
            report.liquidity_gap_item_count,
            LIQUIDITY_GAP_REASON,
            "liquidity_gap_item_count",
        ),
        (report.source_gap_item_count, SOURCE_GAP_REASON, "source_gap_item_count"),
        (
            report.stale_report_item_count,
            STALE_REPORT_REASON,
            "stale_report_item_count",
        ),
    )
    for actual_count, reason_code, field_name in reason_fields:
        if actual_count != _item_count_with_reason(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if report.rows:
        if report.reason_code_counts != expected_reason_code_counts:
            raise ValueError("reason_code_counts must summarize rows")
        expected_reason_codes = tuple(item.reason_code for item in expected_reason_code_counts)
    else:
        expected_reason_code_counts = (
            MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
        if report.reason_code_counts != expected_reason_code_counts:
            raise ValueError("reason_code_counts must summarize no inputs")
        expected_reason_codes = (NO_INPUTS_REASON,)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        item_count=report.item_count,
        watch_item_count=report.watch_item_count,
        blocked_item_count=report.blocked_item_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.max_report_age_seconds_observed != _max_decimal(
        row.report_age_seconds for row in report.rows
    ):
        raise ValueError("max_report_age_seconds_observed must match rows")
    if report.max_availability_probability_delta != _max_decimal(
        row.availability_probability_delta for row in report.rows
    ):
        raise ValueError("max_availability_probability_delta must match rows")
    if report.average_availability_probability_delta != _ratio(
        _sum_decimal(row.availability_probability_delta for row in report.rows),
        report.item_count,
    ):
        raise ValueError("average_availability_probability_delta must match rows")


def _require_report_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a known injury report status")


def _require_digest_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")


def _require_public_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe text")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _six(decimal_value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    return _six(Decimal(str((generated_at - observed_at).total_seconds())))


def _decimal_count(value: int) -> Decimal:
    return _six(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _six(total)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return _six(max(values, default=ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _six(numerator / denominator)


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _six(-value)
    return _six(value)


def _six(value: Decimal) -> Decimal:
    try:
        return value.quantize(SIX_PLACES)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must fit six decimal places") from exc


def _to_plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return f"{text[:-6]}Z"
        return text
    if is_dataclass(value):
        return {field.name: _to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    return value
