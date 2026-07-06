"""Pure typed market cluster correlation v6 report reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_STRATEGY_MARKET_CLUSTER_CORRELATION_V6_CONFIG_VERSION = (
    "strategy-market-cluster-correlation-v6"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(VALUE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

CATEGORY_OVERLAP_SCORE = Decimal("0.100000")
EVENT_CLUSTER_OVERLAP_SCORE = Decimal("0.150000")
TEAM_OVERLAP_SCORE = Decimal("0.100000")
SHARED_SOURCES_OVERLAP_SCORE = Decimal("0.200000")

EMPTY_REASON_CODE = "market_cluster_correlation_v6_empty"
CLEAR_REASON_CODE = "market_cluster_correlation_clear"
ROW_REASON_CODES = (
    "category_overlap",
    CLEAR_REASON_CODE,
    "event_cluster_overlap",
    "probability_co_movement_blocked",
    "probability_co_movement_watch",
    "shared_sources_overlap",
    "team_overlap",
)
REPORT_REASON_CODES = tuple(sorted((*ROW_REASON_CODES, EMPTY_REASON_CODE)))


@dataclass(frozen=True)
class StrategyMarketClusterCorrelationV6Config:
    config_version: str = DEFAULT_STRATEGY_MARKET_CLUSTER_CORRELATION_V6_CONFIG_VERSION
    correlation_watch_score: Decimal = Decimal("0.450000")
    correlation_block_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "correlation_watch_score",
            _normalize_probability(
                "correlation_watch_score",
                self.correlation_watch_score,
            ),
        )
        object.__setattr__(
            self,
            "correlation_block_score",
            _normalize_probability(
                "correlation_block_score",
                self.correlation_block_score,
            ),
        )
        if self.correlation_watch_score > self.correlation_block_score:
            raise ValueError(
                "correlation_watch_score must not exceed correlation_block_score",
            )
        require_paper_only_flags("StrategyMarketClusterCorrelationV6Config", self)


@dataclass(frozen=True)
class StrategyMarketClusterCorrelationV6Market:
    market_slug: str
    category: str
    event_cluster: str
    team: str
    shared_sources: tuple[str, ...]
    probability_co_movement: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_slug",
            "category",
            "event_cluster",
            "team",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "shared_sources",
            _normalize_shared_sources("shared_sources", self.shared_sources),
        )
        object.__setattr__(
            self,
            "probability_co_movement",
            _normalize_probability(
                "probability_co_movement",
                self.probability_co_movement,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        require_paper_only_flags("StrategyMarketClusterCorrelationV6Market", self)


@dataclass(frozen=True)
class StrategyMarketClusterCorrelationV6Row:
    rank: Decimal
    market_slug: str
    category: str
    event_cluster: str
    team: str
    correlation_cluster: str
    shared_sources: tuple[str, ...]
    observed_at: datetime
    probability_co_movement: Decimal
    category_peer_count: Decimal
    event_cluster_peer_count: Decimal
    team_peer_count: Decimal
    shared_source_peer_count: Decimal
    correlation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        for field_name in (
            "market_slug",
            "category",
            "event_cluster",
            "team",
            "correlation_cluster",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "shared_sources",
            _normalize_shared_sources("shared_sources", self.shared_sources),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_co_movement",
            _normalize_probability(
                "probability_co_movement",
                self.probability_co_movement,
            ),
        )
        for field_name in (
            "category_peer_count",
            "event_cluster_peer_count",
            "team_peer_count",
            "shared_source_peer_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "correlation_score",
            _normalize_probability("correlation_score", self.correlation_score),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("StrategyMarketClusterCorrelationV6Row", self)


@dataclass(frozen=True)
class StrategyMarketClusterCorrelationV6Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    correlation_cluster_count: Decimal
    max_correlation_score: Decimal
    blocked_market_count: Decimal
    watch_market_count: Decimal
    pass_market_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyMarketClusterCorrelationV6Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "correlation_cluster_count",
            "blocked_market_count",
            "watch_market_count",
            "pass_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_correlation_score",
            _normalize_probability("max_correlation_score", self.max_correlation_score),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("StrategyMarketClusterCorrelationV6Report", self)


def build_strategy_market_cluster_correlation_v6(
    markets: Iterable[StrategyMarketClusterCorrelationV6Market],
    *,
    config: StrategyMarketClusterCorrelationV6Config,
    generated_at: datetime,
) -> StrategyMarketClusterCorrelationV6Report:
    if type(config) is not StrategyMarketClusterCorrelationV6Config:
        raise ValueError("config must be a StrategyMarketClusterCorrelationV6Config")
    require_paper_only_flags("StrategyMarketClusterCorrelationV6Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows_input = _normalize_markets(markets)
    _reject_future_markets(rows_input, generated_at_utc)
    rows = _rank_rows(
        tuple(
            _unranked_row(row, rows_input, config=config)
            for row in rows_input
        ),
    )
    return StrategyMarketClusterCorrelationV6Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        correlation_cluster_count=_count(len({row.correlation_cluster for row in rows})),
        max_correlation_score=_max_value(rows, "correlation_score"),
        blocked_market_count=_status_count(rows, BLOCKED_STATUS),
        watch_market_count=_status_count(rows, WATCH_STATUS),
        pass_market_count=_status_count(rows, PASS_STATUS),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_market_cluster_correlation_v6_payload(
    report: StrategyMarketClusterCorrelationV6Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketClusterCorrelationV6Report:
        raise ValueError("report must be a StrategyMarketClusterCorrelationV6Report")
    require_paper_only_flags("StrategyMarketClusterCorrelationV6Report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _unranked_row(
    row: StrategyMarketClusterCorrelationV6Market,
    rows: tuple[StrategyMarketClusterCorrelationV6Market, ...],
    *,
    config: StrategyMarketClusterCorrelationV6Config,
) -> StrategyMarketClusterCorrelationV6Row:
    category_peer_count = _peer_count(row, rows, "category")
    event_cluster_peer_count = _peer_count(row, rows, "event_cluster")
    team_peer_count = _peer_count(row, rows, "team")
    shared_source_peer_count = _shared_source_peer_count(row, rows)
    correlation_score = _correlation_score(
        probability_co_movement=row.probability_co_movement,
        category_peer_count=category_peer_count,
        event_cluster_peer_count=event_cluster_peer_count,
        team_peer_count=team_peer_count,
        shared_source_peer_count=shared_source_peer_count,
    )
    return StrategyMarketClusterCorrelationV6Row(
        rank=Decimal("1"),
        market_slug=row.market_slug,
        category=row.category,
        event_cluster=row.event_cluster,
        team=row.team,
        correlation_cluster=_correlation_cluster(row.category, row.event_cluster, row.team),
        shared_sources=row.shared_sources,
        observed_at=row.observed_at,
        probability_co_movement=row.probability_co_movement,
        category_peer_count=category_peer_count,
        event_cluster_peer_count=event_cluster_peer_count,
        team_peer_count=team_peer_count,
        shared_source_peer_count=shared_source_peer_count,
        correlation_score=correlation_score,
        status=_status_from_score(correlation_score, config=config),
        reason_codes=_row_reason_codes(
            probability_co_movement=row.probability_co_movement,
            category_peer_count=category_peer_count,
            event_cluster_peer_count=event_cluster_peer_count,
            team_peer_count=team_peer_count,
            shared_source_peer_count=shared_source_peer_count,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[StrategyMarketClusterCorrelationV6Row, ...],
) -> tuple[StrategyMarketClusterCorrelationV6Row, ...]:
    sorted_rows = sorted(rows, key=_row_sort_key)
    return tuple(
        StrategyMarketClusterCorrelationV6Row(
            rank=_count(index),
            market_slug=row.market_slug,
            category=row.category,
            event_cluster=row.event_cluster,
            team=row.team,
            correlation_cluster=row.correlation_cluster,
            shared_sources=row.shared_sources,
            observed_at=row.observed_at,
            probability_co_movement=row.probability_co_movement,
            category_peer_count=row.category_peer_count,
            event_cluster_peer_count=row.event_cluster_peer_count,
            team_peer_count=row.team_peer_count,
            shared_source_peer_count=row.shared_source_peer_count,
            correlation_score=row.correlation_score,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _row_reason_codes(
    *,
    probability_co_movement: Decimal,
    category_peer_count: Decimal,
    event_cluster_peer_count: Decimal,
    team_peer_count: Decimal,
    shared_source_peer_count: Decimal,
    config: StrategyMarketClusterCorrelationV6Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if category_peer_count > ZERO_COUNT:
        reason_codes.append("category_overlap")
    if event_cluster_peer_count > ZERO_COUNT:
        reason_codes.append("event_cluster_overlap")
    if team_peer_count > ZERO_COUNT:
        reason_codes.append("team_overlap")
    if shared_source_peer_count > ZERO_COUNT:
        reason_codes.append("shared_sources_overlap")
    if probability_co_movement >= config.correlation_block_score:
        reason_codes.append("probability_co_movement_blocked")
    elif probability_co_movement >= config.correlation_watch_score:
        reason_codes.append("probability_co_movement_watch")
    if not reason_codes:
        reason_codes.append(CLEAR_REASON_CODE)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(set(reason_codes))),
        ROW_REASON_CODES,
    )


def _report_reason_codes(
    rows: tuple[StrategyMarketClusterCorrelationV6Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    risk_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON_CODE
    )
    if not risk_codes:
        return (CLEAR_REASON_CODE,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(set(risk_codes))),
        REPORT_REASON_CODES,
    )


def _correlation_cluster(category: str, event_cluster: str, team: str) -> str:
    return f"{category}|{event_cluster}|{team}"


def _correlation_score(
    *,
    probability_co_movement: Decimal,
    category_peer_count: Decimal,
    event_cluster_peer_count: Decimal,
    team_peer_count: Decimal,
    shared_source_peer_count: Decimal,
) -> Decimal:
    overlap_score = ZERO
    if category_peer_count > ZERO_COUNT:
        overlap_score = _q(overlap_score + CATEGORY_OVERLAP_SCORE)
    if event_cluster_peer_count > ZERO_COUNT:
        overlap_score = _q(overlap_score + EVENT_CLUSTER_OVERLAP_SCORE)
    if team_peer_count > ZERO_COUNT:
        overlap_score = _q(overlap_score + TEAM_OVERLAP_SCORE)
    if shared_source_peer_count > ZERO_COUNT:
        overlap_score = _q(overlap_score + SHARED_SOURCES_OVERLAP_SCORE)
    return _q(max(probability_co_movement, min(overlap_score, ONE)))


def _status_from_score(
    correlation_score: Decimal,
    *,
    config: StrategyMarketClusterCorrelationV6Config,
) -> str:
    if correlation_score >= config.correlation_block_score:
        return BLOCKED_STATUS
    if correlation_score >= config.correlation_watch_score:
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(rows: tuple[StrategyMarketClusterCorrelationV6Row, ...]) -> str:
    if any(row.status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _validate_row(row: StrategyMarketClusterCorrelationV6Row) -> None:
    expected_cluster = _correlation_cluster(row.category, row.event_cluster, row.team)
    if row.correlation_cluster != expected_cluster:
        raise ValueError("correlation_cluster must match category event_cluster and team")
    expected_score = _correlation_score(
        probability_co_movement=row.probability_co_movement,
        category_peer_count=row.category_peer_count,
        event_cluster_peer_count=row.event_cluster_peer_count,
        team_peer_count=row.team_peer_count,
        shared_source_peer_count=row.shared_source_peer_count,
    )
    if row.correlation_score != expected_score:
        raise ValueError("correlation_score must match row inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: StrategyMarketClusterCorrelationV6Report) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.correlation_cluster_count != _count(
        len({row.correlation_cluster for row in report.rows}),
    ):
        raise ValueError("correlation_cluster_count must match rows")
    if report.max_correlation_score != _max_value(report.rows, "correlation_score"):
        raise ValueError("max_correlation_score must match rows")
    if report.blocked_market_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_market_count must match rows")
    if report.watch_market_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_market_count must match rows")
    if report.pass_market_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_market_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_markets(
    value: Iterable[StrategyMarketClusterCorrelationV6Market],
) -> tuple[StrategyMarketClusterCorrelationV6Market, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("markets must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("markets must be an iterable") from exc
    market_slugs: set[str] = set()
    for row in rows:
        if type(row) is not StrategyMarketClusterCorrelationV6Market:
            raise ValueError("markets must contain exact market rows")
        require_paper_only_flags("StrategyMarketClusterCorrelationV6Market", row)
        if row.market_slug in market_slugs:
            raise ValueError("market_slug values must be unique")
        market_slugs.add(row.market_slug)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyMarketClusterCorrelationV6Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyMarketClusterCorrelationV6Row:
            raise ValueError("rows must contain exact market cluster rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status score and market_slug")
    return rows


def _reject_future_markets(
    rows: tuple[StrategyMarketClusterCorrelationV6Market, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _peer_count(
    row: StrategyMarketClusterCorrelationV6Market,
    rows: tuple[StrategyMarketClusterCorrelationV6Market, ...],
    field_name: str,
) -> Decimal:
    return _count(
        sum(
            1
            for peer in rows
            if peer.market_slug != row.market_slug
            and getattr(peer, field_name) == getattr(row, field_name)
        ),
    )


def _shared_source_peer_count(
    row: StrategyMarketClusterCorrelationV6Market,
    rows: tuple[StrategyMarketClusterCorrelationV6Market, ...],
) -> Decimal:
    row_sources = frozenset(row.shared_sources)
    return _count(
        sum(
            1
            for peer in rows
            if peer.market_slug != row.market_slug
            and bool(row_sources.intersection(peer.shared_sources))
        ),
    )


def _row_sort_key(row: StrategyMarketClusterCorrelationV6Row) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), -row.correlation_score, row.market_slug)


def _status_rank(status: str) -> int:
    if status == BLOCKED_STATUS:
        return 0
    if status == WATCH_STATUS:
        return 1
    return 2


def _status_count(
    rows: tuple[StrategyMarketClusterCorrelationV6Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "probability_co_movement_blocked" in reason_codes:
        return BLOCKED_STATUS
    if "probability_co_movement_watch" in reason_codes:
        return WATCH_STATUS
    if any(reason_code.endswith("_overlap") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _max_value(
    rows: tuple[StrategyMarketClusterCorrelationV6Row, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value)
            for key, nested_value in asdict(value).items()
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
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_shared_sources(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    normalized = tuple(sorted(value))
    for item in normalized:
        _require_canonical_string(field_name, item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} values must be unique")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_value(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _q(value)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be at least zero")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be at least zero")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains unsupported value")
        normalized.append(reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} values must be unique")
    return tuple(normalized)


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANTUM)


__all__ = (
    "DEFAULT_STRATEGY_MARKET_CLUSTER_CORRELATION_V6_CONFIG_VERSION",
    "StrategyMarketClusterCorrelationV6Config",
    "StrategyMarketClusterCorrelationV6Market",
    "StrategyMarketClusterCorrelationV6Report",
    "StrategyMarketClusterCorrelationV6Row",
    "build_strategy_market_cluster_correlation_v6",
    "strategy_market_cluster_correlation_v6_payload",
)
