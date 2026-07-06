"""Pure report-only event team assignment strategy v10."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS, require_team_id


DEFAULT_STRATEGY_EVENT_TEAM_ASSIGNMENT_V10_CONFIG_VERSION = (
    "strategy-event-team-assignment-v10"
)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FULL_HISTORY_SAMPLE_COUNT = Decimal("100.000000")
DEFAULT_HISTORY_SCORE = Decimal("0.500000")
QUALITY_REVIEW_TEAM = "research_quality"

ASSIGNMENT_STATUSES = ("clear", "assigned", "watch", "escalated")
ROW_REASON_CODES = (
    "strategy_event_team_assignment_v10_asset_crypto_btc",
    "strategy_event_team_assignment_v10_asset_crypto_eth",
    "strategy_event_team_assignment_v10_asset_equity_index",
    "strategy_event_team_assignment_v10_asset_gold",
    "strategy_event_team_assignment_v10_category_politics",
    "strategy_event_team_assignment_v10_category_finance",
    "strategy_event_team_assignment_v10_category_crypto",
    "strategy_event_team_assignment_v10_category_equity_indices",
    "strategy_event_team_assignment_v10_category_commodities_gold",
    "strategy_event_team_assignment_v10_category_sports_soccer",
    "strategy_event_team_assignment_v10_category_sports_basketball",
    "strategy_event_team_assignment_v10_category_sports_other",
    "strategy_event_team_assignment_v10_general_fallback",
    "strategy_event_team_assignment_v10_high_complexity",
    "strategy_event_team_assignment_v10_low_source_coverage",
    "strategy_event_team_assignment_v10_weak_team_history",
    "strategy_event_team_assignment_v10_assigned",
    "strategy_event_team_assignment_v10_escalated",
)
REPORT_REASON_CODES = (
    "strategy_event_team_assignment_v10_clear",
    "strategy_event_team_assignment_v10_assigned",
    "strategy_event_team_assignment_v10_high_complexity",
    "strategy_event_team_assignment_v10_low_source_coverage",
    "strategy_event_team_assignment_v10_weak_team_history",
    "strategy_event_team_assignment_v10_escalated",
)


@dataclass(frozen=True)
class StrategyEventTeamAssignmentV10Config:
    config_version: str = DEFAULT_STRATEGY_EVENT_TEAM_ASSIGNMENT_V10_CONFIG_VERSION
    category_fit_weight: Decimal = Decimal("0.500000")
    team_history_weight: Decimal = Decimal("0.300000")
    source_coverage_weight: Decimal = Decimal("0.200000")
    high_complexity_threshold: Decimal = Decimal("0.700000")
    low_source_coverage_threshold: Decimal = Decimal("0.600000")
    weak_history_threshold: Decimal = Decimal("0.500000")
    max_support_team_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, StrategyEventTeamAssignmentV10Config)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_fit_weight",
            "team_history_weight",
            "source_coverage_weight",
            "high_complexity_threshold",
            "low_source_coverage_threshold",
            "weak_history_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_support_team_count",
            _normalize_nonnegative_count(
                "max_support_team_count",
                self.max_support_team_count,
            ),
        )
        if (
            self.category_fit_weight
            + self.team_history_weight
            + self.source_coverage_weight
        ) != ONE:
            raise ValueError("strategy assignment weight sum must equal 1.000000")
        require_paper_only_flags("StrategyEventTeamAssignmentV10Config", self)


@dataclass(frozen=True)
class StrategyEventTeamAssignmentV10Market:
    event_id: str
    market_category: str
    asset: str | None = None
    league: str | None = None
    country: str | None = None
    parse_rule_complexity_score: Decimal = Decimal("0.000000")
    source_coverage_score: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("market", self, StrategyEventTeamAssignmentV10Market)
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("market_category", self.market_category)
        for field_name in ("asset", "league", "country"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        for field_name in ("parse_rule_complexity_score", "source_coverage_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("StrategyEventTeamAssignmentV10Market", self)


@dataclass(frozen=True)
class StrategyEventTeamAssignmentV10TeamHistory:
    team_id: str
    resolved_event_count: Decimal
    historical_accuracy_score: Decimal
    calibration_score: Decimal
    source_reliability_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("team history", self, StrategyEventTeamAssignmentV10TeamHistory)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "resolved_event_count",
            _normalize_nonnegative_count(
                "resolved_event_count",
                self.resolved_event_count,
            ),
        )
        for field_name in (
            "historical_accuracy_score",
            "calibration_score",
            "source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("StrategyEventTeamAssignmentV10TeamHistory", self)


@dataclass(frozen=True)
class StrategyEventTeamAssignmentV10Row:
    event_id: str
    market_category: str
    asset: str | None
    league: str | None
    country: str | None
    parse_rule_complexity_score: Decimal
    source_coverage_score: Decimal
    lead_team: str
    support_teams: tuple[str, ...]
    escalation_team: str
    category_fit_score: Decimal
    team_history_score: Decimal
    lead_assignment_score: Decimal
    assignment_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyEventTeamAssignmentV10Row)
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("market_category", self.market_category)
        for field_name in ("asset", "league", "country"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "parse_rule_complexity_score",
            "source_coverage_score",
            "category_fit_score",
            "team_history_score",
            "lead_assignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "lead_team", require_team_id("lead_team", self.lead_team))
        object.__setattr__(
            self,
            "support_teams",
            _normalize_team_ids("support_teams", self.support_teams),
        )
        _require_escalation_team("escalation_team", self.escalation_team)
        _require_member("assignment_status", self.assignment_status, ASSIGNMENT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("StrategyEventTeamAssignmentV10Row", self)


@dataclass(frozen=True)
class StrategyEventTeamAssignmentV10Report:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    assigned_event_count: Decimal
    escalated_event_count: Decimal
    assignment_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyEventTeamAssignmentV10Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyEventTeamAssignmentV10Report)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "assigned_event_count",
            "escalated_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("assignment_status", self.assignment_status, ASSIGNMENT_STATUSES)
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
        require_paper_only_flags("StrategyEventTeamAssignmentV10Report", self)


def build_strategy_event_team_assignment_v10_report(
    markets: list[StrategyEventTeamAssignmentV10Market]
    | tuple[StrategyEventTeamAssignmentV10Market, ...],
    *,
    team_histories: list[StrategyEventTeamAssignmentV10TeamHistory]
    | tuple[StrategyEventTeamAssignmentV10TeamHistory, ...],
    config: StrategyEventTeamAssignmentV10Config,
    generated_at: datetime,
) -> StrategyEventTeamAssignmentV10Report:
    if type(config) is not StrategyEventTeamAssignmentV10Config:
        raise ValueError("config must be a StrategyEventTeamAssignmentV10Config")
    require_paper_only_flags("config", config)
    market_rows = _normalize_markets(markets)
    history_by_team = _history_by_team_id(team_histories)
    rows = tuple(
        _assignment_row(market, history_by_team, config)
        for market in market_rows
    )
    return StrategyEventTeamAssignmentV10Report(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_count(len(market_rows)),
        assigned_event_count=_count(len(rows)),
        escalated_event_count=_count(
            sum(1 for row in rows if row.assignment_status == "escalated"),
        ),
        assignment_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_event_team_assignment_v10_payload(report: object) -> dict[str, Any]:
    if type(report) is not StrategyEventTeamAssignmentV10Report:
        reject_unsafe_surface_fields("strategy event team assignment v10 report", report)
        raise ValueError("report must be a StrategyEventTeamAssignmentV10Report")
    require_paper_only_flags("report", report)
    return json_ready_no_floats(report)


def _assignment_row(
    market: StrategyEventTeamAssignmentV10Market,
    history_by_team: dict[str, StrategyEventTeamAssignmentV10TeamHistory],
    config: StrategyEventTeamAssignmentV10Config,
) -> StrategyEventTeamAssignmentV10Row:
    candidates, base_reason_code = _candidate_team_fits(market)
    scored = tuple(
        (
            team_id,
            fit_score,
            _history_score(history_by_team.get(team_id)),
            _assignment_score(
                category_fit_score=fit_score,
                team_history_score=_history_score(history_by_team.get(team_id)),
                source_coverage_score=market.source_coverage_score,
                config=config,
            ),
        )
        for team_id, fit_score in candidates
    )
    lead_team, category_fit_score, team_history_score, lead_assignment_score = max(
        scored,
        key=lambda item: (item[3], item[1], item[2], _team_rank(item[0])),
    )
    support_teams = tuple(
        team_id
        for team_id, _fit, _history, _score in sorted(
            (item for item in scored if item[0] != lead_team),
            key=lambda item: (item[3], item[1], item[2], _team_rank(item[0])),
            reverse=True,
        )[: int(config.max_support_team_count)]
    )
    reason_codes = _row_reason_codes(
        base_reason_code=base_reason_code,
        market=market,
        team_history_score=team_history_score,
        config=config,
    )
    assignment_status = (
        "escalated"
        if "strategy_event_team_assignment_v10_escalated" in reason_codes
        else "assigned"
    )
    escalation_team = QUALITY_REVIEW_TEAM if assignment_status == "escalated" else lead_team
    return StrategyEventTeamAssignmentV10Row(
        event_id=market.event_id,
        market_category=market.market_category,
        asset=market.asset,
        league=market.league,
        country=market.country,
        parse_rule_complexity_score=market.parse_rule_complexity_score,
        source_coverage_score=market.source_coverage_score,
        lead_team=lead_team,
        support_teams=support_teams,
        escalation_team=escalation_team,
        category_fit_score=category_fit_score,
        team_history_score=team_history_score,
        lead_assignment_score=lead_assignment_score,
        assignment_status=assignment_status,
        reason_codes=reason_codes,
    )


def _candidate_team_fits(
    market: StrategyEventTeamAssignmentV10Market,
) -> tuple[tuple[tuple[str, Decimal], ...], str]:
    category = market.market_category.casefold()
    asset = "" if market.asset is None else market.asset.casefold()
    league = "" if market.league is None else market.league.casefold()
    if any(term in asset for term in ("btc", "bitcoin")):
        return (
            (
                ("crypto_btc", Decimal("1.000000")),
                ("crypto_eth", Decimal("0.750000")),
                ("macro_rates", Decimal("0.650000")),
            ),
            "strategy_event_team_assignment_v10_asset_crypto_btc",
        )
    if any(term in asset for term in ("eth", "ethereum")):
        return (
            (
                ("crypto_eth", Decimal("1.000000")),
                ("crypto_btc", Decimal("0.750000")),
                ("macro_rates", Decimal("0.650000")),
            ),
            "strategy_event_team_assignment_v10_asset_crypto_eth",
        )
    if any(term in asset for term in ("nasdaq", "spx", "s&p", "dow", "index")):
        return (
            (
                ("equity_indices", Decimal("1.000000")),
                ("macro_rates", Decimal("0.650000")),
                ("crypto_btc", Decimal("0.250000")),
            ),
            "strategy_event_team_assignment_v10_asset_equity_index",
        )
    if any(term in asset for term in ("gold", "xau")):
        return (
            (
                ("commodities_gold", Decimal("1.000000")),
                ("macro_rates", Decimal("0.650000")),
                ("equity_indices", Decimal("0.450000")),
            ),
            "strategy_event_team_assignment_v10_asset_gold",
        )
    if category.startswith("politics"):
        return (
            (
                ("politics", Decimal("1.000000")),
                ("macro_rates", Decimal("0.500000")),
            ),
            "strategy_event_team_assignment_v10_category_politics",
        )
    if "finance.crypto" in category or category == "crypto":
        return (
            (
                ("crypto_btc", Decimal("0.900000")),
                ("crypto_eth", Decimal("0.900000")),
                ("macro_rates", Decimal("0.700000")),
            ),
            "strategy_event_team_assignment_v10_category_crypto",
        )
    if "equity" in category:
        return (
            (
                ("equity_indices", Decimal("1.000000")),
                ("macro_rates", Decimal("0.650000")),
                ("crypto_btc", Decimal("0.250000")),
            ),
            "strategy_event_team_assignment_v10_category_equity_indices",
        )
    if "commodities.gold" in category or "gold" in category:
        return (
            (
                ("commodities_gold", Decimal("1.000000")),
                ("macro_rates", Decimal("0.650000")),
                ("equity_indices", Decimal("0.450000")),
            ),
            "strategy_event_team_assignment_v10_category_commodities_gold",
        )
    if _is_basketball_market(category, league):
        return (
            (
                ("sports_basketball", Decimal("1.000000")),
                ("sports_other", Decimal("0.550000")),
                ("sports_soccer", Decimal("0.350000")),
            ),
            "strategy_event_team_assignment_v10_category_sports_basketball",
        )
    if _is_soccer_market(category, league):
        return (
            (
                ("sports_soccer", Decimal("1.000000")),
                ("sports_other", Decimal("0.550000")),
                ("sports_basketball", Decimal("0.350000")),
            ),
            "strategy_event_team_assignment_v10_category_sports_soccer",
        )
    if "sports" in category:
        return (
            (
                ("sports_other", Decimal("1.000000")),
                ("sports_soccer", Decimal("0.400000")),
                ("sports_basketball", Decimal("0.400000")),
            ),
            "strategy_event_team_assignment_v10_category_sports_other",
        )
    if "finance" in category:
        return (
            (
                ("macro_rates", Decimal("0.900000")),
                ("equity_indices", Decimal("0.600000")),
                ("crypto_btc", Decimal("0.500000")),
            ),
            "strategy_event_team_assignment_v10_category_finance",
        )
    return (
        (
            ("macro_rates", Decimal("0.600000")),
            ("politics", Decimal("0.400000")),
            ("sports_other", Decimal("0.300000")),
        ),
        "strategy_event_team_assignment_v10_general_fallback",
    )


def _is_soccer_market(category: str, league: str) -> bool:
    return "soccer" in category or any(
        term in league
        for term in (
            "champions league",
            "uefa",
            "fifa",
            "premier league",
            "la liga",
            "serie a",
            "bundesliga",
            "mls",
        )
    )


def _is_basketball_market(category: str, league: str) -> bool:
    return "basketball" in category or any(
        term in league
        for term in (
            "nba",
            "wnba",
            "ncaa basketball",
            "march madness",
            "euroleague",
        )
    )


def _history_score(history: StrategyEventTeamAssignmentV10TeamHistory | None) -> Decimal:
    if history is None:
        return DEFAULT_HISTORY_SCORE
    base_score = _q(
        (
            history.historical_accuracy_score
            + history.calibration_score
            + history.source_reliability_score
        )
        / Decimal("3"),
    )
    sample_ratio = _clamp_ratio(history.resolved_event_count / FULL_HISTORY_SAMPLE_COUNT)
    sample_confidence = _clamp_ratio(Decimal("0.500000") + (Decimal("1.200000") * sample_ratio))
    return _q(base_score * sample_confidence)


def _assignment_score(
    *,
    category_fit_score: Decimal,
    team_history_score: Decimal,
    source_coverage_score: Decimal,
    config: StrategyEventTeamAssignmentV10Config,
) -> Decimal:
    return _q(
        (category_fit_score * config.category_fit_weight)
        + (team_history_score * config.team_history_weight)
        + (source_coverage_score * config.source_coverage_weight),
    )


def _row_reason_codes(
    *,
    base_reason_code: str,
    market: StrategyEventTeamAssignmentV10Market,
    team_history_score: Decimal,
    config: StrategyEventTeamAssignmentV10Config,
) -> tuple[str, ...]:
    codes = [base_reason_code]
    should_escalate = False
    if market.parse_rule_complexity_score >= config.high_complexity_threshold:
        codes.append("strategy_event_team_assignment_v10_high_complexity")
        should_escalate = True
    if market.source_coverage_score < config.low_source_coverage_threshold:
        codes.append("strategy_event_team_assignment_v10_low_source_coverage")
        should_escalate = True
    if team_history_score < config.weak_history_threshold:
        codes.append("strategy_event_team_assignment_v10_weak_team_history")
        should_escalate = True
    if should_escalate:
        codes.append("strategy_event_team_assignment_v10_escalated")
    else:
        codes.append("strategy_event_team_assignment_v10_assigned")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(rows: tuple[StrategyEventTeamAssignmentV10Row, ...]) -> str:
    if not rows:
        return "clear"
    if any(row.assignment_status == "escalated" for row in rows):
        return "watch"
    return "assigned"


def _report_reason_codes(
    rows: tuple[StrategyEventTeamAssignmentV10Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_event_team_assignment_v10_clear",)
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    codes = ["strategy_event_team_assignment_v10_assigned"]
    for reason_code in (
        "strategy_event_team_assignment_v10_high_complexity",
        "strategy_event_team_assignment_v10_low_source_coverage",
        "strategy_event_team_assignment_v10_weak_team_history",
        "strategy_event_team_assignment_v10_escalated",
    ):
        if reason_code in row_codes:
            codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _normalize_markets(
    markets: list[StrategyEventTeamAssignmentV10Market]
    | tuple[StrategyEventTeamAssignmentV10Market, ...],
) -> tuple[StrategyEventTeamAssignmentV10Market, ...]:
    if type(markets) not in (list, tuple):
        raise ValueError("markets must be a list or tuple")
    values = tuple(markets)
    seen: set[str] = set()
    for value in values:
        if type(value) is not StrategyEventTeamAssignmentV10Market:
            raise ValueError("markets must contain StrategyEventTeamAssignmentV10Market")
        require_paper_only_flags("market", value)
        if value.event_id in seen:
            raise ValueError("event_id values must be unique")
        seen.add(value.event_id)
    return values


def _history_by_team_id(
    team_histories: list[StrategyEventTeamAssignmentV10TeamHistory]
    | tuple[StrategyEventTeamAssignmentV10TeamHistory, ...],
) -> dict[str, StrategyEventTeamAssignmentV10TeamHistory]:
    if type(team_histories) not in (list, tuple):
        raise ValueError("team_histories must be a list or tuple")
    values = tuple(team_histories)
    by_team: dict[str, StrategyEventTeamAssignmentV10TeamHistory] = {}
    for value in values:
        if type(value) is not StrategyEventTeamAssignmentV10TeamHistory:
            raise ValueError(
                "team_histories must contain StrategyEventTeamAssignmentV10TeamHistory",
            )
        require_paper_only_flags("team history", value)
        if value.team_id in by_team:
            raise ValueError("team_histories must have unique team_id values")
        by_team[value.team_id] = value
    return by_team


def _normalize_rows(
    rows: tuple[StrategyEventTeamAssignmentV10Row, ...],
) -> tuple[StrategyEventTeamAssignmentV10Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyEventTeamAssignmentV10Row:
            raise ValueError("rows must contain StrategyEventTeamAssignmentV10Row")
        require_paper_only_flags("row", row)
        if row.event_id in seen:
            raise ValueError("rows must have unique event_id values")
        seen.add(row.event_id)
    return rows


def _normalize_team_ids(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for team_id in value:
        require_team_id(field_name, team_id)
        if team_id in seen:
            raise ValueError(f"{field_name} must contain unique teams")
        seen.add(team_id)
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string(field_name, value)
        if value not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported value")
        if value in seen:
            raise ValueError(f"{field_name} contains duplicate value")
        seen.add(value)
    return tuple(value for value in allowed_values if value in seen)


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(SCORE_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _q(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _q(value)


def _team_rank(team_id: str) -> Decimal:
    return _count(len(TEAM_IDS) - TEAM_IDS.index(team_id))


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_escalation_team(field_name: str, value: object) -> None:
    if value == QUALITY_REVIEW_TEAM:
        return
    require_team_id(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _validate_row(row: StrategyEventTeamAssignmentV10Row) -> None:
    if row.lead_team in row.support_teams:
        raise ValueError("lead_team must not appear in support_teams")
    if row.assignment_status == "assigned":
        if row.escalation_team != row.lead_team:
            raise ValueError("assigned rows must keep escalation_team on lead_team")
        if "strategy_event_team_assignment_v10_assigned" not in row.reason_codes:
            raise ValueError("assigned rows must include assigned reason")
    if row.assignment_status == "escalated":
        if row.escalation_team != QUALITY_REVIEW_TEAM:
            raise ValueError("escalated rows must use research quality escalation")
        if "strategy_event_team_assignment_v10_escalated" not in row.reason_codes:
            raise ValueError("escalated rows must include escalated reason")
    if row.assignment_status in ("clear", "watch"):
        raise ValueError("row assignment_status must be assigned or escalated")


def _validate_report(report: StrategyEventTeamAssignmentV10Report) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.assigned_event_count != _count(len(report.rows)):
        raise ValueError("assigned_event_count must match rows")
    escalated_count = _count(
        sum(1 for row in report.rows if row.assignment_status == "escalated"),
    )
    if report.escalated_event_count != escalated_count:
        raise ValueError("escalated_event_count must match rows")
    if report.assignment_status != _report_status(report.rows):
        raise ValueError("assignment_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


__all__ = (
    "DEFAULT_STRATEGY_EVENT_TEAM_ASSIGNMENT_V10_CONFIG_VERSION",
    "StrategyEventTeamAssignmentV10Config",
    "StrategyEventTeamAssignmentV10Market",
    "StrategyEventTeamAssignmentV10Report",
    "StrategyEventTeamAssignmentV10Row",
    "StrategyEventTeamAssignmentV10TeamHistory",
    "build_strategy_event_team_assignment_v10_report",
    "strategy_event_team_assignment_v10_payload",
)
