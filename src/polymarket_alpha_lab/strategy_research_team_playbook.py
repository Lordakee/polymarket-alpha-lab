"""Pure readonly research-source playbook contracts for strategy teams."""

from __future__ import annotations

from dataclasses import dataclass

from polymarket_alpha_lab.strategy_team_taxonomy import (
    STRATEGY_TEAM_IDS,
    require_strategy_team_id,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_STRATEGY_RESEARCH_TEAM_PLAYBOOK_CONFIG_VERSION = (
    "strategy-research-team-playbook-v1"
)

__all__ = (
    "DEFAULT_STRATEGY_RESEARCH_TEAM_PLAYBOOK_CONFIG_VERSION",
    "StrategyResearchTeamPlaybook",
    "StrategyResearchTeamPlaybookConfig",
    "StrategyResearchTeamPlaybookEntry",
    "build_default_strategy_research_team_playbook",
    "get_strategy_research_team_playbook_entry",
)


@dataclass(frozen=True)
class StrategyResearchTeamPlaybookConfig:
    config_version: str = DEFAULT_STRATEGY_RESEARCH_TEAM_PLAYBOOK_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("StrategyResearchTeamPlaybookConfig", self)


@dataclass(frozen=True)
class StrategyResearchTeamPlaybookEntry:
    team_id: str
    required_sources: tuple[str, ...]
    refresh_cadence_minutes: int
    key_failure_modes: tuple[str, ...]
    minimum_evidence_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_strategy_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "required_sources",
            _normalize_string_tuple("required_sources", self.required_sources),
        )
        object.__setattr__(
            self,
            "refresh_cadence_minutes",
            _require_positive_int("refresh_cadence_minutes", self.refresh_cadence_minutes),
        )
        object.__setattr__(
            self,
            "key_failure_modes",
            _normalize_string_tuple("key_failure_modes", self.key_failure_modes),
        )
        object.__setattr__(
            self,
            "minimum_evidence_count",
            _require_positive_int("minimum_evidence_count", self.minimum_evidence_count),
        )
        if self.minimum_evidence_count > len(self.required_sources):
            raise ValueError("minimum_evidence_count cannot exceed required_sources")
        require_paper_only_flags("StrategyResearchTeamPlaybookEntry", self)


@dataclass(frozen=True)
class StrategyResearchTeamPlaybook:
    config_version: str
    team_count: int
    entries: tuple[StrategyResearchTeamPlaybookEntry, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "team_count", _require_positive_int("team_count", self.team_count))
        object.__setattr__(self, "entries", _normalize_entries(self.entries))
        if self.team_count != len(self.entries):
            raise ValueError("team_count must match entries")
        if tuple(entry.team_id for entry in self.entries) != STRATEGY_TEAM_IDS:
            raise ValueError("entries must cover strategy teams in taxonomy order")
        require_paper_only_flags("StrategyResearchTeamPlaybook", self)


def build_default_strategy_research_team_playbook(
    *,
    config: StrategyResearchTeamPlaybookConfig,
) -> StrategyResearchTeamPlaybook:
    if type(config) is not StrategyResearchTeamPlaybookConfig:
        raise ValueError("config must be a StrategyResearchTeamPlaybookConfig")
    require_paper_only_flags("StrategyResearchTeamPlaybookConfig", config)
    entries = tuple(
        StrategyResearchTeamPlaybookEntry(
            team_id=team_id,
            required_sources=required_sources,
            refresh_cadence_minutes=refresh_cadence_minutes,
            key_failure_modes=key_failure_modes,
            minimum_evidence_count=minimum_evidence_count,
        )
        for (
            team_id,
            required_sources,
            refresh_cadence_minutes,
            key_failure_modes,
            minimum_evidence_count,
        ) in _DEFAULT_ENTRY_SPECS
    )
    return StrategyResearchTeamPlaybook(
        config_version=config.config_version,
        team_count=len(entries),
        entries=entries,
    )


