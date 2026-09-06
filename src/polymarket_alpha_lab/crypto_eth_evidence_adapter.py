"""Pure ETH evidence adapter: M2 bundle rows to crypto_eth team inputs.

The adapter maps ready evidence to descriptive ``CryptoEthEvidenceInput``
rows and blocked items to zero-weight reason-coded rows. It never invents
a probability impact: in this slice every impact is exactly zero because
no reviewed model justifies moving canonical P(YES) from spot price alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from .central_data_db_row import NormalizedObservationRow, TypedEnvelope
from .central_evidence_bundle import (
    EvidenceBundle,
    EvidenceItemAvailability,
    SelectedEvidence,
    ZeroWeightPlaceholder,
)
from .crypto_eth_team import CryptoEthEvidenceInput


ADAPTER_VERSION = "crypto-eth-evidence-v1"
ETH_SPOT_ITEM = "eth_spot_price"
GAMMA_ITEM = "gamma_market_metadata"
CLOB_ITEM = "clob_book_depth"
_READY_WEIGHT = Decimal("0.500000")
_FRESHNESS_HORIZON_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class EthEvidenceAdaptation:
    inputs: tuple[CryptoEthEvidenceInput, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.inputs, tuple):
            raise ValueError("inputs must be a tuple")
        for code in self.reason_codes:
            if type(code) is not str or not code or code.strip() != code:
                raise ValueError("reason_codes must contain canonical strings")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must not contain duplicates")


def _freshness_seconds(reference: datetime, moment: datetime) -> int:
    seconds = int((reference - moment).total_seconds())
    return max(0, min(seconds, _FRESHNESS_HORIZON_SECONDS))


def adapt_eth_evidence(
    bundle: EvidenceBundle,
    *,
    observations_by_item: dict[str, NormalizedObservationRow],
    as_of: datetime,
) -> EthEvidenceAdaptation:
    """Map one evidence bundle to canonical crypto_eth evidence inputs."""

    if type(bundle) is not EvidenceBundle:
        raise ValueError("bundle must be an EvidenceBundle")
    if bundle.team_id != "crypto_eth":
        raise ValueError("bundle must belong to crypto_eth")
    inputs: list[CryptoEthEvidenceInput] = []
    reasons: list[str] = []

    for item_name in sorted(bundle.items):
        entry = bundle.items[item_name]
        if type(entry) is ZeroWeightPlaceholder:
            inputs.append(
                CryptoEthEvidenceInput(
                    source_id=f"central:{item_name}",
                    source_type="central_evidence",
                    evidence_text=f"blocked item {item_name}: {entry.availability.value}",
                    data_timestamp=as_of,
                    data_freshness_seconds=_FRESHNESS_HORIZON_SECONDS,
                    evidence_type="blocked_availability",
                    weight=Decimal("0"),
                    probability_impact=Decimal("0"),
                    reason_codes=entry.reason_codes,
                )
            )
            reasons.append(f"{item_name}_{entry.availability.value}")
            continue
        row = observations_by_item.get(item_name)
        if row is None:
            inputs.append(
                CryptoEthEvidenceInput(
                    source_id=f"central:{item_name}",
                    source_type="central_evidence",
                    evidence_text=f"selected evidence missing for {item_name}",
                    data_timestamp=as_of,
                    data_freshness_seconds=_FRESHNESS_HORIZON_SECONDS,
                    evidence_type="missing_observation",
                    weight=Decimal("0"),
                    probability_impact=Decimal("0"),
                    reason_codes=("selected_observation_unavailable",),
                )
            )
            reasons.append(f"{item_name}_selected_observation_unavailable")
            continue
        value = TypedEnvelope.decode(dict(row.typed_value))
        summary = _describe(item_name, value, entry)
        inputs.append(
            CryptoEthEvidenceInput(
                source_id=f"central:{entry.source_id}",
                source_type="official" if entry.source_family.startswith("polymarket") else "public",
                evidence_text=summary,
                data_timestamp=row.observation_time,
                data_freshness_seconds=_freshness_seconds(as_of, row.observation_time),
                evidence_type=f"central_{item_name}",
                weight=_READY_WEIGHT,
                probability_impact=Decimal("0"),
                reason_codes=(f"zero_impact_slice_{ADAPTER_VERSION}",),
            )
        )

    return EthEvidenceAdaptation(
        inputs=tuple(inputs),
        reason_codes=tuple(sorted(set(reasons))),
    )


def _describe(item_name: str, value: object, selected: SelectedEvidence) -> str:
    if item_name == ETH_SPOT_ITEM and isinstance(value, dict):
        parts = [
            f"{key}={_plain(item)}"
            for key, item in sorted(value.items())
            if key in {"last_price", "ask_price", "bid_price", "pair"}
        ]
        detail = " ".join(parts) if parts else "spot observation"
        return (
            f"eth spot via {selected.source_family} at "
            f"{selected.observation_time.isoformat()}: {detail}"
        )
    if item_name == CLOB_ITEM and isinstance(value, dict):
        bids = value.get("bids")
        asks = value.get("asks")
        return (
            f"clob book via {selected.source_family}: "
            f"{len(bids) if isinstance(bids, list) else 0} bids, "
            f"{len(asks) if isinstance(asks, list) else 0} asks"
        )
    if item_name == GAMMA_ITEM and isinstance(value, dict):
        question = value.get("question")
        return (
            f"gamma market via {selected.source_family}: "
            f"{question if isinstance(question, str) else 'metadata'}"
        )
    return f"{item_name} observation via {selected.source_family}"


def _plain(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, str):
        return value
    return "present"


__all__ = (
    "ADAPTER_VERSION",
    "EthEvidenceAdaptation",
    "ETH_SPOT_ITEM",
    "CLOB_ITEM",
    "GAMMA_ITEM",
    "adapt_eth_evidence",
)
