# M2 Stage Plan: Evidence Bundle And Dispatch

Date: 2026-09-05
Stage: M2 of the [Project Delivery Plan](../../roadmap/2026-09-05-project-delivery-plan.md)
Status: plan review completed; findings dispositioned (see the final section)
Depends on: M1 (accepted; commit `c2920a0b`)

## Parent-Plan Traceability

This stage implements the M2 milestone: central source selection and
deterministic per-team evidence bundles with per-item quorum, freshness
gating, deduplication, contradiction surfacing, and blocked availability
with canonical zero-weight placeholders. M3 forecast integration and any
network orchestration stay out of scope: dispatch is a pure reducer over
already-acquired normalized observations.

## Current-Code Facts

- M1 delivers `NormalizedObservationRow` (source-bound, identity-verified,
  parse/freshness/value states, reason codes) and the registry's
  `TeamSourceRequirement` (team -> source ids, family threshold).
- `TeamForecastEvidencePacket` already exists in the team forecast layer
  for later Node E conversion; M2 does not touch it.
- No bundle/dispatch module exists yet.

## Design Decisions

1. Dispatch is pure. `central_evidence_dispatch.py` accepts a team id, a
   required-item policy, as-of time, and already-persisted normalized
   observations keyed by source id. It performs no I/O, no clock, and no
   store access; determinism follows from sorted inputs and stable
   ordering rules.
2. The bundle is the contract. `central_evidence_bundle.py` defines
   `EvidenceItemRequirement` (item name, required source ids or families,
   minimum current families, `max_age_seconds: int | None` per-item
   freshness override that tightens the source policy — effective limit is
   `min(item max_age, source freshness_policy_seconds)` when both exist),
   `EvidenceItemAvailability` enum (`ready`, `missing`, `stale`,
   `parse_failed`, `unknown_value`, `quorum_not_met`, `contradictory`),
   `SelectedEvidence` (observation identity, source id, source family,
   retrieval/observation times, payload hash, parser version,
   parse/freshness states) used only for `ready` items,
   `ZeroWeightPlaceholder` (item name, availability, reason codes,
   `weight: Decimal` exactly `Decimal("0")`) as a distinct type for every
   non-ready item, and `EvidenceBundle` (team id, `market_reference:
   str | None` canonical-nonblank-or-None, as-of time,
   `items: Mapping[str, SelectedEvidence | ZeroWeightPlaceholder]` as a
   `MappingProxyType` keyed by required item name with every required name
   present exactly once and no extra keys, overall status
   `ready`/`blocked`, reason codes). Every field is canonical and
   replay-stable, and downstream consumers distinguish placeholders by
   type, not by sentinel values.
3. Family independence is explicit. Deduplication collapses observations
   sharing a payload hash only within one family (provider mirrors);
   byte-identical payloads from different families are NOT deduped and
   count as independent family observations, because identical responses
   from independent providers are valid corroboration. Quorum counts
   distinct `source_family` values among observations that are current
   AND parse-successful AND value-present; stale, parse-failed,
   unknown-value, and null observations are excluded. Meeting a
   one-family minimum never counts as corroboration in the reason codes;
   corroboration is only asserted when more than one independent family
   is current.
4. Missing, stale, parse-failed, unknown-value, or quorum-blocked
   required items produce exactly one `ZeroWeightPlaceholder` record with
   the blocking reason code and the availability structure. The bundle is
   `blocked` overall if any required item is not `ready`.
5. Contradictions are surfaced, never averaged, under a canonical
   equality contract: `typed_value_equality(a, b)` compares Decimal
   values numerically (so `1.0` equals `1.00`), datetimes exactly,
   objects by identical sorted key sets with recursive value equality,
   sequences by length and element-wise equality; values of different
   envelope types are incomparable (not contradictory). If two selected
   current observations disagree on typed value for the same required
   item, the item is `contradictory`, both source references are
   preserved with their payload hashes, and reason code
   `contradictory_values` is set.
6. Routing is explicit. `route_team(team_id, registry)` returns a
   routing result (`supported` with the requirement, or `unsupported`
   with reason) for each of the ten team ids; unsupported teams never
   receive a fabricated bundle.

## Work Items

### 1. `src/polymarket_alpha_lab/central_evidence_bundle.py` (new)

Pure bundle contracts and the zero-weight placeholder specification
described above, with full `__post_init__` validation (canonical strings,
enum storage values, tuple ordering, paper/report/readonly flags true).

### 2. `src/polymarket_alpha_lab/central_evidence_dispatch.py` (new)

- `route_team(team_id, registry)`: supported/unsupported routing.
- `build_evidence_bundle(team_id, requirements, observations_by_source,
  registry, *, as_of, market_reference)`: per-item selection restricted to
  the requirement's source ids — newest current observation per source by
  `observation_time` with ties broken by ascending lexicographic
  `normalized_observation_id` (so one observation per source per item by
  construction; adapters emitting multiple facets must use separate item
  names) — then dedup by payload hash within a family, family-quorum
  counting, freshness gating against `min(item max_age, source policy)`
  using the provided `as_of`, contradiction detection via
  `typed_value_equality`, placeholder emission, overall status and
  reason codes.
