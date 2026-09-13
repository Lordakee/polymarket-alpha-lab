"""One-shot public preview and explicit, captured native-PostgreSQL research.

No credential reads or automatic model selection. Use a caller-approved model
factory, the existing three public readers and existing at-most-once claim path.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_capture_psycopg import ResearchCaptureConflict
from polymarket_alpha_lab.research_crypto_launch import (
    CryptoLaunchBlocked, CryptoResearchPreview, CryptoResearchSpec, candle_window, copy_spec, market_terms, terms_digest,
)
from polymarket_alpha_lab.team_research_coinbase import CoinbaseCandleReader
from polymarket_alpha_lab.team_research_gamma import GammaResearchReader
from polymarket_alpha_lab.team_research_intake import _digest
from polymarket_alpha_lab.team_research_kraken import KrakenCandleReader


def _now() -> datetime:
    return datetime.now(UTC)


def _enabled(name: str, value: object) -> None:
    if value is not True:
        raise ValueError(name + '_requires_explicit_opt_in')


def fetch_crypto_research_preview(spec: CryptoResearchSpec, *, allow_public_fetch: bool = False) -> CryptoResearchPreview:
    """At most three explicit public GETs, never a DB write or model invocation.

    Capture raw bytes in memory before normalization; no file persistence. A
    transport/data gate failure raises a fixed code and does not invent evidence.
    Public-source applicability to this market still requires operator review.
    """
    spec = copy_spec(spec)
    _enabled('crypto_launch_public_fetch', allow_public_fetch)
    selected = _now()
    if selected >= spec.forecast_cutoff_at:
        raise CryptoLaunchBlocked('crypto_launch_cutoff_elapsed')
    try:
        market = GammaResearchReader(allow_public_fetch=True).fetch(market_slug=spec.market_slug)
    except Exception:
        raise CryptoLaunchBlocked('crypto_launch_gamma_fetch_failed') from None
    # Reject an ineligible event before spending two more public requests.
    market_terms(spec, market, _now())
    window = candle_window(spec, selected)
    try:
        coinbase = CoinbaseCandleReader(True).fetch(window)
    except Exception:
        raise CryptoLaunchBlocked('crypto_launch_coinbase_fetch_failed') from None
    try:
        kraken = KrakenCandleReader(True).fetch(window)
    except Exception:
        raise CryptoLaunchBlocked('crypto_launch_kraken_fetch_failed') from None
    return CryptoResearchPreview(spec, selected, _now(), market, coinbase, kraken)


def launch_crypto_research_with_psycopg(
    dsn: str, *, spec: CryptoResearchSpec, approved_terms_sha256: str, model_factory,
    allow_public_fetch: bool = False, allow_model_calls: bool = False,
    preview: CryptoResearchPreview | None = None,
):
    """Reuse existing captured runner: commit registration/claim BEFORE model.

    Read an existing record first. Exact configuration/approval replay returns
    its original captured/incomplete state without fetching or calling a model.
    A NEW request is derived from validated current snapshots and requires both
    source citations. Concurrent preparations can duplicate public GETs; the
    existing claim enforces at most one research loop, never exactly-once HTTP.

    Preflight failures occur before a research claim and are NOT stored attempts.
    Once claimed, normal model/factory failure is captured by the existing runner.
    That runner also retains incomplete/capture_failed states; no automatic retry.
    model_id is a caller assertion: this module cannot attest which provider/model
    an injected factory actually uses. Approval hashes bind terms, not truth.
    """
    spec = copy_spec(spec)
    _digest(approved_terms_sha256)
    _enabled('crypto_launch_public_fetch', allow_public_fetch)
    _enabled('crypto_launch_model_calls', allow_model_calls)
    if not callable(model_factory):
        raise ValueError('crypto_launch_model_factory_invalid')
    if preview is not None:
        if type(preview) is not CryptoResearchPreview:
            raise ValueError('crypto_launch_preview_invalid')
        preview = replace(preview)
        if preview.spec != spec:
            raise ValueError('crypto_launch_preview_scope_mismatch')
    existing = execution.inspect_captured_research_with_psycopg(dsn, record_id=spec.record_id)
    if existing is not None:
        request = existing.request
        if (request.protocol_version != spec.protocol()
                or request.record_id != spec.record_id or request.model_id != spec.model_id
                or request.forecast_cutoff_at != spec.forecast_cutoff_at
                or request.intake.task_id != spec.record_id or request.intake.team_id != spec.team_id
                or request.intake.condition_id != spec.condition_id or request.intake.market_slug != spec.market_slug
                or request.limits != spec.limits or request.intake.task is None
                or terms_digest(spec, request.intake.task.question, request.intake.task.resolution_criteria)
                != approved_terms_sha256):
            raise ResearchCaptureConflict('crypto_launch_existing_request_conflict')
        return existing
    if preview is None:
        preview = fetch_crypto_research_preview(spec, allow_public_fetch=True)
    # The existing runner rechecks data age and future cutoff against DB time
    # inside the claim transaction. A delayed preview cannot backdate a forecast.
    request = preview.request(approved_terms_sha256=approved_terms_sha256)
    return execution.run_captured_research_with_psycopg(dsn, request=request, model_factory=model_factory)


__all__ = ('fetch_crypto_research_preview', 'launch_crypto_research_with_psycopg')
