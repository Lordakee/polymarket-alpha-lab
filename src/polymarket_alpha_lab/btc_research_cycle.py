"""Pure BTC research-cycle reducer and operator packet renderer.

The reducer wires accepted M1/M2 outputs into the existing crypto_btc
forecast builder. It performs no I/O, reads no clock beyond the provided
``generated_at``/``as_of`` values, and derives base probability from the
YES token's executable book. Each observation window is a distinct cycle
with a deterministic input-derived identity; retry safety is row-level
idempotency in the persistence layers, not identity reuse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
from typing import Iterable, Mapping

from .central_data_db_row import NormalizedObservationRow, TypedEnvelope
from .central_evidence_bundle import EvidenceBundle, EvidenceBundleStatus
from .crypto_btc_evidence_adapter import (
    BTC_SPOT_ITEM,
    CLOB_ITEM,
    GAMMA_ITEM,
    adapt_btc_evidence,
)
from .crypto_btc_team import (
    CryptoBtcEvidenceInput,
    CryptoBtcTeamConfig,
    build_crypto_btc_team_forecast,
)
from .team_forecast_packet import TeamForecastEvidencePacket, TeamForecastPacket


BTC_CYCLE_VERSION = "btc-research-cycle-v1"


@dataclass(frozen=True)
class BtcCycleResult:
    status: str
    cycle_id: str
    condition_id: str
    market_slug: str
    reason_codes: tuple[str, ...]
    forecast: TeamForecastPacket | None
    evidence_packets: tuple[TeamForecastEvidencePacket, ...]
    base_probability: Decimal | None
    operator_packet: str

    def __post_init__(self) -> None:
        if self.status not in {"ready", "blocked"}:
            raise ValueError("status must be ready or blocked")
        for name in ("cycle_id", "condition_id", "market_slug"):
            value = getattr(self, name)
            if type(value) is not str or not value or value.strip() != value:
                raise ValueError(f"{name} must be a canonical nonblank string")
        for code in self.reason_codes:
            if type(code) is not str or not code or code.strip() != code:
                raise ValueError("reason_codes must contain canonical strings")
        if self.status == "ready" and (self.forecast is None or self.base_probability is None):
            raise ValueError("ready cycles require a forecast and base probability")
        if self.status == "blocked" and self.forecast is not None:
            raise ValueError("blocked cycles must not carry a forecast")


def _yes_token_id(metadata_value: Mapping[str, object]) -> str | None:
    """Extract the affirmative token id from Gamma metadata.

    The token is identified only by mapping ``clobTokenIds`` to an outcome
    labeled "yes" (case-insensitive).  When no such label exists the
    affirmative token is genuinely unidentified and the caller blocks the
    cycle; positional fallback is deliberately refused because a reversed
    outcome ordering would silently invert the forecast.
    """

    tokens = metadata_value.get("clob_token_ids")
    outcomes = metadata_value.get("outcomes")
    if not isinstance(tokens, list) or not tokens or not isinstance(outcomes, list):
        return None
    for index, outcome in enumerate(outcomes):
        if isinstance(outcome, str) and outcome.strip().lower() == "yes" and index < len(tokens):
            token = tokens[index]
            if isinstance(token, str) and token.strip():
                return token
    return None


def _book_extremes(book_value: Mapping[str, object]) -> tuple[Decimal, Decimal] | None:
    bids = book_value.get("bids")
    asks = book_value.get("asks")
    if not isinstance(bids, list) or not isinstance(asks, list) or not bids or not asks:
        return None
    bid_prices = [entry.get("price") for entry in bids if isinstance(entry, dict)]
    ask_prices = [entry.get("price") for entry in asks if isinstance(entry, dict)]
    if not all(isinstance(price, Decimal) for price in bid_prices + ask_prices):
        return None
    return max(bid_prices), min(ask_prices)  # type: ignore[arg-type]


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
    if type(bundle) is not EvidenceBundle or bundle.team_id != "crypto_btc":
        raise ValueError("bundle must be a crypto_btc EvidenceBundle")
    if type(config) is not CryptoBtcTeamConfig:
        raise ValueError("config must be a CryptoBtcTeamConfig")

    reasons: list[str] = list(bundle.reason_codes)
    metadata_value = (
        TypedEnvelope.decode(dict(metadata_observation.typed_value))
        if metadata_observation is not None
        else None
    )
    book_value = (
        TypedEnvelope.decode(dict(book_observation.typed_value))
        if book_observation is not None
        else None
    )
    spot_value = (
        TypedEnvelope.decode(dict(spot_observation.typed_value))
        if spot_observation is not None
        else None
    )

    question = "unknown question"
    condition_id = condition_id_hint
    market_slug = market_slug_hint
    if metadata_value is None:
        reasons.append("metadata_observation_missing")
    elif isinstance(metadata_value, Mapping):
        raw_question = metadata_value.get("question")
        if isinstance(raw_question, str) and raw_question:
            question = raw_question
        raw_condition = metadata_value.get("condition_id")
        if isinstance(raw_condition, str) and raw_condition:
            condition_id = raw_condition
        raw_slug = metadata_value.get("slug")
        if isinstance(raw_slug, str) and raw_slug:
            market_slug = raw_slug
    else:
        reasons.append("metadata_shape_invalid")

    yes_token = _yes_token_id(metadata_value) if isinstance(metadata_value, Mapping) else None
    if yes_token is None:
        reasons.append("yes_token_unidentified")

    base_probability: Decimal | None = None
    if book_value is None:
        reasons.append("book_observation_missing")
    elif isinstance(book_value, Mapping):
        extremes = _book_extremes(book_value)
        if extremes is None:
            reasons.append("book_empty_or_malformed")
        else:
            best_bid, best_ask = extremes
            if best_bid >= best_ask:
                reasons.append("book_crossed")
            else:
                midpoint = (best_bid + best_ask) / Decimal("2")
                if Decimal("0") < midpoint < Decimal("1"):
                    base_probability = midpoint
                else:
                    reasons.append("midpoint_out_of_range")
    else:
        reasons.append("book_shape_invalid")

    if spot_value is None:
        reasons.append("spot_observation_missing")

    blocked_items = sorted(
        name
        for name, entry in bundle.items.items()
        if type(entry).__name__ == "ZeroWeightPlaceholder"
    )
    if bundle.status is EvidenceBundleStatus.BLOCKED:
        reasons.append("bundle_blocked")

    if (
        metadata_value is None
        or book_value is None
        or spot_value is None
        or yes_token is None
        or base_probability is None
        or bundle.status is EvidenceBundleStatus.BLOCKED
    ):
        canonical_reasons = tuple(sorted(set(reasons)))
        cycle_id = _cycle_identity(condition_id, bundle.bundle_id, config, None)
        return BtcCycleResult(
            status="blocked",
            cycle_id=cycle_id,
            condition_id=condition_id,
            market_slug=market_slug,
            reason_codes=canonical_reasons,
            forecast=None,
            evidence_packets=(),
            base_probability=None,
            operator_packet=_render_operator_packet(
                status="blocked",
                cycle_id=cycle_id,
                question=question,
                condition_id=condition_id,
                market_slug=market_slug,
                as_of=as_of,
                yes_token=yes_token,
                base_probability=None,
                bundle=bundle,
                reasons=canonical_reasons,
                forecast=None,
                blocked_items=tuple(blocked_items),
            ),
        )

    observations_by_item = {
        GAMMA_ITEM: metadata_observation,
        CLOB_ITEM: book_observation,
        BTC_SPOT_ITEM: spot_observation,
    }
    adaptation = adapt_btc_evidence(
        bundle,
        observations_by_item=observations_by_item,
        as_of=as_of,
    )
    reasons.extend(adaptation.reason_codes)
    forecast, evidence_packets = build_crypto_btc_team_forecast(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        event_template=question,
        evidence=adaptation.inputs,
        base_probability=base_probability,
        config=config,
        generated_at=generated_at,
    )
    canonical_reasons = tuple(sorted(set(reasons)))
    cycle_id = _cycle_identity(condition_id, bundle.bundle_id, config, base_probability)
    return BtcCycleResult(
        status="ready",
        cycle_id=cycle_id,
        condition_id=condition_id,
        market_slug=market_slug,
        reason_codes=canonical_reasons,
        forecast=forecast,
        evidence_packets=evidence_packets,
        base_probability=base_probability,
        operator_packet=_render_operator_packet(
            status="ready",
            cycle_id=cycle_id,
            question=question,
            condition_id=condition_id,
            market_slug=market_slug,
            as_of=as_of,
            yes_token=yes_token,
            base_probability=base_probability,
            bundle=bundle,
            reasons=canonical_reasons,
            forecast=forecast,
            blocked_items=(),
        ),
    )


def _cycle_identity(
    condition_id: str,
    bundle_id: str,
    config: CryptoBtcTeamConfig,
    base_probability: Decimal | None,
) -> str:
    payload = "|".join(
        (
            BTC_CYCLE_VERSION,
            condition_id,
            bundle_id,
            config.config_version,
            "" if base_probability is None else format(base_probability, "f"),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _render_operator_packet(
    *,
    status: str,
    cycle_id: str,
    question: str,
    condition_id: str,
    market_slug: str,
    as_of: datetime,
    yes_token: str | None,
    base_probability: Decimal | None,
    bundle: EvidenceBundle,
    reasons: tuple[str, ...],
    forecast: TeamForecastPacket | None,
    blocked_items: tuple[str, ...],
) -> str:
    lines = [
        "BTC research cycle",
        f"status: {status}",
        f"cycle_id: {cycle_id}",
        f"market: {market_slug}",
        f"condition_id: {condition_id}",
        f"question: {question}",
        f"as_of: {as_of.isoformat()}",
        f"yes_token: {yes_token if yes_token is not None else 'unidentified'}",
    ]
    if base_probability is not None:
        lines.append(f"base_probability(book midpoint): {format(base_probability, 'f')}")
    lines.append("evidence:")
    for name in sorted(bundle.items):
        entry = bundle.items[name]
        if hasattr(entry, "observation_id"):
            lines.append(
                f"  {name}: ready via {entry.source_family} "
                f"payload={entry.payload_hash} parser={entry.parser_version}"
            )
        else:
            lines.append(f"  {name}: {entry.availability.value} reasons={','.join(entry.reason_codes)}")
    if forecast is not None:
        lines.extend(
            [
                f"forecast_p_yes: {format(forecast.forecast_probability, 'f')}",
                f"selected_side: {forecast.selected_side}",
                f"market_implied_hint: {format(forecast.market_implied_probability_observed, 'f')}",
                f"confidence: {format(forecast.confidence, 'f')}",
            ]
        )
    if blocked_items:
        lines.append(f"blocked_items: {', '.join(blocked_items)}")
    if reasons:
        lines.append(f"reason_codes: {', '.join(reasons)}")
    return "\n".join(lines)


__all__ = (
    "BTC_CYCLE_VERSION",
    "BtcCycleResult",
    "run_btc_research_cycle",
)
