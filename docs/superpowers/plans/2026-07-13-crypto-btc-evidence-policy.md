# Crypto BTC Evidence Policy Implementation Plan

**Status:** Node 6 plan; pure Phase 1 policy boundary; implementation pending.

**Goal:** Build the immutable approved BTC source registry, trusted source-record catalog, identity-bound BTC resolution contract, incident-gate assessment, approved BTC aggregation configuration, and pure evidence evaluator. The evaluator produces canonical `TeamEvidenceAggregationRecord` tuples and the immutable `TeamEvidenceAggregationConfig` required by Node 7. It does not build a Node 2C aggregation result, a Node 3 envelope, packets, database rows, or a service.

**Architecture:** Use four small production modules with one ownership seam per policy concern:

- `crypto_btc_evidence_registry.py` owns the approved source registry and fail-closed source lookup.
- `crypto_btc_evidence_catalog.py` owns trusted source records, release-vintage metadata, validity windows, and catalog lookup.
- `crypto_btc_evidence_resolution.py` owns frozen BTC resolution-contract and incident-gate types plus their pure assessment.
- `crypto_btc_evidence_policy.py` owns the review-pinned BTC configuration, caller evidence-input wrapper, Node 2 record validation handoff, and pure evaluator.

This split is deliberate. Node 2 required six modules because its arithmetic and graph contracts are large; Node 3 uses one module because its envelope seam is narrow. Node 6 has four independent contracts and would make a single policy file too large and difficult to scope-audit. Four modules keep each boundary inspectable while allowing one unified Node 6 AST/import/size guard.

**Tech Stack:** Python 3.12, standard library only, exact frozen/slotted dataclasses, UTC-aware caller-supplied datetimes, fixed-six `Decimal`, canonical tuples, SHA-256 digests, pytest, Python `ast`, CodeGraph, and the repository-mandated read-only review gate.

## Global Constraints

- The BTC registry and policy are immutable and version-bound. Callers may submit source IDs and trusted-record IDs, but cannot pass a new registry entry or promote a proxy to official.
- `release_vintage` is present only in the trusted catalog. `CryptoBtcEvidenceInput` has no release-vintage field; evidence claims cannot override catalog metadata.
- Unknown source IDs, unknown record IDs, digest mismatches, source-family mismatches, expired catalog records, and registry/catalog version mismatches fail closed.
- All public values preserve `paper_only=True`, `report_only=True`, and `readonly=True`. No live trading, authentication, credentials, wallets, signing, orders, execution, exchange mutation, or account access is allowed.
- Production modules are pure over explicit inputs. They perform no database, Supabase/Postgres, filesystem, JSONL, cache, network, HTTP, socket, CLI, environment, process, logging, ambient-clock, randomness, or built-in `hash()` operation.
- The evaluator may construct and validate a temporary Node 2A `TeamEvidenceAggregationInput` to obtain canonical records and current selections. It must never call `build_team_evidence_aggregation_result`, any Node 2C reducer, the Node 3 envelope builder, packet constructors, or persistence APIs.
- Node 7 owns composition of the policy output with Node 2C aggregation and Node 3 envelope construction. A policy-gate status is not an aggregation result status.
- No package-root export, CLI, DB migration, service, or plan-document change is part of Node 6.

## Exact Sorted Implementation Allowlist

The implementation range and staged paths must equal this `LC_ALL=C`-sorted list. The plan document is deliberately excluded:

```text
src/polymarket_alpha_lab/crypto_btc_evidence_catalog.py
src/polymarket_alpha_lab/crypto_btc_evidence_policy.py
src/polymarket_alpha_lab/crypto_btc_evidence_registry.py
src/polymarket_alpha_lab/crypto_btc_evidence_resolution.py
tests/test_crypto_btc_evidence_catalog.py
tests/test_crypto_btc_evidence_policy.py
tests/test_crypto_btc_evidence_registry.py
tests/test_crypto_btc_evidence_resolution.py
tests/test_crypto_btc_evidence_scope.py
```

## Locked Public Interfaces

`crypto_btc_evidence_registry.py`:

```python
CryptoBtcApprovedSource
approved_crypto_btc_source_registry() -> tuple[CryptoBtcApprovedSource, ...]
require_approved_crypto_btc_source(source_id: str) -> CryptoBtcApprovedSource
```

