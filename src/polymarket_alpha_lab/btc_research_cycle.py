"""Backward-compatible BTC wrapper over the generalized crypto cycle.

The public API (`run_btc_research_cycle`, `BtcCycleResult`) is
unchanged from M3 except for one documented identity-format change:
cycle ids are now produced by the generalized reducer and include the
team id in the hash payload. Outputs (forecast, evidence packets,
operator packet) are byte-stable for identical inputs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

from .central_data_db_row import NormalizedObservationRow
from .central_evidence_bundle import EvidenceBundle
from .crypto_btc_evidence_adapter import adapt_btc_evidence
from .crypto_btc_team import CryptoBtcTeamConfig, build_crypto_btc_team_forecast
from .crypto_research_cycle import CryptoCycleResult, run_crypto_research_cycle

BtcCycleResult = CryptoCycleResult


def run_btc_research_cycle(
    *,
    bundle: EvidenceBundle,
    metadata_observation: NormalizedObservationRow | None,
    book_observation: NormalizedObservationRow | None,
    spot_observation: NormalizedObservationRow | None,
    as_of: datetime,
    generated_at: datetime,
    config: CryptoBtcTeamConfig,
    market_slug_hint: str = "unknown-market",
    condition_id_hint: str = "unknown-condition",
) -> BtcCycleResult:
    return run_crypto_research_cycle(
        team_id="crypto_btc",
        spot_item="btc_spot_price",
        bundle=bundle,
        metadata_observation=metadata_observation,
        book_observation=book_observation,
        spot_observation=spot_observation,
        as_of=as_of,
        generated_at=generated_at,
        config=config,
        adapt_evidence=adapt_btc_evidence,
        build_forecast=build_crypto_btc_team_forecast,
        market_slug_hint=market_slug_hint,
        condition_id_hint=condition_id_hint,
    )


__all__ = ("BtcCycleResult", "run_btc_research_cycle")