def get_strategy_research_team_playbook_entry(
    team_id: str,
    *,
    config: StrategyResearchTeamPlaybookConfig | None = None,
) -> StrategyResearchTeamPlaybookEntry:
    normalized_team_id = require_strategy_team_id("team_id", team_id)
    active_config = StrategyResearchTeamPlaybookConfig() if config is None else config
    playbook = build_default_strategy_research_team_playbook(config=active_config)
    for entry in playbook.entries:
        if entry.team_id == normalized_team_id:
            return entry
    raise ValueError("team_id must be a known strategy team")


_DEFAULT_ENTRY_SPECS: tuple[
    tuple[str, tuple[str, ...], int, tuple[str, ...], int],
    ...,
] = (
    (
        "politics",
        (
            "official_election_or_government_source",
            "credible_polling_aggregator",
            "campaign_or_court_record",
            "major_news_wire",
        ),
        60,
        (
            "polling_error_or_late_swing",
            "ambiguous_resolution_language",
            "court_or_certification_delay",
            "partisan_source_bias",
        ),
        4,
    ),
    (
        "crypto_btc",
        (
            "btc_spot_reference_price",
            "crypto_derivatives_market_data",
            "etf_flow_or_onchain_source",
            "credible_crypto_news_wire",
        ),
        15,
        (
            "exchange_outage_or_bad_tick",
            "liquidity_cascade",
            "oracle_or_index_dislocation",
            "unverified_social_rumor",
        ),
        4,
    ),
    (
        "equity_index",
        (
            "index_provider_or_exchange_reference",
            "futures_or_options_market_data",
            "macro_calendar_source",
            "market_news_wire",
        ),
        30,
        (
            "market_holiday_or_early_close",
            "futures_cash_basis_dislocation",
            "macro_release_revision",
            "headline_vs_settlement_mismatch",
        ),
        4,
    ),
    (
        "commodities_gold",
        (
            "spot_or_futures_price_reference",
            "real_yield_or_rates_source",
            "central_bank_or_etf_flow_source",
            "macro_calendar_source",
        ),
        60,
        (
            "usd_real_yield_regime_shift",
            "thin_session_price_spike",
            "contract_roll_or_fixing_mismatch",
            "flow_data_revision",
        ),
        4,
    ),
    (
        "soccer",
        (
            "official_competition_fixture_source",
            "team_lineup_or_injury_source",
            "odds_or_market_price_source",
            "credible_local_sports_news",
        ),
        30,
        (
            "late_lineup_rotation",
            "fixture_postponement_or_weather_delay",
            "transfer_registration_uncertainty",
            "local_reporter_false_positive",
        ),
        4,
    ),
    (
        "basketball",
        (
            "official_league_injury_report",
            "team_depth_chart_or_rotation_source",
            "odds_or_market_price_source",
            "beat_reporter_or_local_news",
        ),
        30,
        (
            "late_scratch_or_minutes_limit",
            "back_to_back_rest_distortion",
            "coach_rotation_signal_noise",
            "beat_reporter_false_positive",
        ),
        4,
    ),
    (
        "other_sports",
        (
            "official_event_or_league_source",
            "participant_status_source",
            "odds_or_market_price_source",
        ),
        60,
        (
            "withdrawal_or_retirement_risk",
            "weather_or_venue_change",
            "low_liquidity_price_noise",
        ),
        3,
    ),
    (
        "general",
        (
            "official_primary_source",
            "credible_secondary_source",
            "market_price_source",
        ),
        120,
        (
            "unclear_team_ownership",
            "ambiguous_resolution_criteria",
            "insufficient_source_depth",
        ),
        3,
    ),
)


def _normalize_entries(
    entries: tuple[StrategyResearchTeamPlaybookEntry, ...],
) -> tuple[StrategyResearchTeamPlaybookEntry, ...]:
    if type(entries) is not tuple:
        raise ValueError("entries must be a tuple")
    for entry in entries:
        if type(entry) is not StrategyResearchTeamPlaybookEntry:
            raise ValueError("entries must contain StrategyResearchTeamPlaybookEntry values")
        require_paper_only_flags("StrategyResearchTeamPlaybookEntry", entry)
    return entries


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized = tuple(_require_canonical_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_positive_int(field_name: str, value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")
    return value