Each approved source contains `source_id`, `source_family`, `trust_tier`, and `registry_version`. The fixed registry version is `crypto-btc-approved-registry-v0`. The approved IDs are `btc_spot_reference`, `btc_derivatives_reference`, `btc_onchain_reference`, and `btc_resolution_rules`.

`crypto_btc_evidence_catalog.py`:

```python
CryptoBtcTrustedSourceRecord
trusted_crypto_btc_source_catalog() -> tuple[CryptoBtcTrustedSourceRecord, ...]
resolve_trusted_crypto_btc_source_record(
    source_id: str,
    record_id: str,
    record_digest: str,
    *,
    evaluated_at: datetime,
) -> CryptoBtcTrustedSourceRecord
```

Each record contains the source ID, record ID and digest, source family, trusted `release_vintage`, catalog version, and explicit `valid_from`/`valid_until` bounds. The fixed catalog version is `crypto-btc-source-catalog-v0`. The factory returns the in-code frozen tuple; no caller-supplied catalog is accepted.

`crypto_btc_evidence_resolution.py`:

```python
CryptoBtcResolutionContract
CryptoBtcIncidentGates
CryptoBtcResolutionAssessment
check_crypto_btc_resolution_contract(...) -> CryptoBtcResolutionAssessment
crypto_btc_resolution_contract_payload(...) -> dict[str, object]
```

The contract is bound to `condition_id`, `market_slug`, `event_template`, question text, rules summary, close time, the `btc_resolution_rules` catalog record ID/digest, and `contract_version`. The contract must contain a question of at least 40 characters, a rules summary of at least 80 characters containing an objective official/Polymarket resolution condition, and a non-null close time. The checker requires exact identity equality with the evaluator’s condition, market, and event template.

`CryptoBtcIncidentGates` has exact boolean fields:

```text
source_outage
index_dislocation
chain_reorg
resolution_rule_change
market_halt
derivatives_feed_degraded
```

`source_outage`, `index_dislocation`, `chain_reorg`, `resolution_rule_change`, and `market_halt` produce a blocked assessment when true. `derivatives_feed_degraded` alone produces watch. Blocked signals take precedence over watch; all false signals plus a valid identity-bound contract produce pass. A missing, expired, or digest-mismatched resolution catalog record is blocked. Reason codes are closed, unique, and deterministic.

`crypto_btc_evidence_policy.py`:

```python
CryptoBtcEvidenceInput
CryptoBtcEvidenceEvaluation
build_crypto_btc_evidence_policy_config() -> TeamEvidenceAggregationConfig
evaluate_crypto_btc_evidence(...) -> CryptoBtcEvidenceEvaluation
```

`CryptoBtcEvidenceInput` contains `source_id`, trusted catalog `record_id` and digest, an exact `TeamEvidenceAggregationRecord`, and an explicit `selected_current` boolean. It contains no release-vintage or trust-tier override.

`CryptoBtcEvidenceEvaluation` contains sorted canonical records, current-revision selections, the immutable Node 2 config, the resolution assessment, a policy-gate status of `ready`, `watch`, or `blocked`, deterministic policy reason codes, and the three hard flags. `ready` means only that the BTC policy and incident gates pass; Node 7 must still combine it with the Node 2 aggregation status.

## Review-Pinned BTC Policy Constants

These are pure plan decisions, not values inferred from market data:

| Field | Literal |
|---|---:|
| `config_version` | `crypto-btc-evidence-policy-v0` |
| `max_evidence_age_seconds` | `900.000000` |
| `max_capture_lag_seconds` | `120.000000` |
| `independence_group_weight_cap` | `0.600000` |
| `correlation_group_weight_cap` | `0.750000` |
| `max_requirement_assignments_per_evidence` | `4` |
| `contradiction_no_probability_max` | `0.350000` |
| `contradiction_yes_probability_min` | `0.650000` |
| `contradiction_watch_score` | `0.250000` |
| `contradiction_block_score` | `0.500000` |
| `publish_probability_floor` | `0.020000` |
| `publish_probability_ceiling` | `0.980000` |
| `maximum_records` | `64` |
| `maximum_requirements` | `3` |
| `maximum_requirement_memberships` | `12` |
| `maximum_witness_edges` | `64` |

The sorted requirement tuple is:

```text
("btc_derivatives", 1, 0.200000, "watch")
("btc_onchain",      1, 0.150000, "watch")
("btc_spot",         1, 0.300000, "blocked")
```

## Size Ceilings

