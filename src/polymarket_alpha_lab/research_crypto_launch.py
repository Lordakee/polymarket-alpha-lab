"""Prospective BTC/ETH research specifications and auditable in-memory previews.

No DB, credentials, model or network. A successful preview is input readiness,
not a forecast. Market rules are context, not independent evidence or an oracle.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json

from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.research_resolution import condition, utc
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits, hard_flags, identifier, integer, strict_json, text
from polymarket_alpha_lab.team_research_crypto_candles import CoinbaseCandleSnapshot, CryptoCandleWindow, PRODUCTS
from polymarket_alpha_lab.team_research_cross_source import CrossSourcePolicy, check_crypto_cross_source
from polymarket_alpha_lab.team_research_intake import (
    GammaMarketSnapshot, _ContextRejected, _digest, _market_context, _timestamp,
    prepare_team_research_from_gamma, require_market_slug,
)
from polymarket_alpha_lab.team_research_kraken_candles import KrakenCandleSnapshot

VERSION = 'crypto-launch-v1'


class CryptoLaunchBlocked(ValueError):
    """Fixed-code input/market rejection before any research claim is created."""


def _hash(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                             allow_nan=False, default=str).encode('utf-8')).hexdigest()


@dataclass(frozen=True, slots=True)
class CryptoResearchSpec:
    record_id: str
    team_id: str
    condition_id: str
    market_slug: str
    forecast_cutoff_at: datetime
    model_id: str
    lookback_hours: int = 3
    limits: ResearchAgentLimits = ResearchAgentLimits()
    policy: CrossSourcePolicy = CrossSourcePolicy()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        identifier('record_id', self.record_id)
        if type(self.team_id) is not str or self.team_id not in PRODUCTS:
            raise ValueError('crypto_launch_team_unsupported')
        condition(self.condition_id)
        require_market_slug(self.market_slug)
        object.__setattr__(self, 'forecast_cutoff_at', utc('forecast cutoff', self.forecast_cutoff_at))
        text('model_id', self.model_id, 128)
        integer('lookback_hours', self.lookback_hours, 1, 24)
        if type(self.limits) is not ResearchAgentLimits or type(self.policy) is not CrossSourcePolicy:
            raise ValueError('crypto_launch_configuration_invalid')
        object.__setattr__(self, 'limits', replace(self.limits))
        object.__setattr__(self, 'policy', replace(self.policy))
        hard_flags(self)

    def protocol(self) -> str:
        self.__post_init__()
        # A cohort is a research configuration, never a task/event fingerprint.
        # Team and model are separate evaluator grouping keys. Task scope and
        # terms approval are checked separately on replay.
        # Exact ratios canonicalize 100 vs 100.00 without Decimal context rounding.
        return VERSION + ':' + _hash({'lookback_hours': self.lookback_hours,
            'limits': asdict(self.limits), 'policy': {
                'max_close_divergence_ratio': self.policy.max_close_divergence_bps.as_integer_ratio(),
                'max_capture_skew_seconds': self.policy.max_capture_skew_seconds}})


def copy_spec(spec: CryptoResearchSpec) -> CryptoResearchSpec:
    if type(spec) is not CryptoResearchSpec:
        raise ValueError('crypto_launch_spec_invalid')
    return replace(spec)


def candle_window(spec: CryptoResearchSpec, selected_at: datetime) -> CryptoCandleWindow:
    spec = copy_spec(spec)
    end = utc('selected_at', selected_at).replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    return CryptoCandleWindow(PRODUCTS[spec.team_id], end - timedelta(hours=spec.lookback_hours), end)


def terms_digest(spec: CryptoResearchSpec, question: str, rules: str) -> str:
    spec = copy_spec(spec)
    text('question', question, 2000)
    text('resolution_criteria', rules, 4000)
    return _hash(dict(condition_id=spec.condition_id, market_slug=spec.market_slug,
        question=question, resolution_criteria=rules, team_id=spec.team_id,
        forecast_cutoff_at=spec.forecast_cutoff_at.isoformat()))


def market_terms(spec: CryptoResearchSpec, snapshot: GammaMarketSnapshot, at: datetime) -> dict:
    """Reuse the audited market gate; approval binds rules, not moving quotes.

    The explicit prediction cutoff must precede the scheduled market end. The
    end date is not inferred to be the actual resolution timestamp. Team/source
    relevance must be reviewed by the operator, not asserted by this parser.
    """
    spec = copy_spec(spec)
    if type(snapshot) is not GammaMarketSnapshot:
        raise ValueError('crypto_launch_snapshot_invalid')
    snapshot = replace(snapshot, fetched_at=utc('fetched_at', snapshot.fetched_at))
    at = utc('as_of', at)
    if snapshot.market_slug != spec.market_slug:
        raise CryptoLaunchBlocked('crypto_launch_market_scope_mismatch')
    if at >= spec.forecast_cutoff_at:
        raise CryptoLaunchBlocked('crypto_launch_cutoff_elapsed')
    try:
        question, rules = _market_context(snapshot, spec.condition_id, at, 300)
        end = _timestamp(strict_json(snapshot.raw_json.decode('utf-8'))['endDate'])
    except _ContextRejected as error:
        raise CryptoLaunchBlocked(str(error)) from None
    if spec.forecast_cutoff_at >= end:
        raise CryptoLaunchBlocked('crypto_launch_cutoff_not_before_market_end')
    terms = dict(condition_id=spec.condition_id, market_slug=spec.market_slug,
                 question=question, resolution_criteria=rules, scheduled_end_at=end.isoformat(),
                 forecast_cutoff_at=spec.forecast_cutoff_at.isoformat(), team_id=spec.team_id)
    return dict(terms, terms_sha256=terms_digest(spec, question, rules))


@dataclass(frozen=True, slots=True)
class CryptoResearchPreview:
    spec: CryptoResearchSpec
    selected_at: datetime
    as_of: datetime
    market: GammaMarketSnapshot = field(repr=False)
    coinbase: CoinbaseCandleSnapshot = field(repr=False)
    kraken: KrakenCandleSnapshot = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'spec', copy_spec(self.spec))
        for name in ('selected_at', 'as_of'):
            object.__setattr__(self, name, utc(name, getattr(self, name)))
        if self.selected_at > self.as_of:
            raise ValueError('crypto_launch_clock_invalid')
        for name, cls in (('market', GammaMarketSnapshot), ('coinbase', CoinbaseCandleSnapshot),
                          ('kraken', KrakenCandleSnapshot)):
            item = getattr(self, name)
            if type(item) is not cls:
                raise ValueError('crypto_launch_snapshot_invalid')
            item = replace(item, fetched_at=utc('fetched_at', item.fetched_at))
            if not self.selected_at <= item.fetched_at <= self.as_of:
                raise CryptoLaunchBlocked('crypto_launch_snapshot_clock_invalid')
            object.__setattr__(self, name, item)
        expected = candle_window(self.spec, self.selected_at)
        if self.coinbase.window != expected or self.kraken.window != expected:
            raise CryptoLaunchBlocked('crypto_launch_window_mismatch')
        self._prepared()

    def _prepared(self):
        terms = market_terms(self.spec, self.market, self.as_of)
        check = check_crypto_cross_source(self.coinbase, self.kraken, team_id=self.spec.team_id,
            condition_id=self.spec.condition_id, as_of=self.as_of, policy=self.spec.policy,
            max_evidence_age_seconds=self.spec.limits.max_evidence_age_seconds)
        if check.status != 'matched':
            raise CryptoLaunchBlocked(check.reason_code)
        intake = prepare_team_research_from_gamma(self.market, task_id=self.spec.record_id,
            team_id=self.spec.team_id, condition_id=self.spec.condition_id, as_of=self.as_of,
            evidence=check.evidence, limits=self.spec.limits)
        if intake.status != 'prepared':
            raise CryptoLaunchBlocked(intake.reason_code)
        return terms, check, intake

    def request(self, *, approved_terms_sha256: str) -> CapturedResearchRequest:
        self.__post_init__()
        terms, check, intake = self._prepared()
        _digest(approved_terms_sha256)
        if approved_terms_sha256 != terms['terms_sha256']:
            raise CryptoLaunchBlocked('crypto_launch_terms_approval_mismatch')
        return CapturedResearchRequest(self.spec.record_id, self.spec.model_id,
            self.spec.protocol(), self.spec.forecast_cutoff_at, intake,
            limits=self.spec.limits, required_source_ids=tuple(r.source_id for r in check.source_receipts))

    def to_dict(self) -> dict:
        self.__post_init__()
        terms, check, _ = self._prepared()
        return dict(status='prepared', readiness_only=True, record_id=self.spec.record_id,
            model_id=self.spec.model_id, selected_at=self.selected_at.isoformat(), as_of=self.as_of.isoformat(),
            **terms, window_start=check.window.start.isoformat(), window_end=check.window.end.isoformat(),
            compared_candles=len(check.close_divergences_bps),
            max_close_divergence_bps=str(check.max_observed_divergence_bps),
            market_sha256=self.market.content_sha256, coinbase_sha256=check.coinbase_raw_sha256,
            kraken_sha256=check.kraken_raw_sha256,
            required_source_ids=[r.source_id for r in check.source_receipts],
            limits=asdict(self.spec.limits), paper_only=True, report_only=True, readonly=True,
            model_called=False, database_written=False)


__all__ = ('CryptoResearchSpec', 'CryptoResearchPreview', 'CryptoLaunchBlocked')
