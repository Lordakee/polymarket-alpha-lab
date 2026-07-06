"""Phase 1 paper-only matrix for market research team signal triage."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    TEAM_CATEGORIES,
    TEAM_ID_TO_PRIMARY_CATEGORY,
    TEAM_IDS,
    require_category_id,
    require_team_id,
)


DEFAULT_MARKET_RESEARCH_TEAM_SIGNAL_TRIAGE_MATRIX_V2_CONFIG_VERSION = (
    "market-research-team-signal-triage-matrix-v2-phase-1"
)

COUNT_QUANTUM = Decimal("0.000000")
ONE_COUNT = Decimal("1.000000")

CATEGORY_TO_PRIMARY_TEAM_ID = {
    category_id: team_id for team_id, category_id in TEAM_ID_TO_PRIMARY_CATEGORY.items()
}

EVENT_ARCHETYPES = (
    "court_or_policy_stay",
    "election_polling_shift",
    "etf_flow_or_onchain_shock",
    "regulatory_action",
    "staking_or_protocol_event",
    "central_bank_data_release",
    "treasury_auction_or_rate_path",
    "macro_data_index_move",
    "earnings_index_breadth",
    "real_rates_usd_shock",
    "geopolitical_safety_bid",
    "inventory_or_opec_supply_shock",
    "weather_or_transport_disruption",
    "lineup_or_injury_news",
    "tournament_rules_resolution",
    "injury_or_rotation_news",
    "schedule_fatigue_spot",
    "sport_specific_rules_or_weather",
    "odds_consensus_break",
)

SOURCE_FAMILIES = (
    "agency_statement",
    "auction_result",
    "breadth_market_data",
    "court_docket",
    "earnings_calendar",
    "exchange_market_data",
    "fund_flow",
    "injury_report",
    "inventory_report",
    "league_statement",
    "odds_consensus",
    "official_election_admin",
    "official_statistics",
    "onchain_analytics",
    "polling_aggregator",
    "primary_news_reporting",
    "producer_statement",
    "protocol_governance",
    "rates_curve",
    "real_rates_usd",
    "regulatory_filing",
    "team_statement",
    "tournament_rulebook",
    "weather_feed",
)

ESCALATION_TAGS = (
    "close_margin_risk",
    "cross_team_review",
    "data_revision_risk",
    "injury_confirmation_required",
    "liquidity_dislocation",
    "market_microstructure_review",
    "official_confirmation_required",
    "regulatory_action_risk",
    "resolution_rule_risk",
    "supply_outage_risk",
    "time_sensitive",
    "weather_or_venue_risk",
)


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")
    return value


def _normalize_known_string_tuple(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")

    seen: set[str] = set()
    for item in items:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
    unknown_items = seen - set(allowed_values)
    if unknown_items:
        raise ValueError(f"{field_name} must contain known values")
    return tuple(item for item in allowed_values if item in seen)


def _normalize_specialist_team_ids(
    market_category: str,
    value: object,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("specialist_team_ids must be an iterable of team ids")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("specialist_team_ids must be an iterable of team ids") from exc
    if not items:
        raise ValueError("specialist_team_ids must not be empty")

    seen: set[str] = set()
    for item in items:
        team_id = require_team_id("specialist_team_id", item)
        if team_id in seen:
            raise ValueError("specialist_team_ids must be unique")
        seen.add(team_id)

    primary_team_id = CATEGORY_TO_PRIMARY_TEAM_ID[market_category]
    if primary_team_id not in seen:
        raise ValueError("specialist_team_ids must include the primary team")
    return (primary_team_id,) + tuple(
        team_id for team_id in TEAM_IDS if team_id != primary_team_id and team_id in seen
    )


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ONE_COUNT:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < Decimal("0.000000"):
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


@dataclass(frozen=True)
class MarketResearchTeamSignalTriageMatrixV2Row:
    market_category: str
    event_archetype: str
    specialist_team_ids: tuple[str, ...]
    required_source_families: tuple[str, ...]
    minimum_evidence_count: Decimal
    escalation_tags: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTeamSignalTriageMatrixV2Row:
            raise TypeError(
                "MarketResearchTeamSignalTriageMatrixV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchTeamSignalTriageMatrixV2Row,
            "triage matrix row",
        )
        market_category = require_category_id("market_category", self.market_category)
        object.__setattr__(self, "market_category", market_category)
        object.__setattr__(
            self,
            "event_archetype",
            _require_member("event_archetype", self.event_archetype, EVENT_ARCHETYPES),
        )
        object.__setattr__(
            self,
            "specialist_team_ids",
            _normalize_specialist_team_ids(
                market_category,
                self.specialist_team_ids,
            ),
        )
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_known_string_tuple(
                "required_source_families",
                self.required_source_families,
                SOURCE_FAMILIES,
            ),
        )
        object.__setattr__(
            self,
            "minimum_evidence_count",
            _normalize_positive_count(
                "minimum_evidence_count",
                self.minimum_evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "escalation_tags",
            _normalize_known_string_tuple(
                "escalation_tags",
                self.escalation_tags,
                ESCALATION_TAGS,
            ),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("triage matrix row", self)
        require_paper_only_flags("MarketResearchTeamSignalTriageMatrixV2Row", self)


def _validate_row(row: MarketResearchTeamSignalTriageMatrixV2Row) -> None:
    required_family_count = _count(len(row.required_source_families))
    if row.minimum_evidence_count < required_family_count:
        raise ValueError(
            "minimum_evidence_count must cover all required source families",
        )


DEFAULT_TRIAGE_MATRIX_V2_ROWS = (
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="politics",
        event_archetype="election_polling_shift",
        specialist_team_ids=("politics",),
        required_source_families=(
            "official_election_admin",
            "polling_aggregator",
            "primary_news_reporting",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("close_margin_risk", "official_confirmation_required"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="politics",
        event_archetype="court_or_policy_stay",
        specialist_team_ids=("politics", "macro_rates"),
        required_source_families=(
            "agency_statement",
            "court_docket",
            "primary_news_reporting",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("cross_team_review", "resolution_rule_risk", "time_sensitive"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.crypto.btc",
        event_archetype="etf_flow_or_onchain_shock",
        specialist_team_ids=("crypto_btc",),
        required_source_families=(
            "exchange_market_data",
            "fund_flow",
            "onchain_analytics",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("liquidity_dislocation", "market_microstructure_review"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.crypto.btc",
        event_archetype="regulatory_action",
        specialist_team_ids=("crypto_btc", "politics"),
        required_source_families=(
            "agency_statement",
            "primary_news_reporting",
            "regulatory_filing",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("cross_team_review", "regulatory_action_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.crypto.eth",
        event_archetype="etf_flow_or_onchain_shock",
        specialist_team_ids=("crypto_eth",),
        required_source_families=(
            "exchange_market_data",
            "fund_flow",
            "onchain_analytics",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("liquidity_dislocation", "market_microstructure_review"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.crypto.eth",
        event_archetype="staking_or_protocol_event",
        specialist_team_ids=("crypto_eth",),
        required_source_families=(
            "exchange_market_data",
            "onchain_analytics",
            "protocol_governance",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("official_confirmation_required", "resolution_rule_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.macro.rates",
        event_archetype="central_bank_data_release",
        specialist_team_ids=("macro_rates",),
        required_source_families=(
            "agency_statement",
            "official_statistics",
            "rates_curve",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("data_revision_risk", "official_confirmation_required"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.macro.rates",
        event_archetype="treasury_auction_or_rate_path",
        specialist_team_ids=("macro_rates",),
        required_source_families=("auction_result", "rates_curve", "primary_news_reporting"),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("market_microstructure_review", "time_sensitive"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.equity.indices",
        event_archetype="macro_data_index_move",
        specialist_team_ids=("equity_indices", "macro_rates"),
        required_source_families=(
            "breadth_market_data",
            "official_statistics",
            "rates_curve",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("cross_team_review", "data_revision_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.equity.indices",
        event_archetype="earnings_index_breadth",
        specialist_team_ids=("equity_indices",),
        required_source_families=(
            "breadth_market_data",
            "earnings_calendar",
            "primary_news_reporting",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("market_microstructure_review", "official_confirmation_required"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.commodities.gold",
        event_archetype="real_rates_usd_shock",
        specialist_team_ids=("commodities_gold", "macro_rates"),
        required_source_families=("real_rates_usd", "rates_curve", "primary_news_reporting"),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("cross_team_review", "data_revision_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.commodities.gold",
        event_archetype="geopolitical_safety_bid",
        specialist_team_ids=("commodities_gold", "politics"),
        required_source_families=(
            "agency_statement",
            "exchange_market_data",
            "primary_news_reporting",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("cross_team_review", "time_sensitive"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.commodities.oil",
        event_archetype="inventory_or_opec_supply_shock",
        specialist_team_ids=("commodities_oil",),
        required_source_families=(
            "agency_statement",
            "inventory_report",
            "producer_statement",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("official_confirmation_required", "supply_outage_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="finance.commodities.oil",
        event_archetype="weather_or_transport_disruption",
        specialist_team_ids=("commodities_oil",),
        required_source_families=(
            "exchange_market_data",
            "primary_news_reporting",
            "weather_feed",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("supply_outage_risk", "weather_or_venue_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="sports.soccer",
        event_archetype="lineup_or_injury_news",
        specialist_team_ids=("sports_soccer",),
        required_source_families=("injury_report", "team_statement", "odds_consensus"),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("injury_confirmation_required", "time_sensitive"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="sports.soccer",
        event_archetype="tournament_rules_resolution",
        specialist_team_ids=("sports_soccer",),
        required_source_families=(
            "league_statement",
            "primary_news_reporting",
            "tournament_rulebook",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("official_confirmation_required", "resolution_rule_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="sports.basketball",
        event_archetype="injury_or_rotation_news",
        specialist_team_ids=("sports_basketball",),
        required_source_families=("injury_report", "odds_consensus", "team_statement"),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("injury_confirmation_required", "time_sensitive"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="sports.basketball",
        event_archetype="schedule_fatigue_spot",
        specialist_team_ids=("sports_basketball",),
        required_source_families=("league_statement", "odds_consensus", "team_statement"),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("market_microstructure_review", "time_sensitive"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="sports.other",
        event_archetype="sport_specific_rules_or_weather",
        specialist_team_ids=("sports_other",),
        required_source_families=(
            "league_statement",
            "primary_news_reporting",
            "weather_feed",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("resolution_rule_risk", "weather_or_venue_risk"),
    ),
    MarketResearchTeamSignalTriageMatrixV2Row(
        market_category="sports.other",
        event_archetype="odds_consensus_break",
        specialist_team_ids=("sports_other",),
        required_source_families=(
            "exchange_market_data",
            "odds_consensus",
            "primary_news_reporting",
        ),
        minimum_evidence_count=Decimal("3.000000"),
        escalation_tags=("liquidity_dislocation", "market_microstructure_review"),
    ),
)


@dataclass(frozen=True)
class MarketResearchTeamSignalTriageMatrixV2Config:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TEAM_SIGNAL_TRIAGE_MATRIX_V2_CONFIG_VERSION
    )
    rule_rows: tuple[
        MarketResearchTeamSignalTriageMatrixV2Row,
        ...,
    ] = DEFAULT_TRIAGE_MATRIX_V2_ROWS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTeamSignalTriageMatrixV2Config:
            raise TypeError(
                "MarketResearchTeamSignalTriageMatrixV2Config does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchTeamSignalTriageMatrixV2Config,
            "triage matrix config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_TEAM_SIGNAL_TRIAGE_MATRIX_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "rule_rows",
            _normalize_rule_rows(self.rule_rows),
        )
        require_paper_only_flags("MarketResearchTeamSignalTriageMatrixV2Config", self)


@dataclass(frozen=True)
class MarketResearchTeamSignalTriageMatrixV2:
    config_version: str
    row_count: Decimal
    category_count: Decimal
    event_archetype_count: Decimal
    rows: tuple[MarketResearchTeamSignalTriageMatrixV2Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchTeamSignalTriageMatrixV2:
            raise TypeError(
                "MarketResearchTeamSignalTriageMatrixV2 does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchTeamSignalTriageMatrixV2,
            "triage matrix",
        )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "row_count",
            _normalize_nonnegative_count("row_count", self.row_count),
        )
        object.__setattr__(
            self,
            "category_count",
            _normalize_nonnegative_count("category_count", self.category_count),
        )
        object.__setattr__(
            self,
            "event_archetype_count",
            _normalize_nonnegative_count(
                "event_archetype_count",
                self.event_archetype_count,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rule_rows(self.rows))
        _validate_matrix(self)
        reject_unsafe_surface_fields("triage matrix", self)
        require_paper_only_flags("MarketResearchTeamSignalTriageMatrixV2", self)


def build_market_research_team_signal_triage_matrix_v2(
    *,
    config: MarketResearchTeamSignalTriageMatrixV2Config | None = None,
) -> MarketResearchTeamSignalTriageMatrixV2:
    if config is None:
        config = MarketResearchTeamSignalTriageMatrixV2Config()
    if type(config) is not MarketResearchTeamSignalTriageMatrixV2Config:
        raise ValueError(
            "config must be a MarketResearchTeamSignalTriageMatrixV2Config",
        )
    require_paper_only_flags("MarketResearchTeamSignalTriageMatrixV2Config", config)
    rows = _normalize_rule_rows(config.rule_rows)
    return MarketResearchTeamSignalTriageMatrixV2(
        config_version=config.config_version,
        row_count=_count(len(rows)),
        category_count=_count(len({row.market_category for row in rows})),
        event_archetype_count=_count(len({row.event_archetype for row in rows})),
        rows=rows,
    )


def lookup_market_research_team_signal_triage_matrix_v2(
    market_category: str,
    event_archetype: str,
    *,
    config: MarketResearchTeamSignalTriageMatrixV2Config | None = None,
) -> MarketResearchTeamSignalTriageMatrixV2Row:
    normalized_category = require_category_id("market_category", market_category)
    normalized_archetype = _require_member(
        "event_archetype",
        event_archetype,
        EVENT_ARCHETYPES,
    )
    matrix = build_market_research_team_signal_triage_matrix_v2(config=config)
    for row in matrix.rows:
        if (
            row.market_category == normalized_category
            and row.event_archetype == normalized_archetype
        ):
            return row
    raise ValueError("triage rule not found")


def market_research_team_signal_triage_matrix_v2_payload(
    value: object,
) -> dict[str, Any]:
    if isinstance(
        value,
        (
            MarketResearchTeamSignalTriageMatrixV2,
            MarketResearchTeamSignalTriageMatrixV2Config,
            MarketResearchTeamSignalTriageMatrixV2Row,
        ),
    ):
        require_paper_only_flags("triage matrix payload", value)
    elif not isinstance(value, dict):
        raise ValueError("value must be a triage matrix, config, row, or JSON object")

    _validate_payload_flags(value)
    reject_unsafe_surface_fields("triage matrix payload", value)
    payload = json_ready_no_floats(value)
    if not isinstance(payload, dict):
        raise ValueError("triage matrix payload must be a JSON object")
    _validate_payload_flags(payload)
    reject_unsafe_surface_fields("triage matrix payload", payload)
    return payload


def _normalize_rule_rows(
    value: Iterable[MarketResearchTeamSignalTriageMatrixV2Row],
) -> tuple[MarketResearchTeamSignalTriageMatrixV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rule_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rule_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketResearchTeamSignalTriageMatrixV2Row:
            raise ValueError(
                "rule_rows must contain MarketResearchTeamSignalTriageMatrixV2Row "
                "values",
            )
        require_paper_only_flags("MarketResearchTeamSignalTriageMatrixV2Row", row)
    if len({_row_key(row) for row in rows}) != len(rows):
        raise ValueError("rule_rows must use unique category/archetype keys")
    return tuple(sorted(rows, key=_row_key))


def _row_key(row: MarketResearchTeamSignalTriageMatrixV2Row) -> tuple[str, str]:
    return row.market_category, row.event_archetype


def _validate_matrix(matrix: MarketResearchTeamSignalTriageMatrixV2) -> None:
    rows = matrix.rows
    if matrix.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if matrix.category_count != _count(len({row.market_category for row in rows})):
        raise ValueError("category_count must match rows")
    if matrix.event_archetype_count != _count(
        len({row.event_archetype for row in rows}),
    ):
        raise ValueError("event_archetype_count must match rows")
    if tuple(sorted(rows, key=_row_key)) != rows:
        raise ValueError("rows must use deterministic sorting")


def _validate_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_TEAM_SIGNAL_TRIAGE_MATRIX_V2_CONFIG_VERSION",
    "DEFAULT_TRIAGE_MATRIX_V2_ROWS",
    "ESCALATION_TAGS",
    "EVENT_ARCHETYPES",
    "SOURCE_FAMILIES",
    "MarketResearchTeamSignalTriageMatrixV2",
    "MarketResearchTeamSignalTriageMatrixV2Config",
    "MarketResearchTeamSignalTriageMatrixV2Row",
    "build_market_research_team_signal_triage_matrix_v2",
    "lookup_market_research_team_signal_triage_matrix_v2",
    "market_research_team_signal_triage_matrix_v2_payload",
)