- `REQUIRED_ITEM_CATALOG`: a documented default mapping from team ids to
  required item names (the BTC slice names concrete items such as
  `btc_spot_price` and `gamma_market_metadata`; other teams reference
  their registered sources generically until their M5 adapters land).

### 3. Tests (new)

- `tests/test_central_evidence_bundle.py`: contract validation negatives
  (non-canonical fields, bad enum values, duplicate reason codes).
- `tests/test_central_evidence_dispatch.py` (fixture-driven, no I/O):
  ready path for the BTC item set; stale/missing/parse-failed/unknown
  gating; item-level `max_age_seconds` tightening the source policy;
  mirror dedup within a family; cross-family identical payload hashes
  both counting toward a two-family quorum; one-family minimum meets
  quorum but reason codes never claim corroboration; two-family
  corroboration recorded; `typed_value_equality` cases (Decimal `1.0`
  vs `1.00` equal, cross-type incomparable, nested objects/sequences);
  contradiction surfacing with both references; observation-time
  tie-break by ascending id; zero-weight placeholder exactly once per
  blocked item (distinct type, weight exactly `Decimal("0")`); overall
  blocked status when any required item is blocked; deterministic
  replay (same inputs, identical bundle identity); all ten team ids
  routed supported or explicitly unsupported with reasons.

## Verification

Recorded results (2026-09-05):

- Focused: `tests/test_central_evidence_bundle.py` and
  `tests/test_central_evidence_dispatch.py` — 9 passed covering the full
  acceptance list (ready/blocked paths, item-level tightening, mirror
  dedup, cross-family identical-payload corroboration, quorum blocking,
  contradiction with both references, tie-break, placeholder-once-per-item,
  replay identity, ten-team routing).
- Full central-data set re-run green; compile checks, `git diff --check`,
  and credential scan clean; full Python 3.11 regression recorded in the
  hard-review prompt.
- No transport/acquisition/contracts/registry behavioral changes; no CLI
  changes; no migration.

Original verification requirements (all satisfied by the above):

- Focused: the two new test files plus the full central-data set green.
- Full Python 3.11 regression; compile checks; `git diff --check`;
  credential scan over changed files.
- No changes to transport, acquisition, contracts, registry behavior
  beyond the new catalog constant; no CLI changes; no migration.

## Acceptance Criteria (mirrors delivery-plan M2 exit)

1. Routing covers all ten team ids as supported or explicitly
   unsupported with reasons.
2. Fixture tests prove freshness gating, quorum blocking, mirror
   deduplication, family counting, and deterministic ordering.
3. Blocked required items yield exactly one canonical zero-weight
   placeholder each, and the bundle is blocked overall.
4. Contradictory values are surfaced with preserved source references,
   never averaged or silently dropped.
5. Replay of identical inputs produces an identical bundle identity.
6. No fabricated evidence: unsupported teams and blocked items carry
   explicit reason codes, not neutral values.

## Rollback

Revert the two modules and two test files; nothing else depends on them.

## Plan Review Response (2026-09-05)

Claude Code reviewed this plan read-only (`claude-opus-5`, effort `max`)
and returned REQUEST_CHANGES: three BLOCKER, three MAJOR, three MINOR,
one NIT. All ten findings are accepted:

1. BLOCKER typed-value equality semantics: ACCEPTED; a canonical
   `typed_value_equality` contract (numeric Decimal equality, exact
   datetimes, recursive object/sequence equality, cross-type
   incomparable) is specified and tested.
2. BLOCKER placeholder precision: ACCEPTED; `ZeroWeightPlaceholder` is a
   distinct dataclass with `weight = Decimal("0")`, used for every
   non-ready item, distinguished by type rather than sentinel values.
3. BLOCKER cross-family identical payloads: ACCEPTED; only intra-family
   mirrors are deduped; identical hashes across independent families
   count toward quorum as corroboration, with a dedicated test.
4. MAJOR freshness override semantics: ACCEPTED; `max_age_seconds`
   tightens with effective limit `min(item, source policy)`.
5. MAJOR per-item results structure: ACCEPTED; `items` is a
   `MappingProxyType` keyed by required item name, validated for exact
   key coverage.
6. MAJOR tie-breaking: ACCEPTED; ascending lexicographic
   `normalized_observation_id` with a fixture test.
7. MINOR market reference typing: ACCEPTED; `str | None` canonical
   nonblank when present.
8. MINOR multiple observations per source/item: ACCEPTED; newest-per-
   source selection makes one observation per source per item by
   construction, and adapters must use separate item names for facets.
9. MINOR quorum phrasing: ACCEPTED; rewritten as an inclusive positive
   filter with explicit exclusions.
10. NIT contract-list preview of the freshness field type: ACCEPTED.
