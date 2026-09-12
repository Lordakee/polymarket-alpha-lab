"""Bounded, in-process batches of supplied-input team forecasts.

This is not autonomous research, the BTC policy/persistence service, a
publication gate, or strategy-cycle wiring. No network or durable writes.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType

from polymarket_alpha_lab import (
    commodities_gold_team as gold,
    commodities_oil_team as oil,
    crypto_btc_team as btc,
    crypto_eth_team as eth,
    equity_indices_team as equities,
    macro_rates_team as macro,
    politics_team as politics,
    sports_basketball_team as basketball,
    sports_other_team as other_sports,
    sports_soccer_team as soccer,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


_Builder = Callable[..., tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]]
_Team = tuple[type, type, _Builder]


# Fixed local implementations only. A caller cannot supply a plugin or worker.
_TEAMS = MappingProxyType({
    "politics": (politics.PoliticsTeamConfig, politics.PoliticsEvidenceInput,
                 politics.build_politics_team_forecast),
    "crypto_btc": (btc.CryptoBtcTeamConfig, btc.CryptoBtcEvidenceInput,
                   btc.build_crypto_btc_team_forecast),
    "crypto_eth": (eth.CryptoEthTeamConfig, eth.CryptoEthEvidenceInput,
                   eth.build_crypto_eth_team_forecast),
    "macro_rates": (macro.MacroRatesTeamConfig, macro.MacroRatesEvidenceInput,
                    macro.build_macro_rates_team_forecast),
    "equity_indices": (equities.EquityIndicesTeamConfig, equities.EquityIndicesEvidenceInput,
                       equities.build_equity_indices_team_forecast),
    "commodities_gold": (gold.CommoditiesGoldTeamConfig, gold.CommoditiesGoldEvidenceInput,
                         gold.build_commodities_gold_team_forecast),
    "commodities_oil": (oil.CommoditiesOilTeamConfig, oil.CommoditiesOilEvidenceInput,
                        oil.build_commodities_oil_team_forecast),
    "sports_soccer": (soccer.SportsSoccerTeamConfig, soccer.SportsSoccerEvidenceInput,
                      soccer.build_sports_soccer_team_forecast),
    "sports_basketball": (basketball.SportsBasketballTeamConfig, basketball.SportsBasketballEvidenceInput,
                          basketball.build_sports_basketball_team_forecast),
    "sports_other": (other_sports.SportsOtherTeamConfig, other_sports.SportsOtherEvidenceInput,
                     other_sports.build_sports_other_team_forecast),
})
SUPPORTED_TEAM_IDS = tuple(_TEAMS)


def _text(name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _team(team_id: str) -> _Team:
    if type(team_id) is not str or team_id not in _TEAMS:
        raise ValueError("team_id must identify a supported supplied-input team")
    return _TEAMS[team_id]


@dataclass(frozen=True, slots=True)
class TeamForecastBatchRequest:
    request_id: str
    team_id: str
    condition_id: str
    market_slug: str
    question: str
    event_template: str
    base_probability: Decimal
    config: object
    evidence: tuple[object, ...]
    generated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("request_id", "condition_id", "market_slug", "question", "event_template"):
            _text(name, getattr(self, name))
        config_type, evidence_type, _ = _team(self.team_id)
        require_paper_only_flags("batch request", self)
        if type(self.config) is not config_type:
            raise ValueError("config must match the exact team config type")
        require_paper_only_flags("batch config", self.config)
        if type(self.evidence) is not tuple or not self.evidence:
            raise ValueError("evidence must be a nonempty tuple")
        if (type(self.base_probability) is not Decimal
                or not self.base_probability.is_finite()
                or not Decimal(0) <= self.base_probability <= Decimal(1)):
            raise ValueError("base_probability must be a finite Decimal in [0, 1]")
        if (type(self.generated_at) is not datetime
                or self.generated_at.tzinfo is None
                or self.generated_at.utcoffset() is None):
            raise ValueError("generated_at must be an aware datetime")
        source_ids = []
        for item in self.evidence:
            if type(item) is not evidence_type:
                raise ValueError("evidence must match the exact team evidence type")
            require_paper_only_flags("batch evidence", item)
            source_ids.append(item.source_id)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("evidence source_id values must be unique within a request")


@dataclass(frozen=True, slots=True)
class TeamForecastBatchOutcome:
    request_id: str
    team_id: str
    condition_id: str
    market_slug: str
    status: str
    forecast: TeamForecastPacket | None
    evidence: tuple[TeamForecastEvidencePacket, ...]
    reason_code: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for name in ("request_id", "condition_id", "market_slug"):
            _text(name, getattr(self, name))
        _team(self.team_id)
        require_paper_only_flags("batch outcome", self)
        if type(self.evidence) is not tuple:
            raise ValueError("outcome evidence must be a tuple")
        if type(self.status) is not str:
            raise ValueError("status must be built or failed")
        if self.status == "failed":
            if (self.forecast is not None or self.evidence
                    or self.reason_code != "team_forecast_build_failed"):
                raise ValueError("failed outcome must suppress all packets")
        elif self.status == "built":
            if (type(self.forecast) is not TeamForecastPacket or not self.evidence
                    or self.reason_code != "team_forecast_built"):
                raise ValueError("built outcome must contain forecast and evidence packets")
            require_paper_only_flags("batch forecast", self.forecast)
            if (self.forecast.team_id != self.team_id
                    or self.forecast.condition_id != self.condition_id
                    or self.forecast.market_slug != self.market_slug):
                raise ValueError("forecast identity must match the batch outcome")
            for item in self.evidence:
                if type(item) is not TeamForecastEvidencePacket:
                    raise ValueError("outcome evidence must contain exact evidence packets")
                require_paper_only_flags("batch evidence packet", item)
                if item.team_id != self.team_id or item.market_slug != self.market_slug:
                    raise ValueError("evidence identity must match the batch outcome")
        else:
            raise ValueError("status must be built or failed")


def _snapshot(request: TeamForecastBatchRequest) -> TeamForecastBatchRequest:
    """Reconstruct nested inputs before any worker is started."""
    if type(request) is not TeamForecastBatchRequest:
        raise ValueError("requests must contain exact TeamForecastBatchRequest values")
    try:
        request.__post_init__()
        config = replace(request.config)
        evidence = tuple(replace(item) for item in request.evidence)
        return replace(request, config=config, evidence=evidence)
    except Exception:
        # Never expose data or exception text supplied through a builder input.
        raise ValueError("invalid supplied-input batch request") from None


def _build_one(request: TeamForecastBatchRequest) -> TeamForecastBatchOutcome:
    _, _, builder = _team(request.team_id)
    try:
        forecast, evidence = builder(
            condition_id=request.condition_id, market_slug=request.market_slug,
            question=request.question, event_template=request.event_template,
            base_probability=request.base_probability, config=request.config,
            evidence=request.evidence, generated_at=request.generated_at,
        )
        if type(forecast) is not TeamForecastPacket or type(evidence) is not tuple:
            raise ValueError("invalid builder packet types")
        if len(evidence) != len(request.evidence):
            raise ValueError("builder evidence count mismatch")
        forecast = replace(forecast)
        evidence = tuple(replace(item) for item in evidence)
        if (forecast.generated_at != request.generated_at
                or tuple(item.source_id for item in evidence)
                != tuple(item.source_id for item in request.evidence)):
            raise ValueError("builder provenance mismatch")
        return TeamForecastBatchOutcome(
            request.request_id, request.team_id, request.condition_id, request.market_slug,
            "built", forecast, evidence, "team_forecast_built",
        )
    except Exception:
        # A failed job cannot leak an exception, partial packet, or ready status.
        return TeamForecastBatchOutcome(
            request.request_id, request.team_id, request.condition_id, request.market_slug,
            "failed", None, (), "team_forecast_build_failed",
        )


def run_team_forecast_batch(
    requests: tuple[TeamForecastBatchRequest, ...], *, max_workers: int = 4,
) -> tuple[TeamForecastBatchOutcome, ...]:
    """Validate all input first; build concurrently; return in input order.

    Invalid requests fail the entire batch before any builder starts. Valid
    requests whose builders fail return redacted, packetless failed outcomes.
    `built` means construction only, never publication/risk/quality approval.
    The call returns only after all workers have finished and been joined.
    """
    if type(requests) is not tuple:
        raise ValueError("requests must be a tuple")
    if type(max_workers) is not int or max_workers < 1:
        raise ValueError("max_workers must be a positive int")
    snapshots = tuple(_snapshot(request) for request in requests)
    ids = tuple(request.request_id for request in snapshots)
    if len(set(ids)) != len(ids):
        raise ValueError("request_id values must be unique within a batch")
    if not snapshots:
        return ()
    workers = min(max_workers, len(snapshots))
    if workers == 1:
        return tuple(_build_one(request) for request in snapshots)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="team-forecast") as pool:
        return tuple(pool.map(_build_one, snapshots))


__all__ = (
    "SUPPORTED_TEAM_IDS", "TeamForecastBatchRequest", "TeamForecastBatchOutcome",
    "run_team_forecast_batch",
)