| File | Maximum lines |
|---|---:|
| `crypto_btc_evidence_registry.py` | 260 |
| `crypto_btc_evidence_catalog.py` | 360 |
| `crypto_btc_evidence_resolution.py` | 560 |
| `crypto_btc_evidence_policy.py` | 820 |
| Node 6 production aggregate | 2,000 |
| `test_crypto_btc_evidence_registry.py` | 450 |
| `test_crypto_btc_evidence_catalog.py` | 550 |
| `test_crypto_btc_evidence_resolution.py` | 850 |
| `test_crypto_btc_evidence_policy.py` | 1,150 |
| `test_crypto_btc_evidence_scope.py` | 650 |
| Node 6 test aggregate | 3,600 |

## Implementation Tasks

- [ ] **Task 1 — Red/green base and boundary checks:** Record local candidate `NODE_BASE=938a01b5`; verify branch, clean worktree, Node 3 source/signature stability, and the exact allowlist. If `origin/main` is not exactly this base, record the handoff as blocked and do not rebase, force-push, or substitute local ancestry for remote equality. Stop on any Node 2 or Node 3 interface drift.

- [ ] **Task 2 — Red/green registry and catalog:** Add tests for frozen/slotted values, sorted factory output, exact registry/catalog versions, unknown source rejection, source-family and trust-tier matching, record digest mismatch, expired validity windows, and proof that release-vintage comes only from the trusted catalog. Implement the four approved sources and deterministic in-code catalog records.

- [ ] **Task 3 — Red/green resolution and incident gates:** Add tests for condition/market/template identity binding, minimum question/rules semantics, required `btc_resolution_rules` catalog identity, every blocking incident, watch-only derivatives degradation, blocked-over-watch precedence, pass reason-code ordering, false hard flags, naive datetimes, and constructor-bypassed tampering. Implement the new BTC-specific frozen types rather than reusing `strategy_event_resolution_contract` types: the existing precedent is non-slotted, has production defaults, and lacks BTC catalog identity and incident gates. Reuse its ambiguity concepts only as explicit BTC rules.

- [ ] **Task 4 — Red/green policy config and evaluator:** Add tests asserting every literal policy value, canonical requirement ordering, source lookup fail-closed behavior, duplicate record/digest rejection, selected-current projection, Node 2A input-contract validation, preservation of caller records, policy-status mapping, and deterministic output under hostile Decimal contexts. Prove with AST and spies that the evaluator never calls Node 2C or Node 3 and never constructs packets or persistence objects. Implement the evaluator as a pure adapter from approved source IDs and trusted records to Node 2 records/config.

- [ ] **Task 5 — Red/green Node 6 scope guard:** Add `test_crypto_btc_evidence_scope.py` covering the exact nine-path allowlist, normalized import allowlists, no package-root exports, frozen/slotted/final public dataclasses, forbidden DB/network/CLI/auth/order surfaces, no floats or ambient clocks, and all line ceilings. The guard must deliberately allow the exact Node 6 evaluator symbols (`CryptoBtcEvidenceEvaluation`, `evaluate_crypto_btc_evidence`) even though Node 2C’s historical guard forbids the identifier component `evaluator`; all other forbidden-surface rules remain active.

- [ ] **Task 6 — Verification and publication gate:** Run the focused five-file test command, sanitized full suite, compileall, `git diff --check`, secret and Phase 1 boundary scans, and CodeGraph sync. Submit the complete node range to the human-directed read-only external Codex review gate (`gpt-6-astra`, `model_reasoning_effort=max`, final line `VERDICT: PASS`). A missing reviewer, non-PASS verdict, failed static gate, unavailable CodeGraph, or unequal remote `main` blocks completion. Commit and push only after every required gate passes; never report local candidate success as remote publication.

## Stop Conditions

Stop for a reviewed amendment if any source can be caller-promoted, release-vintage can come from evidence input, a resolution contract is not identity-bound, an incident blocker is downgraded, policy values drift, the evaluator calls Node 2C or Node 3, a non-pure import or persistence surface appears, a scope/size/focused/full test fails, or review/remote publication evidence is unavailable.

## Completion Evidence

Completion requires the exact nine-path range, clean worktree, focused tests, compile success, sanitized full suite, diff/secret/purity scans, CodeGraph status, review verdict, and candidate commit. The completion record must separately classify predecessor handoff, reviewer result, CodeGraph synchronization, and exact remote equality as `pass`, `blocked`, or `documented-unavailable`.
