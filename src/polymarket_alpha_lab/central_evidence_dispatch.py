"""Pure evidence dispatch: team routing and deterministic bundle assembly.

Dispatch consumes already-persisted normalized observations keyed by
source id. It performs no I/O and reads no clock; freshness is evaluated
against the caller-provided ``as_of`` moment with an effective limit of
``min(item max_age_seconds, source freshness_policy_seconds)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from .central_data_contracts import (
    ObservationValueState,
    ParseState,
    SourceDefinition,
)
from .central_data_db_row import NormalizedObservationRow, TypedEnvelope
from .central_data_registry import SourceRegistry, build_default_source_registry
from .central_evidence_bundle import (
    EvidenceBundle,
    EvidenceItemAvailability,
    EvidenceItemRequirement,
    SelectedEvidence,
    ZeroWeightPlaceholder,
    typed_value_equality,
)
from .team_taxonomy import require_team_id


@dataclass(frozen=True)
class TeamRouting:
    team_id: str
    supported: bool
    reason_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_team_id("team_id", self.team_id)
        if type(self.supported) is not bool:
            raise ValueError("supported must be a bool")
        for code in self.reason_codes:
            if type(code) is not str or not code or code.strip() != code:
                raise ValueError("reason_codes must contain canonical strings")


BTC_ITEM_REQUIREMENTS = (
    EvidenceItemRequirement(
        item_name="btc_spot_price",
        source_ids=("kraken_btc_ticker",),
        minimum_current_families=1,
        max_age_seconds=300,
    ),
    EvidenceItemRequirement(
        item_name="gamma_market_metadata",
        source_ids=("polymarket_gamma_markets",),
        minimum_current_families=1,
    ),
    EvidenceItemRequirement(
        item_name="clob_book_depth",
        source_ids=("polymarket_clob_book",),
        minimum_current_families=1,
    ),
)

_GENERIC_ITEM_REQUIREMENTS = (
    EvidenceItemRequirement(
        item_name="gamma_market_metadata",
        source_ids=("polymarket_gamma_markets",),
        minimum_current_families=1,
    ),
    EvidenceItemRequirement(
        item_name="clob_book_depth",
        source_ids=("polymarket_clob_book",),
        minimum_current_families=1,
    ),
)

# The BTC slice is the first fully specified item set; the other nine
# teams reference their registered sources generically until their M5
# domain adapters land.
REQUIRED_ITEM_CATALOG: Mapping[str, tuple[EvidenceItemRequirement, ...]] = {
    "crypto_btc": BTC_ITEM_REQUIREMENTS,
    **{
        team_id: _GENERIC_ITEM_REQUIREMENTS
        for team_id in (
            "politics",
            "crypto_eth",
            "macro_rates",
            "equity_indices",
            "commodities_gold",
            "commodities_oil",
            "sports_soccer",
            "sports_basketball",
            "sports_other",
        )
    },
}


def route_team(team_id: str, registry: SourceRegistry | None = None) -> TeamRouting:
    catalog = registry or build_default_source_registry()
    require_team_id("team_id", team_id)
    requirements = {item.team_id: item for item in catalog.requirements}
    if team_id not in requirements:
        return TeamRouting(team_id, False, ("team_requirement_not_registered",))
    if team_id not in REQUIRED_ITEM_CATALOG:
        return TeamRouting(team_id, False, ("team_item_requirements_not_defined",))
    return TeamRouting(team_id, True, ())


def _effective_max_age(
    requirement: EvidenceItemRequirement,
    source: SourceDefinition,
) -> int:
    limits = [source.freshness_policy_seconds]
    if requirement.max_age_seconds is not None:
        limits.append(requirement.max_age_seconds)
    return min(limits)


def _select_newest(observations: Sequence[NormalizedObservationRow]) -> NormalizedObservationRow:
    return min(
        observations,
        key=lambda row: (-row.observation_time.timestamp(), row.normalized_observation_id),
    )


def build_evidence_bundle(
    team_id: str,
    requirements: Sequence[EvidenceItemRequirement],
    observations_by_source: Mapping[str, Sequence[NormalizedObservationRow]],
    registry: SourceRegistry | None = None,
    *,
    as_of: datetime,
    market_reference: str | None = None,
) -> EvidenceBundle:
    catalog = registry or build_default_source_registry()
    require_team_id("team_id", team_id)
    if not requirements:
        raise ValueError("requirements must not be empty")

    items: dict[str, SelectedEvidence | ZeroWeightPlaceholder] = {}
    bundle_reasons: list[str] = []
    for requirement in sorted(requirements, key=lambda item: item.item_name):
        for source_id in requirement.source_ids:
            catalog.get(source_id)
        per_source: list[tuple[SourceDefinition, NormalizedObservationRow, EvidenceItemAvailability]] = []
        for source_id in requirement.source_ids:
            source = catalog.get(source_id)
            provided = list(observations_by_source.get(source_id, ()))
            if not provided:
                continue
            newest = _select_newest(provided)
            if newest.parse_state != ParseState.SUCCESS.value:
                status = EvidenceItemAvailability.PARSE_FAILED
            elif newest.value_state != ObservationValueState.PRESENT.value:
                status = EvidenceItemAvailability.UNKNOWN_VALUE
            else:
                age = (as_of - newest.observation_time).total_seconds()
                if age < 0 or age > _effective_max_age(requirement, source):
                    status = EvidenceItemAvailability.STALE
                else:
                    status = EvidenceItemAvailability.READY
            per_source.append((source, newest, status))

        if not per_source:
            items[requirement.item_name] = ZeroWeightPlaceholder(
                item_name=requirement.item_name,
                availability=EvidenceItemAvailability.MISSING,
                reason_codes=("item_missing",),
            )
            bundle_reasons.append("item_missing")
            continue

        ready = [pair for pair in per_source if pair[2] is EvidenceItemAvailability.READY]
        if not ready:
            priority = [
                EvidenceItemAvailability.PARSE_FAILED,
                EvidenceItemAvailability.STALE,
                EvidenceItemAvailability.UNKNOWN_VALUE,
            ]
            availability = min(
                (pair[2] for pair in per_source),
                key=lambda status: priority.index(status),
            )
            reason = f"item_{availability.value}"
            items[requirement.item_name] = ZeroWeightPlaceholder(
                item_name=requirement.item_name,
                availability=availability,
                reason_codes=(reason,),
                references=tuple(
                    SelectedEvidence.from_observation(row, source_family=source.source_family)
                    for source, row, _status in per_source
                ),
            )
            bundle_reasons.append(reason)
            continue

        deduped: dict[str, tuple[SourceDefinition, NormalizedObservationRow]] = {}
        for source, row, _status in sorted(
            ready, key=lambda pair: pair[1].normalized_observation_id
        ):
            deduped.setdefault(f"{source.source_family}:{row.raw_payload_sha256}", (source, row))
        families = {source.source_family for source, _row in deduped.values()}
        if len(families) < requirement.minimum_current_families:
            items[requirement.item_name] = ZeroWeightPlaceholder(
                item_name=requirement.item_name,
                availability=EvidenceItemAvailability.QUORUM_NOT_MET,
                reason_codes=("source_quorum_not_met",),
                references=tuple(
                    SelectedEvidence.from_observation(row, source_family=source.source_family)
                    for source, row in deduped.values()
                ),
            )
            bundle_reasons.append("item_quorum_not_met")
            continue

        selected_rows = sorted(deduped.values(), key=lambda pair: pair[1].normalized_observation_id)
        first_value = TypedEnvelope.decode(dict(selected_rows[0][1].typed_value))
        contradictory = False
        for _source, row in selected_rows[1:]:
            other = TypedEnvelope.decode(dict(row.typed_value))
            equality = typed_value_equality(first_value, other)
            if equality is False:
                contradictory = True
                break
        if contradictory:
            items[requirement.item_name] = ZeroWeightPlaceholder(
                item_name=requirement.item_name,
                availability=EvidenceItemAvailability.CONTRADICTORY,
                reason_codes=("contradictory_values",),
                references=tuple(
                    SelectedEvidence.from_observation(row, source_family=source.source_family)
                    for source, row in selected_rows
                ),
            )
            bundle_reasons.append("item_contradictory_values")
            continue

        if len(families) > 1:
            bundle_reasons.append("multi_family_corroboration")
        items[requirement.item_name] = SelectedEvidence.from_observation(
            selected_rows[0][1],
            source_family=selected_rows[0][0].source_family,
        )

    return EvidenceBundle(
        team_id=team_id,
        market_reference=market_reference,
        as_of=as_of,
        items=items,
        reason_codes=tuple(sorted(set(bundle_reasons))),
    )


__all__ = (
    "BTC_ITEM_REQUIREMENTS",
    "REQUIRED_ITEM_CATALOG",
    "TeamRouting",
    "build_evidence_bundle",
    "route_team",
)
